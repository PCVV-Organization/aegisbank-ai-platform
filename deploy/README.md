# Deployment Artifacts

Deployment files describe reproducible local or laboratory configuration. Their presence does not prove that a service was deployed or accepted.

## Areas

- `local/` — local development and container configuration
- [Kubernetes](kubernetes/README.md) — laboratory manifests

## Promotion boundary

Follow the approved order: local, Docker, CI, then cloud only after explicit approval. Do not infer permission to run `kubectl apply`, provision Azure resources, or deploy from these documents. Verify current evidence in the [project README](../README.md) and [maturity matrix](../docs/requirements/V1.0-MATURITY-MATRIX.md).
