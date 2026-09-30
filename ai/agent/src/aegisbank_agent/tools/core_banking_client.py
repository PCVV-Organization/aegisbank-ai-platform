"""HTTP API client for Core Banking with service authentication and trace propagation.

Enforces the architectural boundary that the Agent interacts with Core Banking
exclusively via HTTP API contracts in staging and production, never via direct DB.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("aegisbank.tools.core_banking_client")


@runtime_checkable
class ServiceAuthHandler(Protocol):
    """Protocol for service-to-service authentication against Core Banking."""

    def get_auth_headers(self) -> dict[str, str]: ...


class NoAuthHandler:
    """No-op authentication handler for local development and test environments."""

    def get_auth_headers(self) -> dict[str, str]:
        return {}


class EntraServiceAuthHandler:
    """Acquires Microsoft Entra ID bearer tokens for Core Banking service authentication.

    Status: READY_TO_VALIDATE (executes against live Entra app registrations).
    """

    def __init__(
        self,
        audience: str | None = None,
        credential: Any = None,
    ) -> None:
        self.audience = audience or os.getenv(
            "CORE_BANKING_ENTRA_AUDIENCE", "api://aegisbank-core-banking/.default"
        )
        self.credential = credential

    def get_auth_headers(self) -> dict[str, str]:
        if self.credential is None:
            from ..configuration.identity import resolve_azure_credential

            self.credential = resolve_azure_credential()
        token = self.credential.get_token(self.audience)
        return {"Authorization": f"Bearer {token.token}"}


def get_traceparent_header() -> dict[str, str]:
    """Extract W3C traceparent from current OpenTelemetry context if available."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        span_ctx = span.get_span_context()
        if span_ctx.is_valid:
            trace_id = f"{span_ctx.trace_id:032x}"
            span_id = f"{span_ctx.span_id:016x}"
            trace_flags = f"{span_ctx.trace_flags:02x}"
            return {"traceparent": f"00-{trace_id}-{span_id}-{trace_flags}"}
    except ImportError:
        pass
    return {}


class CoreBankingHttpClient:
    """Client for invoking Core Banking REST endpoints with auth and trace correlation."""

    def __init__(
        self,
        base_url: str | None = None,
        auth_handler: ServiceAuthHandler | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("AEGISBANK_CORE_BANKING_URL")
            or os.getenv("CORE_BANKING_URL")
            or "http://localhost:8000"
        ).rstrip("/")
        self.auth_handler = auth_handler or NoAuthHandler()
        self.timeout = timeout

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Perform an HTTP POST request to Core Banking API."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.auth_handler.get_auth_headers())
        headers.update(get_traceparent_header())

        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
                return json.loads(resp_bytes.decode("utf-8")) if resp_bytes else {}
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
                msg = (
                    err_json.get("error", {}).get("message")
                    or err_json.get("detail")
                    or str(http_err)
                )
            except Exception:
                msg = str(http_err)
            raise ValueError(f"Core Banking HTTP error ({http_err.code}): {msg}") from http_err
        except Exception as exc:
            raise ValueError(f"Core Banking HTTP connection failure: {exc}") from exc
