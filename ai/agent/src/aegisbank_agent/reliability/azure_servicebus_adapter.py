"""Azure Service Bus Messaging Adapter for AegisBank AI Platform.

Implements the canonical `MessageBus` interface using the official `azure-servicebus` SDK.
Connects to the local Azure Service Bus Emulator via AMQP (or cloud Azure Service Bus in future).
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, Callable

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError

from ..configuration.environment import resolve_runtime_environment
from .messaging import Message, MessageBus

logger = logging.getLogger("aegisbank.reliability.azure_servicebus")

# Default connection string for the official local Azure Service Bus Emulator
DEFAULT_EMULATOR_CONN_STR = (
    "Endpoint=sb://127.0.0.1;SharedAccessKeyName=RootManageSharedAccessKey;"
    "SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"
)


class AzureServiceBusMessageBus(MessageBus):
    """Adapter connecting canonical MessageBus to Azure Service Bus (emulator or cloud)."""

    def __init__(
        self,
        connection_string: str | None = None,
        default_queue_name: str = "service-requests",
        fully_qualified_namespace: str | None = None,
        credential: Any = None,
    ) -> None:
        environment = resolve_runtime_environment()
        self.fully_qualified_namespace = fully_qualified_namespace or os.getenv(
            "AEGISBANK_SERVICEBUS_NAMESPACE"
        )
        self.credential = credential
        if environment.is_cloud:
            if not self.fully_qualified_namespace:
                raise RuntimeError(
                    "AEGISBANK_SERVICEBUS_NAMESPACE is required in cloud environments"
                )
            self.connection_string = None
        else:
            self.connection_string = (
                connection_string
                or os.getenv("AEGISBANK_SERVICEBUS_CONN_STR")
                or DEFAULT_EMULATOR_CONN_STR
            )
        self.default_queue_name = default_queue_name
        self._client: ServiceBusClient | None = None

    def _get_client(self) -> ServiceBusClient:
        if self._client is None:
            if self.fully_qualified_namespace is not None and self.connection_string is None:
                if self.credential is None:
                    from azure.identity import DefaultAzureCredential

                    self.credential = DefaultAzureCredential()
                self._client = ServiceBusClient(
                    fully_qualified_namespace=self.fully_qualified_namespace,
                    credential=self.credential,
                )
            else:
                self._client = ServiceBusClient.from_connection_string(self.connection_string)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def publish(self, topic: str, message: Message) -> None:
        """Publish a canonical Message to an Azure Service Bus queue or topic."""
        target_entity = topic or self.default_queue_name
        client = self._get_client()

        payload_dict = {
            "event_id": message.event_id,
            "event_type": message.event_type,
            "aggregate_type": message.aggregate_type,
            "aggregate_id": message.aggregate_id,
            "payload": message.payload,
            "created_at": message.created_at.isoformat(),
        }

        body_str = json.dumps(payload_dict, ensure_ascii=False)
        sb_message = ServiceBusMessage(
            body=body_str,
            message_id=message.event_id,
            content_type="application/json",
            application_properties={
                "event_type": message.event_type,
                "aggregate_type": message.aggregate_type,
                "aggregate_id": message.aggregate_id,
            },
        )

        sender = client.get_queue_sender(queue_name=target_entity)
        with sender:
            sender.send_messages(sb_message)
            logger.info(
                "Published message to Azure Service Bus queue '%s': event_id=%s, type=%s",
                target_entity,
                message.event_id,
                message.event_type,
            )

    def receive_and_settle(
        self,
        queue_name: str | None = None,
        handler: Callable[[Message], bool] | None = None,
        max_messages: int = 10,
        max_wait_time: float = 3.0,
    ) -> list[dict[str, Any]]:
        """Receive messages from queue, convert to canonical Message, execute handler and settle."""
        target_entity = queue_name or self.default_queue_name
        client = self._get_client()
        receiver = client.get_queue_receiver(queue_name=target_entity, max_wait_time=max_wait_time)
        processed: list[dict[str, Any]] = []

        with receiver:
            received_messages = receiver.receive_messages(
                max_message_count=max_messages, max_wait_time=max_wait_time
            )
            for sb_msg in received_messages:
                try:
                    if isinstance(sb_msg.body, str):
                        raw_body = sb_msg.body
                    elif isinstance(sb_msg.body, (bytes, bytearray)):
                        raw_body = sb_msg.body.decode("utf-8")
                    elif isinstance(sb_msg.body, Iterable):
                        raw_body = b"".join(sb_msg.body).decode("utf-8")
                    else:
                        raw_body = str(sb_msg.body)

                    data = json.loads(raw_body)
                    created_at_val = data.get("created_at")
                    created_at = (
                        datetime.fromisoformat(created_at_val)
                        if created_at_val
                        else datetime.now(timezone.utc)
                    )

                    canonical_msg = Message(
                        event_id=data.get("event_id", str(sb_msg.message_id)),
                        event_type=data.get("event_type", "unknown"),
                        aggregate_type=data.get("aggregate_type", "unknown"),
                        aggregate_id=data.get("aggregate_id", "unknown"),
                        payload=data.get("payload", {}),
                        created_at=created_at,
                    )

                    success = True
                    if handler is not None:
                        success = handler(canonical_msg)

                    if success:
                        receiver.complete_message(sb_msg)
                        status = "COMPLETED"
                    else:
                        receiver.abandon_message(sb_msg)
                        status = "ABANDONED"

                    processed.append(
                        {
                            "event_id": canonical_msg.event_id,
                            "status": status,
                            "message": canonical_msg,
                        }
                    )
                except Exception as exc:
                    logger.error(
                        "Error processing message %s, routing to DLQ: %s",
                        sb_msg.message_id,
                        exc,
                    )
                    try:
                        receiver.dead_letter_message(
                            sb_msg,
                            reason="ProcessingException",
                            error_description=str(exc)[:500],
                        )
                        processed.append(
                            {
                                "event_id": str(sb_msg.message_id),
                                "status": "DEAD_LETTERED",
                                "error": str(exc),
                            }
                        )
                    except ServiceBusError as sb_err:
                        logger.error("Failed to dead-letter message: %s", sb_err)
                        receiver.abandon_message(sb_msg)

        return processed
