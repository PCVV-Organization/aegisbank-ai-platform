"""Opt-in Docker Compose acceptance run for the v0.11 local lab."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deploy" / "local" / "docker-compose.yml"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def _health_url() -> bool:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8000/health/ready", timeout=3
        ) as response:
            return response.status == 200
    except OSError:
        return False


def _message_flow() -> bool:
    sys.path.insert(0, str(ROOT / "ai" / "agent" / "src"))
    sys.path.insert(0, str(ROOT / "services" / "mock-core-banking" / "src"))
    from aegisbank_agent.reliability.azure_servicebus_adapter import (
        AzureServiceBusMessageBus,
    )
    from aegisbank_agent.reliability.messaging import IdempotentConsumer, Message

    adapter = AzureServiceBusMessageBus(
        connection_string=os.environ.get("AEGISBANK_SERVICEBUS_CONN_STR"),
        default_queue_name="service-requests",
    )
    message = Message(
        event_id=f"v011-{int(time.time())}",
        event_type="ServiceRequestCreated",
        aggregate_type="ServiceRequest",
        aggregate_id="SR-CONTAINER-001",
        payload={"customer_id": "CUST-0001", "source": "container-acceptance"},
    )
    seen: list[str] = []
    consumer = IdempotentConsumer(handler=lambda event: seen.append(event.event_id))
    try:
        adapter.publish("service-requests", message)
        adapter.publish("service-requests", message)
        received = adapter.receive_and_settle(
            queue_name="service-requests", handler=consumer.handle, max_messages=10
        )
        return len(received) == 2 and seen == [message.event_id]
    finally:
        adapter.close()


def main() -> int:
    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("AEGISBANK_V0.11_MSSQL_PASSWORD_REQUIRED")
        return 2

    compose = ["docker", "compose", "-f", str(COMPOSE)]
    started = True
    try:
        result = _run(*compose, "up", "-d", "--build")
        if result.returncode:
            print(result.stdout + result.stderr)
            return result.returncode
        for _ in range(36):
            if _health_url():
                break
            time.sleep(5)
        else:
            print("AEGISBANK_V0.11_CORE_HEALTH_TIMEOUT")
            return 1

        status = _run(*compose, "ps", "--format", "json")
        print(status.stdout)
        if status.returncode:
            return status.returncode
        try:
            parsed = json.loads(status.stdout)
            records = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            records = [
                json.loads(line) for line in status.stdout.splitlines() if line.strip()
            ]
        names = {record.get("Service") or record.get("Name") for record in records}
        required = {"mock-core-banking", "mssql", "servicebus-emulator"}
        if not required.issubset(names):
            print(f"AEGISBANK_V0.11_SERVICES_MISSING: {sorted(required - names)}")
            return 1
        print("CONTAINER_HEALTH=PASS")
        print("CORE_API=PASS")
        print("SERVICE_BUS_STACK=RUNNING")
        time.sleep(30)
        try:
            message_ok = _message_flow()
        except Exception as exc:
            print(f"AEGISBANK_V0.11_MESSAGE_FLOW_ERROR: {type(exc).__name__}")
            return 1
        if not message_ok:
            print("AEGISBANK_V0.11_MESSAGE_FLOW_FAILED")
            return 1
        print("MESSAGE_FLOW=PASS")
        return 0
    finally:
        if started:
            down = _run(*compose, "down")
            if down.returncode:
                print(down.stdout + down.stderr, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
