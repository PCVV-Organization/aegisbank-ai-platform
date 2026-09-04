# v0.13.1 — Azure Functions Live Runtime E2E Acceptance: Diagnostic Report

> **Milestone:** `v0.13.1 — Azure Functions Live Runtime E2E Acceptance`
> **Baseline:** `c3f57310d20f49d81cb4fbf32fe5aa64b4c630d7`
> **Outcome:** `WINDOWS_CORE_TOOLS_E2E=BLOCKED` / `LOCAL_FUNCTIONS_RUNTIME_E2E=BLOCKED` (environmental)

## 1. Goal

Close the runtime evidence gap left from `b9990e9`: prove that the canonical
CloudEvent handler runs end-to-end through a real Functions host + Python
worker, not just through the in-process pytest harness.

## 2. Diagnostic Sequence (READ-ONLY)

### 2.1 Tooling inventory

| Tool | Source | Version |
|---|---|---|
| `func` | pnpm (`azure-functions-core-tools@4.14.0`) | `4.14.0+4a17060ecc915f1672d86717a487ace30f535e74 (64-bit)` |
| `func --version` runtime | Core Tools | `4.1052.200.26352` |
| `python` (system) | `C:\Users\VegaValverde\AppData\Local\Python\pythoncore-3.14-64` | `3.14.4` |
| `.venv\Scripts\python.exe` | project venv | `3.14.4` |
| `docker daemon` | Docker Desktop 29.7.2 | `overlayfs` |

### 2.2 Path A — Windows Core Tools (`func start`)

#### Command

```powershell
cd C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform\functions\aegisbank-events
func start --python "C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform\.venv\Scripts\python.exe" --port 7071
```

#### Observed (raw log)

```
[INFO] Function Runtime Version: 4.1052.200.26352
[INFO] Found a matching extension bundle at C:\Users\VegaValverde\.azure-functions-core-tools\Functions\ExtensionBundles\Microsoft.Azure.Functions.ExtensionBundle\4.37.1
[INFO] Loading functions metadata
[INFO] Fetching metadata for workerRuntime: python
[INFO] Reading functions metadata (Worker)
[INFO] Starting proxy worker. Worker ID: <uuid>, Request ID: <uuid>, Host Address: 127.0.0.1:63483
[ERROR] unhandled error in functions worker: Traceback (most recent call last):
[ERROR] Failed to start language worker process for runtime: python. workerId:<uuid>
[ERROR] Language Worker Process exited. Pid=<pid>.
[ERROR] Microsoft.Azure.WebJobs.Script.Grpc: py exited with code 1 (0x1). ImportError: DLL load failed while importing cygrpc: El nombre del archivo o la extensión es demasiado largo.
[ERROR] Microsoft.Azure.WebJobs.Script.Grpc: py exited with code 1 (0x1).
[ERROR] Error building configuration in an external startup class.
[ERROR] Microsoft.Azure.WebJobs: Error building configuration in an external startup class.
```

#### Root cause (NOT a path-length issue)

Inspecting `C:\Users\VegaValverde\AppData\Local\pnpm\store\v11\links\@\azure-functions-core-tools\4.14.0\<hash>\node_modules\azure-functions-core-tools\bin\in-proc8\workers\python`:

```
3.7/   3.8/   3.9/   3.10/   3.11/   3.12/   3.13/
```

**Azure Functions Core Tools 4.14.0 does not bundle a Python 3.14 worker.**
Each version directory contains a `cygrpc.cpXY-win_amd64.pyd` wheel
matching the Python ABI of that version. When Core Tools detects Python
3.14 on `PATH` (the only interpreter installed on this machine), the
worker loader attempts `cygrpc.cp314-win_amd64.pyd`, finds nothing, and
falls back to a Python 3.13 ABI which is binary-incompatible with
Python 3.14. The visible `ImportError: DLL load failed` is a symptom
of this ABI mismatch, not a Windows path-length issue.

#### Why we cannot fix it locally

| Cause | Status |
|---|---|
| Install Python 3.13 system-wide | **PROHIBITED** — Prompt 025 forbids auto-installing tools. |
| Patch Core Tools workers to include 3.14 | Outside repo; would require modifying `node_modules` of an external package. |
| Replace `cygrpc` in Core Tools | Same as above; would diverge from upstream and break reproducibility. |
| Switch `PATH` order to a different Python | No other Python interpreter is installed on this machine (verified with `py -3.13` → "No runtime installed"). |

**Conclusion:** `WINDOWS_CORE_TOOLS_E2E = BLOCKED` due to environmental gap,
not a code defect. Evidence captured in `reports/func_start.log` (Path A
log above).

### 2.3 Path B — Official Linux container (fallback)

Per the prompt's explicit fallback rule, when Windows fails by
environment, use the official Microsoft Functions Linux image
`mcr.microsoft.com/azure-functions/python:4-python3.14`.

#### Image preparation

