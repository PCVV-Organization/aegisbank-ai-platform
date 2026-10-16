from __future__ import annotations

import pytest

from aegisbank_agent.customer_auth import CustomerAuth, account_key, password_hash, verify_password


class Store:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self.version = 0

    def read(self, key):
        item = self.items.get(key)
        return dict(item, _etag=item.get("_etag", "1")) if item else None

    def create(self, item):
        if item["id"] in self.items:
            raise RuntimeError("conflict")
        self.version += 1
        self.items[item["id"]] = dict(item, _etag=str(self.version))

    def replace(self, item, etag):
        current = self.items.get(item["id"])
        if not current or current.get("_etag") != etag:
            from aegisbank_agent.customer_auth import ConflictError

            raise ConflictError
        self.version += 1
        self.items[item["id"]] = dict(item, _etag=str(self.version))

    def delete(self, key):
        self.items.pop(key, None)

    def ready(self):
        return None


def test_scrypt_hash_and_wrong_password():
    encoded = password_hash("synthetic-password")
    assert verify_password("synthetic-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_login_binds_customer_and_logout_revokes_session():
    store = Store()
    auth = CustomerAuth(store)
    auth.enroll("12345678", "synthetic-password", "CUST-0001")
    result = auth.login("12345678", "synthetic-password")
    assert result["customer_id"] == "CUST-0001"
    assert auth.authenticate(result["access_token"]) == "CUST-0001"
    auth.logout(result["access_token"])
    with pytest.raises(Exception):
        auth.authenticate(result["access_token"])


def test_invalid_customer_binding_is_rejected():
    store = Store()
    auth = CustomerAuth(store)
    with pytest.raises(ValueError):
        auth.enroll("12345678", "synthetic-password", "CUST-999")
    with pytest.raises(ValueError):
        account_key("1234")
