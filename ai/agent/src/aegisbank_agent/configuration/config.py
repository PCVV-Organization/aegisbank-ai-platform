"""Canonical configuration provider for AegisBank.

Configuration = **non-secret** application values that change behavior
(feature flags, environment, service URLs, log levels). It is **not** the
place to store passwords, tokens, or API keys — those belong in the
:mod:`~aegisbank_agent.configuration.secrets` module and, in cloud, in
Azure Key Vault.

The canonical contract is intentionally narrow so that implementations
remain replaceable:

* :py:meth:`ConfigurationProvider.get` returns the current value for a
  key or raises :py:class:`MissingConfigurationKey`.
* :py:meth:`ConfigurationProvider.get_optional` returns ``None`` instead of
  raising for keys that may legitimately be absent.
* :py:meth:`ConfigurationProvider.refresh` re-reads the underlying source
  (used by tests and by App Configuration's watcher).
  * :py:meth:`ConfigurationProvider.current_label` exposes the active label so
  consumers can log which environment a value came from.

Implementations:

* :class:`EnvironmentConfigurationProvider` — process environment
  fallback (always available, no external dependency).
* :class:`AppConfigurationEmulatorProvider` — Azure App Configuration
  Emulator (https://learn.microsoft.com/en-us/azure/azure-app-configuration/emulator-overview)
  with anonymous auth for local development.
* :class:`AppConfigurationCloudProvider` — Azure App Configuration in
  cloud, used when ``AEGISBANK_USE_AZURE_CONFIG=true`` and the host has
  ``DefaultAzureCredential`` configured (Tagged ``CLOUD-PENDING`` locally).

Provider selection is centralised in :func:`build_default_provider`.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

from .environment import (
    resolve_runtime_environment,
    validate_runtime_configuration,
)

logger = logging.getLogger(__name__)


def _validated_urlopen(target: str | urllib.request.Request, timeout: float):
    """Open only HTTP(S) App Configuration endpoints."""
    target_url = target if isinstance(target, str) else target.full_url
    if urllib.parse.urlparse(target_url).scheme not in {"http", "https"}:
        raise ValueError("App Configuration endpoint must use http or https")
    return urllib.request.urlopen(target, timeout=timeout)  # nosec B310 - scheme validated above


class ConfigurationError(RuntimeError):
    """Base class for configuration-related failures."""


class MissingConfigurationKey(ConfigurationError):  # noqa: N818
    """Raised when a required configuration key is absent."""


class InvalidConfigurationValue(ConfigurationError):  # noqa: N818
    """Raised when a value cannot be coerced to its declared type."""


@dataclass(frozen=True, slots=True)
class ConfigurationSource:
    """Describes where a configuration value originated.

    Surfaced by :py:meth:`ConfigurationProvider.describe` to make
    observability trivial and to back the AuditLogger requirement from
    the Security + Configuration policy of AI-200.
    """

    name: str
    label: str | None
    last_refresh_at: str | None


@runtime_checkable
class ConfigurationProvider(Protocol):
    """Single canonical contract for non-secret configuration values."""

    name: str

    def get(self, key: str) -> str: ...

    def get_optional(self, key: str) -> str | None: ...

    def require(self, key: str) -> str: ...

    def current_label(self) -> str | None: ...

    def refresh(self) -> None: ...

    def describe(self, key: str) -> ConfigurationSource | None: ...


def require_key(provider: ConfigurationProvider, key: str) -> str:
    """Resolve a required configuration key or raise."""
    value = provider.get_optional(key)
    if value is None:
        raise MissingConfigurationKey(key)
    return value


def coerce_int(value: str, key: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise InvalidConfigurationValue(f"config '{key}' must be int: {value!r}") from exc


def coerce_float(value: str, key: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidConfigurationValue(f"config '{key}' must be float: {value!r}") from exc


def coerce_bool(value: str, key: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off", ""}:
        return False
    raise InvalidConfigurationValue(f"config '{key}' must be bool: {value!r}")


def coerce_json(value: str, key: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise InvalidConfigurationValue(f"config '{key}' is not valid JSON: {value!r}") from exc


@dataclass(slots=True)
class EnvironmentConfigurationProvider:
    """Fallback provider that reads configuration from ``os.environ``.

    The simplest implementation: zero dependencies, always available,
    no caching. Useful as a baseline when App Configuration is offline.
    """

    name: str = "environment"
    _cache: dict[str, str] = field(default_factory=dict)
    _label: str = field(default_factory=lambda: os.getenv("AEGISBANK_CONFIG_LABEL", "local"))

    def __post_init__(self) -> None:
        self.refresh()

    def get(self, key: str) -> str:
        value = self._cache.get(key)
        if value is None:
            raise MissingConfigurationKey(key)
        return value

    def get_optional(self, key: str) -> str | None:
        return self._cache.get(key)

    def require(self, key: str) -> str:
        return require_key(self, key)

    def current_label(self) -> str | None:
        return self._label

    def refresh(self) -> None:
        # Environment is read at process start; refresh is a no-op there.
        self._cache.clear()
        for key, value in os.environ.items():
            self._cache[key] = value

    def describe(self, key: str) -> ConfigurationSource | None:
        if key not in self._cache:
            return None
        return ConfigurationSource(
            name=self.name,
            label=self._label,
            last_refresh_at=None,
        )


@dataclass(slots=False)
class AppConfigurationEmulatorProvider:
    """Provider backed by the local Azure App Configuration Emulator.

    The emulator exposes the same REST API as Azure App Configuration
    (``/kv``, ``/labels``, ``/locks``, ``/revisions``, ``/snapshots``) but
    accepts anonymous authentication when launched with
    ``-e Tenant:AnonymousAuthEnabled=true`` and
    ``-e Authentication:Anonymous:AnonymousUserRole=Owner``.

    See https://learn.microsoft.com/en-us/azure/azure-app-configuration/emulator-overview.

    Tagged ``LOCAL-APPCONFIG-COVERED`` after the v0.14.0 acceptance run.
    """

    name: str = "app-configuration-emulator"
    endpoint: str = "http://127.0.0.1:8483"
    _label: str = "local"
    timeout_seconds: float = 3.0

    _cache: dict[str, str] = field(default_factory=dict)
    _last_refresh: str | None = None

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8483",
        _label: str = "local",
        label: str | None = None,
        timeout_seconds: float = 3.0,
        name: str = "app-configuration-emulator",
    ) -> None:
        self.name = name
        self.endpoint = endpoint.rstrip("/")
        self._label = label if label is not None else _label
        self.timeout_seconds = timeout_seconds
        self._cache = {}
        self._last_refresh = None
        self.__post_init__()

    def __post_init__(self) -> None:
        try:
            self.refresh()
        except (OSError, RuntimeError) as exc:  # pragma: no cover - safety net
            logger.warning(
                "App Configuration Emulator unreachable at %s; keeping empty cache. error=%s",
                self.endpoint,
                exc,
            )

    def _build_url(self, key: str | None = None, label: str | None = None) -> str:
        effective_label = label if label is not None else self._label
        label_param = f"?label={effective_label}" if effective_label else ""
        if key is None:
            return f"{self.endpoint}/kv{label_param}"
        from urllib.parse import quote

        sep = "&" if label_param else "?"
        return f"{self.endpoint}/kv/{quote(key, safe='')}{label_param}{sep}api-version=1.0"

    def refresh(self) -> None:
        from datetime import datetime, timezone

        url = self._build_url(None)
        with _validated_urlopen(url, timeout=self.timeout_seconds) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        new_cache: dict[str, str] = {}
        for item in payload.get("items", []):
            new_cache[item["key"]] = item.get("value") or ""
        self._cache = new_cache
        self._last_refresh = datetime.now(timezone.utc).isoformat()

    def set_kv(
        self,
        key: str,
        value: str,
        label: str | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """Store a configuration key-value in the emulator via REST PUT."""
        url = self._build_url(key, label=label)
        body_dict: dict[str, Any] = {"value": value}
        if content_type is not None:
            body_dict["content_type"] = content_type
        data_bytes = json.dumps(body_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with _validated_urlopen(req, timeout=self.timeout_seconds) as resp:
            content = resp.read().decode("utf-8")
            result = json.loads(content) if content else {}
        target_label = label if label is not None else self._label
        if target_label == self._label:
            self._cache[key] = value
        return result

    def get_kv_raw(self, key: str, label: str | None = None) -> dict[str, Any]:
        """Fetch raw metadata for a key from the emulator."""
        url = self._build_url(key, label=label)
        with _validated_urlopen(url, timeout=self.timeout_seconds) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}

    def delete_kv(self, key: str, label: str | None = None) -> bool:
        """Delete a key-value from the emulator via REST DELETE."""
        url = self._build_url(key, label=label)
        req = urllib.request.Request(url, method="DELETE")
        try:
            with _validated_urlopen(req, timeout=self.timeout_seconds) as resp:
                self._cache.pop(key, None)
                return resp.status in (200, 204)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            raise

    def set_keyvault_reference(
        self,
        key: str,
        secret_uri: str | None = None,
        vault_uri: str | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        """Store an Azure Key Vault reference in App Configuration."""
        uri = secret_uri or vault_uri
        if not uri:
            raise ValueError("secret_uri or vault_uri is required")
        return self.set_kv(
            key=key,
            value=json.dumps({"uri": uri}),
            label=label,
            content_type="application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8",
        )

    def set_feature_flag(
        self, feature_name: str, enabled: bool, label: str | None = None
    ) -> dict[str, Any]:
        """Store an Azure Feature Flag setting in App Configuration."""
        key = f".appconfig.featureflag/{feature_name}"
        value = json.dumps(
            {"id": feature_name, "enabled": enabled, "conditions": {"client_filters": []}}
        )
        return self.set_kv(
            key=key,
            value=value,
            label=label,
            content_type="application/vnd.microsoft.appconfig.ff+json;charset=utf-8",
        )

    def get(self, key: str) -> str:
        value = self._cache.get(key)
        if value is None:
            raise MissingConfigurationKey(key)
        return value

    def get_optional(self, key: str) -> str | None:
        return self._cache.get(key)

    def require(self, key: str) -> str:
        return require_key(self, key)

    def current_label(self) -> str | None:
        return self._label

    def describe(self, key: str) -> ConfigurationSource | None:
        if key not in self._cache:
            return None
        return ConfigurationSource(
            name=self.name,
            label=self._label,
            last_refresh_at=self._last_refresh,
        )


@dataclass(slots=True)
class AppConfigurationCloudProvider:
    """Azure App Configuration adapter authenticated with ``DefaultAzureCredential``.

    Imports and network access are deferred until this cloud-only provider is
    explicitly selected.  The official provider resolves App Configuration values
    and Key Vault references with the same managed-identity credential.
    """

    endpoint: str
    _label: str
    credential: Any = None
    loader: Any = None
    name: str = "azure-app-configuration"
    _provider: Any = field(init=False, default=None)
    _cache: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        if not self.endpoint.startswith("https://"):
            raise ConfigurationError(
                "AZURE_APPCONFIG_ENDPOINT must use https in cloud environments"
            )
        if self.credential is None:
            from azure.identity import DefaultAzureCredential

            self.credential = DefaultAzureCredential()
        if self.loader is None:
            from azure.appconfiguration.provider import SettingSelector, load

            selects = [SettingSelector(key_filter="*", label_filter="\0")]
            if self._label:
                selects.append(SettingSelector(key_filter="*", label_filter=self._label))

            def default_loader(**kwargs: Any) -> Any:
                return load(
                    endpoint=self.endpoint,
                    credential=self.credential,
                    keyvault_credential=self.credential,
                    selects=selects,
                    refresh_enabled=True,
                    startup_timeout=30,
                    **kwargs,
                )

            self.loader = default_loader
        self.refresh()

    def refresh(self) -> None:
        if self._provider is None:
            self._provider = self.loader()
        else:
            refresh = getattr(self._provider, "refresh", None)
            if callable(refresh):
                refresh()
        self._cache = {key: str(value) for key, value in self._provider.items()}

    def get(self, key: str) -> str:
        return require_key(self, key)

    def get_optional(self, key: str) -> str | None:
        return self._cache.get(key)

    def require(self, key: str) -> str:
        return require_key(self, key)

    def current_label(self) -> str | None:
        return self._label

    def describe(self, key: str) -> ConfigurationSource | None:
        if key not in self._cache:
            return None
        return ConfigurationSource(name=self.name, label=self._label, last_refresh_at=None)


def build_default_provider() -> ConfigurationProvider:
    """Select the canonical provider based on environment.

    Resolution rules:

    1. If ``AEGISBANK_USE_APPCONFIG_EMULATOR=true`` (default), prefer
       ``AppConfigurationEmulatorProvider`` against the configured endpoint.
    2. If the emulator endpoint is unreachable, fall back to
       :class:`EnvironmentConfigurationProvider` with a warning log so
       tests do not crash.
    3. If ``AEGISBANK_USE_APPCONFIG_EMULATOR=false``, return the
       environment provider.

    Selection is centralised here so tests can override the provider
    via :py:func:`set_default_provider` without patching individual
    call sites.
    """
    environment = resolve_runtime_environment()
    if environment.is_cloud:
        validate_runtime_configuration(environment)
        endpoint = os.getenv("AZURE_APPCONFIG_ENDPOINT", "")
        if not endpoint:
            raise MissingConfigurationKey("AZURE_APPCONFIG_ENDPOINT")
        label = os.getenv("AEGISBANK_CONFIG_LABEL", environment.value)
        return AppConfigurationCloudProvider(endpoint=endpoint, _label=label)

    flag = os.getenv("AEGISBANK_USE_APPCONFIG_EMULATOR", "true").lower()
    if flag not in {"1", "true", "yes", "on"}:
        return EnvironmentConfigurationProvider(_label=os.getenv("AEGISBANK_CONFIG_LABEL", "local"))

    endpoint = os.getenv("AEGISBANK_APPCONFIG_EMULATOR_URL", "http://127.0.0.1:8483")
    label = os.getenv("AEGISBANK_CONFIG_LABEL", "local")
    provider: ConfigurationProvider = AppConfigurationEmulatorProvider(
        endpoint=endpoint, _label=label
    )

    # Fail-fast probe: if the emulator is not running we still want tests
    # to proceed. We probe via the same /kv endpoint used by refresh().
    try:
        provider.refresh()
    except (OSError, RuntimeError) as exc:
        logger.warning(
            "App Configuration Emulator not reachable at %s; falling back to env. error=%s",
            endpoint,
            exc,
        )
        provider = EnvironmentConfigurationProvider(_label=label)
    return provider


_DEFAULT_PROVIDER: ConfigurationProvider | None = None


def get_default_provider() -> ConfigurationProvider:
    """Return a process-wide default configuration provider (lazy)."""
    global _DEFAULT_PROVIDER
    if _DEFAULT_PROVIDER is None:
        _DEFAULT_PROVIDER = build_default_provider()
    return _DEFAULT_PROVIDER


def set_default_provider(provider: ConfigurationProvider | None) -> None:
    """Replace the process-wide default provider (testing hook)."""
    global _DEFAULT_PROVIDER
    _DEFAULT_PROVIDER = provider


def reset_default_provider() -> None:
    """Force the next :py:func:`get_default_provider` to rebuild."""
    set_default_provider(None)


def snapshot_for_audit(provider: ConfigurationProvider) -> Mapping[str, str]:
    """Return a stable name → description mapping for the AuditLogger.

    The helper deliberately walks a small subset of pre-declared keys
    rather than dumping the whole cache, so audit payloads stay
    predictable and avoid leaking unrelated environment variables.
    """
    out: dict[str, str] = {}
    for key in _AUDIT_KEYS:
        value = provider.get_optional(key)
        if value is not None:
            source = provider.describe(key)
            out[key] = f"{source.name}:{source.label or 'unlabeled'}" if source else "unknown"
    return out


_AUDIT_KEYS: tuple[str, ...] = (
    "AEGISBANK_ENV",
    "AEGISBANK_CONFIG_LABEL",
    "AEGISBANK_DATABASE_URL",
    "REDIS_URL",
    "AEGISBANK_PGVECTOR_URL",
    "COSMOS_ENDPOINT",
)
