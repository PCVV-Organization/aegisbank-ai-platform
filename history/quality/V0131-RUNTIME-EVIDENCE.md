# v0.13.1 — Azure Functions Live Runtime E2E Acceptance: Diagnostic & Validation Report

> **Milestone:** `v0.13.1 — Azure Functions Live Runtime E2E Acceptance`
> **Baseline:** `c3f57310d20f49d81cb4fbf32fe5aa64b4c630d7`
> **Final Outcome:** `WINDOWS_CORE_TOOLS_E2E=BLOCKED` (environmental) | `LOCAL_FUNCTIONS_RUNTIME_E2E=PASS` (verified)
> **Token:** `AEGISBANK_V0.13_FUNCTIONS_RUNTIME_E2E_READY`

---

## 1. Executive Summary & Objective

The primary objective of micro-milestone **`v0.13.1`** is to close the runtime evidence gap identified in `v0.13.0`: proving that the canonical Event Grid CloudEvent handler (`service_request_created`) runs end-to-end through a live Azure Functions Host + Python 3.14 language worker, and not merely through in-process pytest mocks.

This acceptance run achieved:
1. **Definitive Diagnosis of Windows Core Tools Limitation (`Path A: BLOCKED`)**: Identified the exact dynamic library loading failure in the host-spawned Python worker under Windows (`ERROR_FILENAME_EXCED_RANGE` / `0xCE` on `cygrpc.cp314-win_amd64.pyd`).
2. **Deterministic Linux Container Execution (`Path B: PASS`)**: Extracted and verified execution using Microsoft's official container image `mcr.microsoft.com/azure-functions/python:4-python3.14`. Resolved container disk space constraints, secret storage schemas (`ScriptSecretSerializerV1`), and CloudEvent SDK property extraction.
3. **Automated Verification**: Created `scripts/functions_runtime_acceptance.py` and pytest suite `ai/agent/tests/infra/serverless/test_functions_runtime_e2e.py` (3 passed in 0.43s), establishing permanent regression gates.

---

## 2. Tooling Inventory & Environment

| Component | Source / Location | Version / Digest | Role |
|---|---|---|---|
| `func` CLI | pnpm global (`azure-functions-core-tools@4.14.0`) | `4.14.0+4a17060ecc91` | Windows host CLI |
| Functions Host Runtime | Azure Functions Core Tools v4 | `4.1052.200.26352` | Windows local host |
| Python (System) | Windows AMD64 | `3.14.4` | System runtime |
| Python (.venv) | Project Virtualenv | `3.14.4` | Workspace runtime |
| Official Microsoft Image | Microsoft Container Registry (MCR) | `mcr.microsoft.com/azure-functions/python:4-python3.14` (`sha256:410b8676060d...`) | Base Functions runtime |
| Functions WebHost in Container | Official MCR WebHost | `4.1053.200.3` | Container WebHost |
| Docker Engine | Docker Desktop for Windows (WSL2) | `29.7.2` | Container runtime engine |

---

## 3. Path A — Windows Core Tools Diagnosis (`BLOCKED`)

### 3.1 Execution Command
```powershell
Set-Location 'C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform\functions\aegisbank-events'
func start --python "C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform\.venv\Scripts\python.exe" --port 7071
```

### 3.2 Observed Failure Trace
```
[INFO] Function Runtime Version: 4.1052.200.26352
[INFO] Loading functions metadata
[INFO] Fetching metadata for workerRuntime: python
[INFO] Reading functions metadata (Worker)
[INFO] Starting proxy worker. Worker ID: <uuid>, Request ID: <uuid>, Host Address: 127.0.0.1:63483
[ERROR] Microsoft.Azure.WebJobs.Script.Grpc: py exited with code 1 (0x1).
        ImportError: DLL load failed while importing cygrpc: El nombre del archivo o la extensión es demasiado largo.
[ERROR] Language Worker Process exited. Pid=<pid>.
```

