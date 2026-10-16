"""Durable Session Store for conversational continuity and entity memory.

Enforces strict customer ownership isolation: a session belonging to customer A
cannot be accessed, resumed, or mutated by customer B.
Uses embedded SQLite for zero-configuration, zero-cost local durability.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_SESSION_DB_ENV = "AEGISBANK_SESSION_DB_PATH"


class OwnershipViolationError(PermissionError):
    """Raised when an operation attempts cross-customer session access."""


@dataclass
class SessionData:
    session_id: str
    customer_id: str
    last_loan_id: str | None = None
    last_account_id: str | None = None
    last_intent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """A user-visible message owned by one authenticated customer session."""

    message_id: int
    session_id: str
    customer_id: str
    role: str
    content: str
    created_at: str


def _resolve_db_path(custom_path: Path | str | None = None) -> Path:
    if custom_path is not None:
        if str(custom_path) == ":memory:":
            return Path(":memory:")
        return Path(custom_path)
    env_override = os.environ.get(DEFAULT_SESSION_DB_ENV, "").strip()
    if env_override:
        if env_override == ":memory:":
            return Path(":memory:")
        return Path(env_override)
    # Default to data/sessions.db relative to repository root
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "data" / "sessions.db"


class SQLiteSessionStore:
    """Durable SQLite-backed store for agent session and entity state."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._path = _resolve_db_path(db_path)
        if str(self._path) != ":memory:":
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if str(self._path) == ":memory:":
            if not hasattr(self, "_mem_conn"):
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
            return self._mem_conn
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agent_sessions (
                        session_id TEXT PRIMARY KEY,
                        customer_id TEXT NOT NULL,
                        last_loan_id TEXT,
                        last_account_id TEXT,
                        last_intent TEXT,
                        metadata_json TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agent_messages (
                        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        customer_id TEXT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES agent_sessions(session_id)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON agent_messages(session_id, message_id)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_sessions_customer
                    ON agent_sessions(customer_id)
                    """
                )
        finally:
            if str(self._path) != ":memory:":
                conn.close()

    def get_or_create(self, session_id: str, customer_id: str) -> SessionData:
        """Retrieve existing session or initialize a new one.

        Raises OwnershipViolationError if session exists for a different customer_id.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agent_sessions WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            if row is not None:
                stored_cust = row["customer_id"]
                if stored_cust != customer_id:
                    raise OwnershipViolationError(
                        f"Cross-customer violation: Session '{session_id}' is owned by "
                        f"'{stored_cust}', but access was attempted by '{customer_id}'."
                    )
                meta = {}
                if row["metadata_json"]:
                    try:
                        meta = json.loads(row["metadata_json"])
                    except json.JSONDecodeError:
                        meta = {}
                return SessionData(
                    session_id=row["session_id"],
                    customer_id=row["customer_id"],
                    last_loan_id=row["last_loan_id"],
                    last_account_id=row["last_account_id"],
                    last_intent=row["last_intent"],
                    metadata=meta,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            # Insert new session
            now = datetime.now(timezone.utc).isoformat()
            new_session = SessionData(
                session_id=session_id,
                customer_id=customer_id,
                created_at=now,
                updated_at=now,
            )
            with conn:
                conn.execute(
                    """
                    INSERT INTO agent_sessions (
                        session_id, customer_id, last_loan_id, last_account_id,
                        last_intent, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_session.session_id,
                        new_session.customer_id,
                        new_session.last_loan_id,
                        new_session.last_account_id,
                        new_session.last_intent,
                        json.dumps(new_session.metadata),
                        new_session.created_at,
                        new_session.updated_at,
                    ),
                )
            return new_session
        finally:
            if str(self._path) != ":memory:":
                conn.close()

    def update(self, session: SessionData) -> None:
        """Update an existing session's state and timestamps.

        Verifies customer ownership before mutation.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_id FROM agent_sessions WHERE session_id = ?",
                (session.session_id,),
            )
            row = cursor.fetchone()
            if row is not None and row["customer_id"] != session.customer_id:
                raise OwnershipViolationError(
                    f"Cross-customer mutation denied: Session '{session.session_id}' "
                    f"is owned by '{row['customer_id']}'."
                )

            now = datetime.now(timezone.utc).isoformat()
            session.updated_at = now
            with conn:
                conn.execute(
                    """
                    UPDATE agent_sessions
                    SET last_loan_id = ?,
                        last_account_id = ?,
                        last_intent = ?,
                        metadata_json = ?,
                        updated_at = ?
                    WHERE session_id = ? AND customer_id = ?
                    """,
                    (
                        session.last_loan_id,
                        session.last_account_id,
                        session.last_intent,
                        json.dumps(session.metadata),
                        session.updated_at,
                        session.session_id,
                        session.customer_id,
                    ),
                )
        finally:
            if str(self._path) != ":memory:":
                conn.close()

    def record_loan_access(
        self,
        session_id: str,
        customer_id: str,
        loan_id: str,
        intent: str = "GET_LOAN_DETAILS",
    ) -> None:
        """Record a successful loan consultation in session state."""
        session = self.get_or_create(session_id, customer_id)
        session.last_loan_id = loan_id
        session.last_intent = intent
        self.update(session)

    def append_message(
        self, session_id: str, customer_id: str, role: str, content: str
    ) -> ConversationMessage:
        """Append a redacted user-visible message after verifying ownership."""
        if role not in {"user", "assistant"}:
            raise ValueError("Conversation role must be user or assistant")
        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Conversation content cannot be empty")
        self.get_or_create(session_id, customer_id)
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO agent_messages(session_id, customer_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, customer_id, role, clean_content[:8000], now),
                )
                return ConversationMessage(
                    message_id=int(cursor.lastrowid),
                    session_id=session_id,
                    customer_id=customer_id,
                    role=role,
                    content=clean_content[:8000],
                    created_at=now,
                )
        finally:
            if str(self._path) != ":memory:":
                conn.close()

    def list_messages(
        self, session_id: str, customer_id: str, *, limit: int = 40
    ) -> list[ConversationMessage]:
        """Return only messages owned by the authenticated customer."""
        self.get_or_create(session_id, customer_id)
        bounded_limit = max(1, min(limit, 100))
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT message_id, session_id, customer_id, role, content, created_at
                FROM agent_messages
                WHERE session_id = ? AND customer_id = ?
                ORDER BY message_id DESC LIMIT ?
                """,
                (session_id, customer_id, bounded_limit),
            ).fetchall()
            return [
                ConversationMessage(
                    message_id=int(row["message_id"]),
                    session_id=row["session_id"],
                    customer_id=row["customer_id"],
                    role=row["role"],
                    content=row["content"],
                    created_at=row["created_at"],
                )
                for row in reversed(rows)
            ]
        finally:
            if str(self._path) != ":memory:":
                conn.close()
