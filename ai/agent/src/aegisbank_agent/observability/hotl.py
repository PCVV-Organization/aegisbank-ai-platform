"""Human-on-the-Loop (HOTL) supervisory control and write kill-switch foundation."""

from __future__ import annotations

import threading
from typing import Any, Callable

from .audit import AuditEventType, AuditLogger, get_audit_logger


class HOTLSupervisor:
    """Controller for monitoring and dynamically disabling write capabilities."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._lock = threading.Lock()
        self._writes_enabled: bool = True
        self._kill_switch_reason: str = ""
        self._audit = audit_logger or get_audit_logger()
        self._alert_subscribers: list[Callable[[str, dict[str, Any]], None]] = []

    @property
    def is_write_allowed(self) -> bool:
        """Check if banking write operations are permitted by supervisor."""
        with self._lock:
            return self._writes_enabled

    @property
    def kill_switch_reason(self) -> str:
        with self._lock:
            return self._kill_switch_reason

    def engage_kill_switch(
        self,
        reason: str,
        actor: str = "SUPERVISOR",
        correlation_id: str = "HOTL-SUPERVISORY",
    ) -> None:
        """Engage supervisory kill-switch to immediately disable all write tools."""
        with self._lock:
            self._writes_enabled = False
            self._kill_switch_reason = reason

        self._audit.record(
            event_type=AuditEventType.HOTL_KILL_SWITCH_ENGAGED,
            correlation_id=correlation_id,
            actor=actor,
            payload={"reason": reason},
        )
        self._notify_alerts("KILL_SWITCH_ENGAGED", {"reason": reason, "actor": actor})

    def disengage_kill_switch(
        self,
        actor: str = "SUPERVISOR",
        correlation_id: str = "HOTL-SUPERVISORY",
    ) -> None:
        """Disengage supervisory kill-switch to restore normal operations."""
        with self._lock:
            self._writes_enabled = True
            self._kill_switch_reason = ""

        self._audit.record(
            event_type=AuditEventType.HOTL_KILL_SWITCH_DISENGAGED,
            correlation_id=correlation_id,
            actor=actor,
            payload={"action": "restored"},
        )
        self._notify_alerts("KILL_SWITCH_DISENGAGED", {"actor": actor})

    def subscribe_alerts(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        self._alert_subscribers.append(callback)

    def _notify_alerts(self, event_name: str, payload: dict[str, Any]) -> None:
        for sub in self._alert_subscribers:
            try:
                sub(event_name, payload)
            except Exception:
                pass


_GLOBAL_HOTL = HOTLSupervisor()


def get_hotl_supervisor() -> HOTLSupervisor:
    """Retrieve global HOTL supervisor instance."""
    return _GLOBAL_HOTL
