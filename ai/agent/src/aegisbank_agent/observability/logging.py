"""Structured JSON logging with automatic sensitive data and secret redaction."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from .context import ObservabilityContext

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(api[_-]?key|password|secret|token|authorization|bearer|cvv|pin|access[_-]?token)"
)
SECRET_VALUE_PATTERN = re.compile(r"(?i)(sk-[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9_\-\.]+)")


class RedactionFilter:
    """Sanitizes sensitive keywords, tokens, credentials, and raw secrets from telemetry."""

    @classmethod
    def redact_value(cls, key: str, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: cls.redact_value(k, v) for k, v in value.items()}
        if isinstance(value, list):
            return [cls.redact_value(key, v) for v in value]
        if isinstance(value, str):
            if SENSITIVE_KEY_PATTERN.search(key):
                return "[REDACTED]"
            # Redact raw API key patterns within strings
            redacted_str = SECRET_VALUE_PATTERN.sub("[REDACTED]", value)
            return redacted_str
        return value

    @classmethod
    def redact_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        return {k: cls.redact_value(k, v) for k, v in data.items()}


class StructuredLogger:
    """Outputs standardized, redacted JSON log entries with tracing correlation."""

    def __init__(self, name: str = "aegisbank.agent") -> None:
        self.name = name
        self._records: list[dict[str, Any]] = []
        self._raw_logger = logging.getLogger(name)

    @property
    def emitted_logs(self) -> list[dict[str, Any]]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()

    def log(
        self,
        level: str,
        event_name: str,
        context: ObservabilityContext | None = None,
        tool_name: str | None = None,
        approval_status: str | None = None,
        execution_status: str | None = None,
        latency_ms: float | None = None,
        error_code: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Emit a structured JSON log entry."""
        now = datetime.now(timezone.utc).isoformat()
        ctx_dict = context.to_dict() if context else {}

        log_payload: dict[str, Any] = {
            "timestamp": now,
            "level": level.upper(),
            "logger": self.name,
            "event_name": event_name,
            "correlation_id": ctx_dict.get("correlation_id", ""),
            "trace_id": ctx_dict.get("trace_id", "0" * 32),
            "span_id": ctx_dict.get("span_id", "0" * 16),
            "session_id": ctx_dict.get("session_id", "default_session"),
            "customer_id": ctx_dict.get("customer_id", ""),
            "tool_name": tool_name,
            "approval_status": approval_status,
            "execution_status": execution_status,
            "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
            "error_code": error_code,
        }

        if extra:
            log_payload["details"] = RedactionFilter.redact_dict(extra)

        # Apply top-level redaction
        clean_entry = RedactionFilter.redact_dict(log_payload)
        self._records.append(clean_entry)

        json_str = json.dumps(clean_entry, ensure_ascii=False)
        if level.upper() == "ERROR":
            self._raw_logger.error(json_str)
        elif level.upper() == "WARNING":
            self._raw_logger.warning(json_str)
        else:
            self._raw_logger.info(json_str)

        return clean_entry

    def info(self, event_name: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("INFO", event_name, **kwargs)

    def warning(self, event_name: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("WARNING", event_name, **kwargs)

    def error(self, event_name: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("ERROR", event_name, **kwargs)


_DEFAULT_LOGGER = StructuredLogger()


def get_logger(name: str = "aegisbank.agent") -> StructuredLogger:
    """Retrieve global structured logger instance."""
    return _DEFAULT_LOGGER