### 3.3 Root Cause Analysis
The Windows error string `El nombre del archivo o la extensión es demasiado largo` maps directly to Windows system error code **206 (0xCE: `ERROR_FILENAME_EXCED_RANGE`)**.
Investigation revealed that:
1. Core Tools includes the Python 3.14 worker directory (`workers/python/3.14/WINDOWS/X64`).
2. When the Functions WebHost launches `python.exe` as a child gRPC worker process, Windows dynamic linker `LoadLibraryExW` fails to load `cygrpc.cp314-win_amd64.pyd` within the host-configured process context due to path length limitations in Windows dynamic library dependency resolution.
3. System-wide path shortening or Windows registry edits (`LongPathsEnabled`) require administrative elevation which is prohibited.
4. **Classification**: `WINDOWS_CORE_TOOLS_E2E = BLOCKED` due to an environmental Windows DLL loading limitation.

---

## 4. Path B — Official Linux Container Isolation (`PASS`)

### 4.1 Architecture & Container Build
To achieve deterministic execution without Windows host environment issues, the runtime was packaged into `functions/aegisbank-events/Dockerfile` based on Microsoft's official `mcr.microsoft.com/azure-functions/python:4-python3.14`.

Key enhancements implemented in `v0.13.1`:
1. **Dependency Packaging**: Included `opentelemetry-api`, `opentelemetry-sdk`, `pydantic`, `sqlalchemy`, and `azure-servicebus` in the container site-packages.
2. **Contract Schema Bundling**: Copied `contracts/` into `/home/site/wwwroot/contracts` and added multi-location resolution in `cloud_event.py` (`_resolve_contracts_dir`) so schemas are found both locally and in containerized environments.
3. **Pre-Seeded Secrets Storage**: Pre-seeded `/home/site/secrets/host.json` adhering to the exact `ScriptSecretSerializerV1` JSON schema required by `FileSystemSecretsRepository`:
   ```json
   {
     "masterKey": {
       "name": "master",
       "value": "aegisbank-local-master-key",
       "encrypted": false
     },
     "functionKeys": [
       {"name": "default", "value": "aegisbank-local-function-key", "encrypted": false}
     ],
     "systemKeys": [
       {"name": "eventgridextensionconfig_extension", "value": "aegisbank-local-eventgrid-key", "encrypted": false}
     ]
   }
   ```
4. **CloudEvent SDK Compatibility**: Resolved worker-bundled `azure.functions.CloudEvent` representation where `.to_dict()` is absent by extracting standard RFC properties (`id`, `source`, `type`, `specversion`, `time`, `get_json()`, `extension_attrs`).
5. **UTC ISO 8601 Timestamps**: Aligned sample events to RFC 3339 UTC format (`2026-09-01T22:56:00Z`) required by the Python worker's `try_parse_datetime_with_formats`.

### 4.2 Live Acceptance Execution Evidence
Running `python scripts/functions_runtime_acceptance.py`:

```
=== AegisBank AI Platform v0.13.1 Azure Functions Acceptance ===
[1/5] Ensuring runtime container is active...
[2/5] Waiting for Azure Functions Host readiness...
       Host ID: ea6aa762b4bb-2137340777, Version: 4.1053.200.3, State: Running
[3/5] Testing Event Grid SubscriptionValidation handshake...
       Handshake verified: HTTP 200 OK
[4/5] Delivering canonical CloudEvent (Initial Dispatch)...
       Initial event accepted: HTTP 202 (133.14 ms)
[5/5] Replaying duplicate CloudEvent (Idempotency Guard)...
       Duplicate replay accepted idempotently: HTTP 202 (26.76 ms)

Evidence written to: reports/azure_functions_runtime_evidence.json

--- CLASSIFICATION RESULT ---
WINDOWS_CORE_TOOLS_E2E=BLOCKED
LOCAL_FUNCTIONS_RUNTIME_E2E=PASS
AEGISBANK_V0.13_FUNCTIONS_RUNTIME_E2E_READY
```

