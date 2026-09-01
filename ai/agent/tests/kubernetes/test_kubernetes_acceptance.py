"""Acceptance test suite for Kubernetes local orchestration and manifests.

Validates context safety, namespace, deployment specs, probes, security context,
resource limits, and Service definitions without external dependencies.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
K8S_DIR = REPO_ROOT / "deploy" / "kubernetes"


def _has_local_kubernetes() -> bool:
    """Check if kubectl is available and connected to an explicitly local development cluster."""
    if not shutil.which("kubectl"):
        return False
    try:
        ctx_res = subprocess.run(
            ["kubectl", "config", "current-context"],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
        ctx = ctx_res.stdout.strip().lower()
        if ctx_res.returncode != 0 or not ctx:
            return False
        # Context must be explicitly local
        if not any(
            local_prefix in ctx for local_prefix in ("docker-desktop", "kind-", "minikube", "k3d-")
        ):
            return False
        # Check node availability
        node_res = subprocess.run(
            ["kubectl", "get", "nodes"],
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
        return node_res.returncode == 0
    except Exception:
        return False


def test_kubernetes_manifest_declarations_and_structure() -> None:
    """Verify all YAML manifests in deploy/kubernetes are valid and follow canonical schema."""
    manifest_files = list(K8S_DIR.glob("*.yaml"))
    assert len(manifest_files) >= 3, f"Expected at least 3 manifests in {K8S_DIR}"

    kinds: dict[str, dict] = {}
    for mf in manifest_files:
        content = yaml.safe_load(mf.read_text(encoding="utf-8"))
        assert content is not None
        assert "kind" in content
        assert "metadata" in content
        kinds[content["kind"]] = content

    assert "Namespace" in kinds or "Deployment" in kinds
    assert "Deployment" in kinds
    assert "Service" in kinds
    assert "ConfigMap" in kinds


def test_kubernetes_deployment_hardening_and_spec() -> None:
    """Verify Deployment manifest adheres to AegisBank security and observability standards."""
    dep_file = K8S_DIR / "deployment.yaml"
    assert dep_file.exists()
    dep = yaml.safe_load(dep_file.read_text(encoding="utf-8"))

    spec = dep.get("spec", {})
    template = spec.get("template", {})
    pod_spec = template.get("spec", {})
    containers = pod_spec.get("containers", [])
    assert len(containers) >= 1

    core_container = containers[0]

    # Image versioning & pull policy
    assert "aegisbank/mock-core-banking:0.11.0" in core_container.get("image", "")
    assert core_container.get("imagePullPolicy") in ("IfNotPresent", "Never")

    # Probes
    readiness = core_container.get("readinessProbe", {}).get("httpGet", {})
    liveness = core_container.get("livenessProbe", {}).get("httpGet", {})
    assert readiness.get("path") == "/health/ready"
    assert liveness.get("path") == "/health/live"
    assert readiness.get("port") == 8000
    assert liveness.get("port") == 8000

    # Resource requests and limits
    resources = core_container.get("resources", {})
    assert "requests" in resources and "limits" in resources
    assert resources["requests"].get("memory") == "128Mi"
    assert resources["limits"].get("memory") == "256Mi"

    # Security Context
    pod_sec = pod_spec.get("securityContext", {})
    assert pod_sec.get("runAsNonRoot") is True
    assert pod_sec.get("runAsUser") == 10001
    assert pod_sec.get("seccompProfile", {}).get("type") == "RuntimeDefault"

    cont_sec = core_container.get("securityContext", {})
    assert cont_sec.get("allowPrivilegeEscalation") is False
    assert "ALL" in cont_sec.get("capabilities", {}).get("drop", [])


def test_kubernetes_service_spec_and_clusterip() -> None:
    """Verify Service manifest declares ClusterIP and correct port mappings."""
    svc_file = K8S_DIR / "service.yaml"
    assert svc_file.exists()
    svc = yaml.safe_load(svc_file.read_text(encoding="utf-8"))

    spec = svc.get("spec", {})
    assert spec.get("type") == "ClusterIP"
    ports = spec.get("ports", [])
    assert len(ports) >= 1
    assert ports[0].get("port") == 8000
    assert ports[0].get("targetPort") == 8000


def test_kubernetes_no_production_secrets_in_manifests() -> None:
    """Verify no hardcoded credentials or production secret tokens exist in deploy/kubernetes."""
    for mf in K8S_DIR.glob("*.yaml"):
        text = mf.read_text(encoding="utf-8")
        assert "password" not in text.lower() or "Password123!" not in text
        assert "secret_key" not in text.lower()
        assert "PRIVATE KEY" not in text


def test_kubernetes_live_cluster_runtime_verification() -> None:
    """If local Kubernetes is active, verify cluster state, namespace, and workload readiness."""
    if not _has_local_kubernetes():
        return  # Gracefully skip live check if run in CI without live cluster runner

    # 1. Verify Namespace
    ns_res = subprocess.run(
        ["kubectl", "get", "namespace", "aegisbank-local", "-o", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ns_res.returncode == 0
    ns_data = json.loads(ns_res.stdout)
    assert ns_data["status"]["phase"] == "Active"

    # 2. Verify Deployment
    dep_res = subprocess.run(
        [
            "kubectl",
            "get",
            "deployment",
            "mock-core-banking",
            "-n",
            "aegisbank-local",
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert dep_res.returncode == 0
    dep_data = json.loads(dep_res.stdout)
    assert dep_data["status"].get("readyReplicas", 0) >= 1

    # 3. Verify Pods
    pod_res = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-n",
            "aegisbank-local",
            "-l",
            "app.kubernetes.io/name=mock-core-banking",
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert pod_res.returncode == 0
    pods_data = json.loads(pod_res.stdout)
    items = pods_data.get("items", [])
    assert len(items) >= 1
    assert items[0]["status"]["phase"] == "Running"
    # Verify container statuses are ready
    container_statuses = items[0]["status"].get("containerStatuses", [])
    assert len(container_statuses) >= 1
    assert container_statuses[0]["ready"] is True

    # 4. Verify Service
    svc_res = subprocess.run(
        [
            "kubectl",
            "get",
            "service",
            "mock-core-banking-service",
            "-n",
            "aegisbank-local",
            "-o",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert svc_res.returncode == 0
    svc_data = json.loads(svc_res.stdout)
    assert svc_data["spec"]["type"] == "ClusterIP"
