"""CloudEvents 1.0 mapping and strict contract validation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

CLOUD_EVENT_SPEC_VERSION = "1.0"
CLOUD_EVENT_TYPE = "com.aegisbank.service-request.created.v1"
CLOUD_EVENT_SOURCE = "urn:aegisbank:mock-core-banking"
CLOUD_EVENT_DATA_SCHEMA = "urn:aegisbank:contracts:service-request-created:v1"


def _resolve_contracts_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parent / "contracts",
        Path(__file__).resolve().parents[2] / "contracts",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parents[2] / "contracts"


_CONTRACTS_DIR = _resolve_contracts_dir()
_DOMAIN_SCHEMA_PATH = _CONTRACTS_DIR / "service-request-created.schema.json"
_CLOUD_EVENT_SCHEMA_PATH = (
    _CONTRACTS_DIR / "cloudevents" / "service-request-created-v1.schema.json"
)


class CloudEventValidationError(ValueError):
    """Raised when an event violates an AegisBank event contract."""


@lru_cache(maxsize=2)
def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(
    instance: Mapping[str, Any], schema_path: Path, contract_name: str
) -> None:
    validator = Draft202012Validator(
        _load_schema(schema_path),
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(dict(instance)), key=lambda error: list(error.path)
    )
    if not errors:
        return

    error = errors[0]
    location = ".".join(str(part) for part in error.absolute_path) or "<root>"
    raise CloudEventValidationError(
        f"{contract_name} validation failed at {location}: {error.message}"
    )


def validate_cloud_event(event: Mapping[str, Any]) -> None:
    """Validate the strict AegisBank CloudEvent envelope and data payload."""
    _validate(event, _CLOUD_EVENT_SCHEMA_PATH, "CloudEvent")


def map_service_request_created(
    domain_event: Mapping[str, Any],
    *,
    correlation_id: str,
    traceparent: str | None = None,
) -> dict[str, Any]:
    """Map the canonical Outbox event to the versioned CloudEvents 1.0 contract."""
    _validate(domain_event, _DOMAIN_SCHEMA_PATH, "ServiceRequestCreated")

    cloud_event: dict[str, Any] = {
        "specversion": CLOUD_EVENT_SPEC_VERSION,
        "id": domain_event["event_id"],
        "source": CLOUD_EVENT_SOURCE,
        "type": CLOUD_EVENT_TYPE,
        "subject": f"/service-requests/{domain_event['aggregate_id']}",
        "time": domain_event["timestamp"],
        "datacontenttype": "application/json",
        "dataschema": CLOUD_EVENT_DATA_SCHEMA,
        "correlationid": correlation_id,
        "data": {
            field: domain_event["payload"][field]
            for field in (
                "service_request_id",
                "customer_id",
                "category",
                "reason_code",
                "reason_label",
                "status",
            )
        },
    }
    if traceparent is not None:
        cloud_event["traceparent"] = traceparent

    validate_cloud_event(cloud_event)
    return cloud_event


def cloud_event_from_sdk(event: Any) -> dict[str, Any]:
    """Flatten an ``azure.functions.CloudEvent`` into its JSON wire representation."""
    if hasattr(event, "to_dict"):
        event_dict = dict(event.to_dict())
        extensions = event_dict.pop("extension_attrs", {})
        if isinstance(extensions, Mapping):
            event_dict.update(extensions)
        return {key: value for key, value in event_dict.items() if value is not None}

    if not (hasattr(event, "id") and hasattr(event, "specversion")):
        raise CloudEventValidationError(
            "Azure Functions binding did not provide a CloudEvent"
        )

    data = (
        event.get_json() if hasattr(event, "get_json") else getattr(event, "data", None)
    )

    time_val = getattr(event, "time", None)
    if hasattr(time_val, "isoformat"):
        time_str = time_val.isoformat()
        if time_str.endswith("+00:00"):
            time_str = time_str[:-6] + "Z"
    else:
        time_str = time_val

    result: dict[str, Any] = {
        "specversion": event.specversion,
        "id": event.id,
        "source": getattr(event, "source", None),
        "type": getattr(event, "type", None),
        "subject": getattr(event, "subject", None),
        "time": time_str,
        "datacontenttype": getattr(event, "datacontenttype", None),
        "dataschema": getattr(event, "dataschema", None),
        "data": data,
    }

    extensions = getattr(event, "extension_attrs", {})
    if isinstance(extensions, Mapping):
        result.update(extensions)

    return {key: value for key, value in result.items() if value is not None}