### 4.3 Container Host & Worker Logs Evidence
From container stdout (`docker logs aeg-func-live`):
```json
info: Function.service_request_created[1]
      Executing 'Functions.service_request_created' (Reason='EventGrid trigger fired at 2026-09-04T16:13:13.3587467+00:00', Id=658e49bf-a875-4df3-929a-c78119c85098)
info: Function.service_request_created.User[0]
      {"timestamp": "2026-09-04T16:13:13.413967+00:00", "level": "INFO", "logger": "aegisbank.agent", "event_name": "service_request_created_event_processed", "correlation_id": "CORR-V013-LOCAL-001", "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736", "span_id": "7fe37d6def488841", "session_id": "azure-functions-local", "customer_id": "CUST-0001", "tool_name": null, "approval_status": null, "execution_status": "SUCCESS", "latency_ms": null, "error_code": null, "details": {"event_id": "EVT-SR-000123", "event_type": "com.aegisbank.service-request.created.v1", "service_request_id": "SR-000123", "category": "GENERAL", "status": "OPEN"}}
info: Function.service_request_created[2]
      Executed 'Functions.service_request_created' (Succeeded, Id=658e49bf-a875-4df3-929a-c78119c85098, Duration=75ms)
```

Duplicate Replay Log:
```json
info: Function.service_request_created.User[0]
      {"timestamp": "2026-09-04T16:13:27.532672+00:00", "level": "INFO", "logger": "aegisbank.agent", "event_name": "event_grid_duplicate", "correlation_id": "CORR-V013-LOCAL-001", "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736", "span_id": "2baa128898abb648", "session_id": "azure-functions-local", "customer_id": "CUST-0001", "tool_name": null, "approval_status": null, "execution_status": "DUPLICATE", "latency_ms": null, "error_code": null, "details": {"event_id": "EVT-SR-000123", "event_type": "com.aegisbank.service-request.created.v1"}}
info: Function.service_request_created[2]
      Executed 'Functions.service_request_created' (Succeeded, Id=e35b86ab-24ae-43f4-92a5-594eb328d4ed, Duration=7ms)
```

---

## 5. Automated Regression Test Suite

Created `ai/agent/tests/infra/serverless/test_functions_runtime_e2e.py`:
- Marked with `@pytest.mark.infra`.
- Validates host status (`/admin/host/status`), Event Grid handshake, and CloudEvent idempotency.
- Automatically skips when container is inactive, preserving zero-overhead execution for unit/contract fast gates.

Execution result:
```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
collected 3 items

ai\agent\tests\infra\serverless\test_functions_runtime_e2e.py::test_live_functions_host_status_is_running PASSED [ 33%]
ai\agent\tests\infra\serverless\test_functions_runtime_e2e.py::test_live_event_grid_subscription_handshake PASSED [ 66%]
ai\agent\tests\infra\serverless\test_functions_runtime_e2e.py::test_live_event_grid_cloudevent_execution_and_idempotency PASSED [100%]

============================== 3 passed in 0.43s ==============================
```

---

## 6. Classification & Sign-Off

| Gate / Classification | Status | Evidence Summary |
|---|---|---|
| `WINDOWS_CORE_TOOLS_E2E` | **BLOCKED** | Environmental Windows DLL loader limitation (`ERROR_FILENAME_EXCED_RANGE` on cygrpc). |
| `LOCAL_FUNCTIONS_RUNTIME_E2E` | **PASS** | Live Microsoft Host + Python 3.14 container verified (200 host, 200 handshake, 202 event, 202 replay). |
| `QUALITY_GATE_FAST` | **PASS** | Zero impact on `src/`, all existing unit/contract gates clean. |

**Final Completion Token:**
`AEGISBANK_V0.13_FUNCTIONS_RUNTIME_E2E_READY`
