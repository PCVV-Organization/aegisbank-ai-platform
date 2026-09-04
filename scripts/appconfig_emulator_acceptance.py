"""Live Azure App Configuration Emulator acceptance runner for v0.14.0.

Validates end-to-end configuration management, labels, feature flags,
Key Vault reference resolution, dynamic refresh, and secret hygiene
against the official Microsoft App Configuration Emulator container.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "appconfig_emulator_evidence.json"
CONTAINER_NAME = "aegisbank-app-configuration-emulator"
IMAGE_TAG = "mcr.microsoft.com/azure-app-configuration/app-configuration-emulator:1.2.0"
IMAGE_DIGEST = "sha256:f84ca52fcf51aab3bad8a0363198c161e8a79eb41712d27779f6e0eb777c7000"
PINNED_IMAGE = f"{IMAGE_TAG}@{IMAGE_DIGEST}"
HOST_PORT = 8483
BASE_URL = f"http://127.0.0.1:{HOST_PORT}"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def ensure_emulator_container() -> bool:
    """Ensure the App Configuration Emulator container is running and healthy."""
    ps = _run("docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}")
    if CONTAINER_NAME not in ps.stdout:
        print(f"[*] Starting {CONTAINER_NAME} container...")
        _run("docker", "rm", "-f", CONTAINER_NAME)
        run_res = _run(
            "docker",
            "run",
            "-d",
            "--name",
            CONTAINER_NAME,
            "-p",
            f"127.0.0.1:{HOST_PORT}:{HOST_PORT}",
            "-e",
            "Tenant:AnonymousAuthEnabled=true",
            "-e",
            "Authentication:Anonymous:AnonymousUserRole=Owner",
            PINNED_IMAGE,
        )
        if run_res.returncode != 0:
            print(f"[!] Failed to run container: {run_res.stderr}")
            return False

    # Wait for /health to respond Healthy
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2.0) as resp:
                if resp.status == 200:
                    print("[*] App Configuration Emulator is healthy.")
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(1.0)

    print("[!] Timed out waiting for emulator /health.")
    return False


def run_acceptance_suite() -> dict[str, Any]:
    """Execute all acceptance verification checks against the live emulator."""
    sys.path.insert(0, str(ROOT / "ai" / "agent" / "src"))
    from aegisbank_agent.configuration.config import (
        AppConfigurationEmulatorProvider,
        MissingConfigurationKey,
        coerce_bool,
        coerce_int,
    )
    from aegisbank_agent.configuration.secrets import (
        KeyVaultReferenceResolver,
        LocalSyntheticSecretProvider,
    )

    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "emulator_image": PINNED_IMAGE,
        "endpoint": BASE_URL,
        "steps": {},
        "status": "FAILED",
        "maturity_tags": [
            "LOCAL-APPCONFIG-COVERED",
            "CLOUD-APPCONFIG-PENDING",
            "LOCAL-SECRETS-COVERED",
            "CLOUD-KEYVAULT-PENDING",
            "MANAGED-IDENTITY-CLOUD-PENDING",
            "DEFAULT-AZURE-CREDENTIAL-LOCAL-COVERED",
        ],
    }

    steps = results["steps"]

    # Step 1: Health endpoint probe
    with urllib.request.urlopen(f"{BASE_URL}/health", timeout=3.0) as resp:
        health_text = resp.read().decode("utf-8").strip()
        assert resp.status == 200
        assert health_text == "Healthy"
    steps["health_check"] = {"status": "PASS", "response": health_text}
    print("  [✓] Step 1: Health check passed (HTTP 200 Healthy)")

    # Step 2: Multi-environment label separation
    local_provider = AppConfigurationEmulatorProvider(endpoint=BASE_URL, label="local")
    prod_provider = AppConfigurationEmulatorProvider(endpoint=BASE_URL, label="production")

    local_provider.set_kv("rag.top_k", "10", label="local")
    prod_provider.set_kv("rag.top_k", "5", label="production")

    local_provider.refresh()
    prod_provider.refresh()

    local_top_k = coerce_int(local_provider.get("rag.top_k"), "rag.top_k")
    prod_top_k = coerce_int(prod_provider.get("rag.top_k"), "rag.top_k")
    assert local_top_k == 10
    assert prod_top_k == 5
    steps["label_separation"] = {
        "status": "PASS",
        "local_top_k": local_top_k,
        "prod_top_k": prod_top_k,
    }
    print("  [✓] Step 2: Multi-environment label isolation verified (local=10, prod=5)")

    # Step 3: Feature Flag management
    local_provider.set_feature_flag("agent_write_enabled", enabled=False, label="local")
    local_provider.refresh()

    ff_raw = local_provider.get(".appconfig.featureflag/agent_write_enabled")
    assert ff_raw is not None
    ff_obj = json.loads(ff_raw)
    assert ff_obj["id"] == "agent_write_enabled"
    assert ff_obj["enabled"] is False
    steps["feature_flags"] = {
        "status": "PASS",
        "flag_id": ff_obj["id"],
        "enabled": ff_obj["enabled"],
    }
    print("  [✓] Step 3: Feature Flag stored and verified (.appconfig.featureflag/agent_write_enabled)")

    # Step 4: Key Vault Reference pattern and resolution
    secret_store = LocalSyntheticSecretProvider({
        "db-sa-password": "synthetic-ultra-secure-pass-98765",
    })
    resolver = KeyVaultReferenceResolver(secret_provider=secret_store)

    vault_uri = "https://aegisbank-kv.vault.azure.net/secrets/db-sa-password"
    local_provider.set_keyvault_reference(
        key="database.password.ref",
        vault_uri=vault_uri,
        label="local",
    )
    local_provider.refresh()

    raw_kv_ref = local_provider.get("database.password.ref")
    assert raw_kv_ref is not None
    resolved_secret = resolver.resolve(raw_kv_ref)
    assert resolved_secret == "synthetic-ultra-secure-pass-98765"
    steps["keyvault_reference"] = {
        "status": "PASS",
        "key": "database.password.ref",
        "reference_stored": raw_kv_ref,
        "resolved_successfully": True,
    }
    print("  [✓] Step 4: Key Vault reference stored and resolved safely without plaintext in config")

    # Step 5: Dynamic config refresh
    reader = AppConfigurationEmulatorProvider(endpoint=BASE_URL, label="local")
    admin = AppConfigurationEmulatorProvider(endpoint=BASE_URL, label="local")

    admin.set_kv("runtime.maintenance_mode", "false", label="local")
    reader.refresh()
    assert coerce_bool(reader.get("runtime.maintenance_mode"), "runtime.maintenance_mode") is False

    admin.set_kv("runtime.maintenance_mode", "true", label="local")
    # Reader cache holds false until refresh
    assert coerce_bool(reader.get("runtime.maintenance_mode"), "runtime.maintenance_mode") is False

    reader.refresh()
    assert coerce_bool(reader.get("runtime.maintenance_mode"), "runtime.maintenance_mode") is True
    steps["dynamic_refresh"] = {
        "status": "PASS",
        "key": "runtime.maintenance_mode",
        "cache_isolation_verified": True,
        "refresh_verified": True,
    }
    print("  [✓] Step 5: Dynamic config refresh & cache isolation verified")

    # Step 6: Fail-fast on missing keys
    try:
        local_provider.require("non.existent.key.for.test")
        raise AssertionError("Expected MissingConfigurationKey was not raised")
    except MissingConfigurationKey:
        pass
    steps["fail_fast"] = {"status": "PASS", "missing_key_behavior": "MissingConfigurationKey"}
    print("  [✓] Step 6: Fail-fast on missing key verified")

    # Step 7: Secret Hygiene Assertion
    # Scan all keys in emulator; verify no plaintext credentials stored
    all_kv_req = urllib.request.urlopen(f"{BASE_URL}/kv?api-version=1.0", timeout=3.0)
    all_kv = json.loads(all_kv_req.read().decode("utf-8")).get("items", [])
    for item in all_kv:
        val = item.get("value") or ""
        # Must not contain actual credentials or passwords
        assert "synthetic-ultra-secure-pass" not in val, f"Secret leaked in config key {item['key']}"
    steps["secret_hygiene"] = {
        "status": "PASS",
        "keys_scanned": len(all_kv),
        "zero_plaintext_secrets_found": True,
    }
    print(f"  [✓] Step 7: Secret hygiene assertion verified across {len(all_kv)} keys")

    results["status"] = "PASS"
    return results


def main() -> int:
    print("=" * 70)
    print("AegisBank v0.14.0 — Azure App Configuration Emulator Acceptance")
    print("=" * 70)

    if not ensure_emulator_container():
        print("[!] FATAL: App Configuration Emulator container could not be prepared.")
        return 1

    try:
        evidence = run_acceptance_suite()
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Acceptance suite failed with exception: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    print("\n" + "=" * 70)
    print(f"[+] ACCEPTANCE COMPLETED: {evidence['status']}")
    print(f"[+] Evidence report written to: {REPORT_PATH}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
