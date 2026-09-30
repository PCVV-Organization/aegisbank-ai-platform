"""Configuration abstractions for AegisBank.

This package provides two complementary providers:

* :class:`~aegisbank_agent.configuration.config.ConfigurationProvider` —
  a canonical, type-safe interface for **non-secret configuration**
  (feature flags, environment, service URLs). Implementations exist for
  the Azure App Configuration Emulator (``AppConfigurationEmulatorProvider``)
  and a plain environment-variable fallback (``EnvironmentConfigurationProvider``).

* :class:`~aegisbank_agent.configuration.secrets.SecretProvider` — a
  canonical interface for **secrets** (passwords, connection strings,
  API keys). Implementations exist for the local synthetic store
  (``LocalSyntheticSecretProvider``) and an Azure Key Vault ``SecretClient``
  adapter contract (``AzureKeyVaultSecretProvider``).

Why a package boundary? ``Configuration`` and ``Secret`` have
different threat models and different SLAs in Azure. App Configuration
stores *configuration* (cheap, frequent refresh, no SLA on confidentiality)
and Key Vault stores *secrets* (encrypted, audit-logged, RBAC-protected).
Mixing them in one abstraction is exactly what Microsoft warns against
(https://learn.microsoft.com/en-us/azure/azure-app-configuration/use-key-vault-references-python-provider).
"""

from .config import (
    AppConfigurationCloudProvider,
    AppConfigurationEmulatorProvider,
    ConfigurationError,
    ConfigurationProvider,
    ConfigurationSource,
    EnvironmentConfigurationProvider,
    InvalidConfigurationValue,
    MissingConfigurationKey,
    build_default_provider,
    coerce_bool,
    coerce_float,
    coerce_int,
    coerce_json,
    get_default_provider,
    reset_default_provider,
    set_default_provider,
    snapshot_for_audit,
)
from .environment import (
    EnvironmentSelectionError,
    RuntimeEnvironment,
    load_local_dotenv,
    resolve_runtime_environment,
    validate_runtime_configuration,
)
from .identity import resolve_azure_credential
from .secrets import (
    AzureKeyVaultSecretProvider,
    KeyVaultReferenceResolver,
    LocalSyntheticSecretProvider,
    MissingSecret,
    SecretAccessDenied,
    SecretError,
    SecretProvider,
    SecretSource,
    build_default_secret_provider,
    get_default_secret_provider,
    reset_default_secret_provider,
    set_default_secret_provider,
)

__all__ = [
    "AppConfigurationEmulatorProvider",
    "AppConfigurationCloudProvider",
    "AzureKeyVaultSecretProvider",
    "ConfigurationError",
    "ConfigurationProvider",
    "ConfigurationSource",
    "EnvironmentConfigurationProvider",
    "EnvironmentSelectionError",
    "InvalidConfigurationValue",
    "KeyVaultReferenceResolver",
    "LocalSyntheticSecretProvider",
    "MissingConfigurationKey",
    "MissingSecret",
    "SecretAccessDenied",
    "SecretError",
    "SecretProvider",
    "SecretSource",
    "RuntimeEnvironment",
    "build_default_provider",
    "build_default_secret_provider",
    "coerce_bool",
    "coerce_float",
    "coerce_int",
    "coerce_json",
    "get_default_provider",
    "get_default_secret_provider",
    "load_local_dotenv",
    "reset_default_provider",
    "reset_default_secret_provider",
    "resolve_azure_credential",
    "set_default_provider",
    "set_default_secret_provider",
    "snapshot_for_audit",
    "resolve_runtime_environment",
    "validate_runtime_configuration",
]
