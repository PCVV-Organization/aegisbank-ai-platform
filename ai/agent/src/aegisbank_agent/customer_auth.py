"""Explicit synthetic-customer authentication for the Students staging laboratory.

Passwords use scrypt; bearer sessions are random, short lived, and stored only as
SHA-256 digests. Cosmos conditional writes serialize admission to password checks.
There is no public enrollment endpoint or in-memory cloud fallback.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from collections.abc import Callable
from typing import Any, Protocol

from fastapi import HTTPException

from .configuration.environment import resolve_runtime_environment

SESSION_SECONDS = 900
ATTEMPT_WINDOW = 900
ACCOUNT_ATTEMPTS = 5
GLOBAL_ATTEMPTS = 60


class ConflictError(Exception):
    """An optimistic write lost a race; the caller must re-read."""


class AuthStore(Protocol):
    def read(self, key: str) -> dict[str, Any] | None: ...
    def create(self, item: dict[str, Any]) -> None: ...
    def replace(self, item: dict[str, Any], etag: str) -> None: ...
    def delete(self, key: str) -> None: ...
    def ready(self) -> None: ...


class CosmosAuthStore:
    """Auth-specific atomic adapter; never auto-creates cloud resources.

    CosmosRepository's automatic initialization and unconditional upserts cannot
    provide the compare-and-swap contract required by credential throttling.
    """

    def __init__(self) -> None:
        from azure.cosmos import CosmosClient

        from .configuration.identity import resolve_azure_credential

        endpoint = os.getenv("AEGISBANK_AUTH_COSMOS_ENDPOINT", "")
        if not re.fullmatch(r"https://[a-z0-9-]+\.documents\.azure\.com:443/?", endpoint):
            raise ValueError("Auth Cosmos HTTPS endpoint is required")
        self.client = CosmosClient(
            endpoint,
            credential=resolve_azure_credential(resolve_runtime_environment()),
            connection_timeout=5,
            timeout=10,
            retry_total=2,
        )
        database = os.getenv("AEGISBANK_AUTH_COSMOS_DATABASE", "aegisbank-auth")
        container = os.getenv("AEGISBANK_AUTH_COSMOS_CONTAINER", "identities")
        self.container = self.client.get_database_client(database).get_container_client(container)

    def ready(self) -> None:
        props = self.container.read()
        if props.get("partitionKey", {}).get("paths") != ["/id"]:
            raise ValueError("Auth store partition contract mismatch")
        if props.get("defaultTtl") != -1:
            raise ValueError("Auth store TTL contract mismatch")

    def read(self, key: str) -> dict[str, Any] | None:
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        try:
            return self.container.read_item(item=key, partition_key=key)
        except CosmosResourceNotFoundError:
            return None

    def create(self, item: dict[str, Any]) -> None:
        from azure.cosmos.exceptions import CosmosResourceExistsError

        try:
            self.container.create_item(body=item)
        except CosmosResourceExistsError as exc:
            raise ConflictError from exc

    def replace(self, item: dict[str, Any], etag: str) -> None:
        from azure.core import MatchConditions
        from azure.cosmos.exceptions import CosmosHttpResponseError

        try:
            self.container.replace_item(
                item=item["id"],
                body=item,
                etag=etag,
                match_condition=MatchConditions.IfNotModified,
            )
        except CosmosHttpResponseError as exc:
            if exc.status_code == 412:
                raise ConflictError from exc
            raise

    def delete(self, key: str) -> None:
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        try:
            self.container.delete_item(item=key, partition_key=key)
        except CosmosResourceNotFoundError:
            pass


def password_hash(password: str, salt: str | None = None) -> str:
    """OWASP scrypt alternative: N=2^14, r=8, p=5 (16 MiB per check)."""
    if not 15 <= len(password) <= 128:
        raise ValueError("Password must contain 15 to 128 characters")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=bytes.fromhex(salt),
        n=16384,
        r=8,
        p=5,
        maxmem=64 * 1024 * 1024,
    ).hex()
    return f"scrypt-v1${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        version, salt, _digest = encoded.split("$")
        return version == "scrypt-v1" and hmac.compare_digest(
            encoded, password_hash(password, salt)
        )
    except ValueError, TypeError:
        return False


def account_key(dni: str) -> str:
    if not re.fullmatch(r"[0-9]{8}", dni):
        raise ValueError("Synthetic DNI must contain eight ASCII digits")
    return "account-" + hashlib.sha256(dni.encode("ascii")).hexdigest()


def denied() -> HTTPException:
    return HTTPException(
        401,
        "Credenciales o sesión no válidas",
        headers={
            "WWW-Authenticate": "Bearer",
            "Cache-Control": "no-store",
        },
    )


class CustomerAuth:
    def __init__(self, store: AuthStore, clock: Callable[[], float] = time.time) -> None:
        self.store = store
        self.clock = clock
        # Same work factor for unknown users; this is not an account credential.
        self._dummy = password_hash(secrets.token_urlsafe(32))

    def _reserve(self, key: str, limit: int, window: int) -> None:
        """Persist an attempt BEFORE hashing, across workers and restarts.

        Only conflicts are retried. An unavailable store or exhausted contention
        budget cannot admit a password check. Successful logins consume a slot.
        """
        now = int(self.clock())
        for _ in range(8):
            current = self.store.read(key)
            fresh = current is None or now >= current["until"]
            count = 0 if fresh else current["count"]
            if count >= limit:
                raise HTTPException(
                    429,
                    "Demasiados intentos. Intenta más tarde.",
                    headers={
                        "Retry-After": str(max(1, current["until"] - now)),
                    },
                )
            item = {
                "id": key,
                "count": count + 1,
                "until": now + window if fresh else current["until"],
                "ttl": window * 2,
            }
            try:
                if current is None:
                    self.store.create(item)
                else:
                    self.store.replace(item, current["_etag"])
                return
            except ConflictError:
                continue
        raise HTTPException(503, "Autenticación temporalmente no disponible")

    def login(self, dni: str, password: str) -> dict[str, Any]:
        self._reserve("throttle-global", GLOBAL_ATTEMPTS, 60)
        key = account_key(dni)
        self._reserve("throttle-" + key, ACCOUNT_ATTEMPTS, ATTEMPT_WINDOW)
        account = self.store.read(key)
        valid = verify_password(password, account["password_hash"] if account else self._dummy)
        if not valid or not account or account.get("disabled"):
            raise denied()
        customer_id = account.get("customer_id", "")
        if not re.fullmatch(r"CUST-[0-9]{4}", customer_id):
            raise denied()
        token = secrets.token_urlsafe(32)
        expires = int(self.clock()) + SESSION_SECONDS
        self.store.create(
            {
                "id": self._session_key(token),
                "account_id": key,
                "epoch": account["epoch"],
                "expires": expires,
                "ttl": SESSION_SECONDS,
            }
        )
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_at": expires,
            "customer_id": customer_id,
        }

    @staticmethod
    def _session_key(token: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
            raise denied()
        return "session-" + hashlib.sha256(token.encode("ascii")).hexdigest()

    def authenticate(self, token: str) -> str:
        for _ in range(8):
            session = self.store.read(self._session_key(token))
            if not session or self.clock() >= session["expires"]:
                raise denied()
            account = self.store.read(session["account_id"])
            if not account or account.get("disabled") or account["epoch"] != session["epoch"]:
                raise denied()
            customer = account.get("customer_id", "")
            if not re.fullmatch(r"CUST-[0-9]{4}", customer):
                raise denied()
            try:
                # Conditional writes fence stale reads across SDK clients under
                # Session consistency: deleted sessions and rotated accounts
                # cannot authorize using an older replica's document version.
                self.store.replace(session, session["_etag"])
                self.store.replace(account, account["_etag"])
                return customer
            except ConflictError:
                continue
        raise HTTPException(503, "Autenticación temporalmente no disponible")

    def logout(self, token: str) -> None:
        self.store.delete(self._session_key(token))

    def enroll(self, dni: str, password: str, customer_id: str, *, rotate: bool = False) -> None:
        """Operator-only CLI entry; no API accepts customer mappings or passwords."""
        if not re.fullmatch(r"CUST-[0-9]{4}", customer_id):
            raise ValueError("A synthetic CUST identifier is required")
        key = account_key(dni)
        current = self.store.read(key)
        if current and not rotate:
            raise ValueError("Account exists; use explicit rotation to revoke its sessions")
        if current and current["customer_id"] != customer_id:
            raise ValueError("Existing customer binding cannot be changed")
        item = {
            "id": key,
            "customer_id": customer_id,
            "password_hash": password_hash(password),
            "epoch": secrets.token_hex(16),
            "disabled": False,
            "ttl": -1,
        }
        if current:
            self.store.replace(item, current["_etag"])
        else:
            self.store.create(item)