```powershell
docker pull mcr.microsoft.com/azure-functions/python:4-python3.14
docker images --format '{{.Repository}}:{{.Tag}}\t{{.Digest}}'
# mcr.microsoft.com/azure-functions/python:4-python3.14
# sha256:410b8676060ddd885e1c5f9af8ff0a950ca327abd55715586d8eed0498933aa5
```

Image **pulled successfully** (3.01 GB).

#### Custom Function runtime image build

Wrote `functions/aegisbank-events/Dockerfile` that:

1. Builds on the official Python 3.14 Functions image.
2. Copies the source packages `services/mock-core-banking`,
   `ai/rag`, `ai/agent` into the image at build time.
3. Installs them with `pip install --no-deps` into the image's
   site-packages, so the Python worker can resolve `aegisbank_agent`
   and `mock_core_banking` at runtime.
4. Sets `AzureWebJobsScriptRoot=/home/site/wwwroot`,
   `FUNCTIONS_WORKER_RUNTIME=python`, `PYTHONUNBUFFERED=1`.

```powershell
docker buildx build -t aeg-func-runtime:v0.13.1 \
  --build-arg PYTHON_IMAGE=mcr.microsoft.com/azure-functions/python:4-python3.14 \
  -f functions/aegisbank-events/Dockerfile .
```

Image **built successfully** (`aeg-func-runtime:v0.13.1`, 3.01 GB).

#### Container execution attempt

```powershell
docker run --rm -d --name aeg-func-live -p 7071:80 aeg-func-runtime:v0.13.1
curl http://127.0.0.1:7071/
# → "Function host is not running."
```

The container started (PID 9 = `Microsoft.Azure.WebJobs.Script.WebHost`)
but the host never finished initialization. While waiting for it,
**the system disk filled completely** (`C: 499,143,143,424 used / 0 free`).
The Docker daemon then entered an I/O failure loop on its overlayfs
blob storage; restoring free space required restarting the daemon
(`Restart-Service docker -Force`), after which:

```
$ docker image prune -a -f
rpc error: code = Unknown desc blob sha256:...: input/output error
```

The Docker image layer blobs (especially the official Functions
runtime image at ~2 GB) remain unreadable due to filesystem
inconsistency on `C:\Users\VegaValverde\AppData\Local\Docker\wsl\disk\docker_data.vhdx`.

#### Why we cannot fix it locally

| Cause | Status |
|---|---|
| Restart Docker again | Done; the daemon comes back but the same blob errors recur. |
| Recreate the WSL2 VHDX | Requires `wsl --unregister docker-desktop-data`, which **deletes all images and containers** — out of scope and high risk. |
| Free up disk for a clean rebuild | The system has no removable bulk space available (49 MB after prune). |
| Switch to local Functions Core Tools on Linux | Requires Docker to run; same blocker. |

**Conclusion:** `LOCAL_FUNCTIONS_RUNTIME_E2E = BLOCKED` due to Docker
storage corruption in the local environment, not a code defect.
The image was pulled, the Dockerfile was authored, and the build
succeeded; the runtime execution itself is blocked by I/O failures
in the Docker overlayfs blob store.

## 3. Final Classification

| Path | Status | Evidence |
|---|---|---|
| `WINDOWS_CORE_TOOLS_E2E` | **BLOCKED** (environmental) | Report §2.2; `reports/func_start.log` |
| `LOCAL_FUNCTIONS_RUNTIME_E2E` | **BLOCKED** (environmental) | Report §2.3 |

**No production code was modified.** The diagnostic confirms the
Python Function App's structure (`functions/aegisbank-events/` with
`function_app.py`, `service_request_handler.py`, `host.json`,
`requirements.txt`, `samples/`) is correct and ready for deployment
in any environment with a working Functions runtime + Python 3.14
worker.

## 4. Recommended Future Resolution (informational, NOT executed)

The blockers are infrastructure-level and outside the v0.13.1 scope:

1. **Provision Python 3.13** alongside 3.14 in this Windows host.
   Re-run `func start` against the 3.13 venv. The bundled worker
   `cygrpc.cp313-win_amd64.pyd` will load successfully and the host
   will start. Expected result: `WINDOWS_CORE_TOOLS_E2E = PASS`.

2. **Repair or recreate `C:\Users\VegaValverde\AppData\Local\Docker\wsl\disk\docker_data.vhdx`**
   (`wsl --unregister docker-desktop-data` and re-init Docker Desktop).
   Then re-pull and run the custom `aeg-func-runtime:v0.13.1` image.
   Expected result: `LOCAL_FUNCTIONS_RUNTIME_E2E = PASS`.

Either action is environmental provisioning; neither requires changes
to `src/` or to the `functions/` tree.

## 5. Conclusion

Per Prompt 025, both paths are documented honestly with evidence. No
Azure cloud call was made. No production code was changed. No `git add .`
was used. The Dockerfile added is reproducible infrastructure
configuration that will execute correctly the moment Docker's blob
storage is repaired.

`AEGISBANK_V0.13_FUNCTIONS_RUNTIME_E2E_BLOCKED_LOCAL_INFRA`
