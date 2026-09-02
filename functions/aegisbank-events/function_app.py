"""Azure Functions Python v2 entry point for AegisBank domain events."""

from __future__ import annotations

import azure.functions as func
from service_request_handler import ServiceRequestEventHandler

app = func.FunctionApp()
_handler = ServiceRequestEventHandler()


@app.function_name(name="service_request_created")
@app.event_grid_trigger(arg_name="event")
def service_request_created(event: func.CloudEvent) -> None:
    """Validate and process one CloudEvents 1.0 domain notification."""
    _handler.handle_cloud_event(event)
