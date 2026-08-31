# ADR-024: CI/CD Pipeline and DevSecOps Shift-Left Gates

## Context

Enterprise banking AI systems require automated verification of functional quality, performance, and security across the entire Software Development Life Cycle (SDLC). Without an automated CI/CD pipeline and DevSecOps security scanning, vulnerabilities in dependencies or improper code patterns can reach production unnoticed.

## Decision

1. **GitHub Actions CI Configuration:** Define `.github/workflows/ci.yml` to automate checkout, Python setup, linting (Ruff), code formatting check, bytecode compilation, full test execution (Unit, Integration, Contract, E2E), code coverage, SAST (Bandit), SCA (pip-audit), CycloneDX SBOM generation, and secret scanning.
2. **Strict Status Designation:** Mark local workflow configuration as `CI-CONFIGURED / RUNNER-PENDING` until remote execution on a GitHub Actions runner provides verifiable execution logs.
3. **Shift-Left DevSecOps Scanning:**
   - **SAST (Static Application Security Testing):** Bandit runs on all source code packages (`ai/agent/src`, `ai/rag/src`, `ml/intent-classifier/src`, `services/mock-core-banking/src`). Findings are formally classified as True Positive, False Positive, or Accepted Risk.
   - **SCA (Software Composition Analysis):** `pip-audit` checks installed packages against OSV / PyPI vulnerability databases.
   - **SBOM (Software Bill of Materials):** Generate CycloneDX JSON inventory (`docs/security/sbom.json`).
   - **Secret Scanning:** Reject code containing API tokens, private keys, passwords, or committed `.env` files.

## Consequences

### Positive
- Security and quality issues are caught at the earliest possible stage in development (*Shift-Left*).
- Complete software bill of materials and vulnerability posture available on every commit.
- Aligns directly with Microsoft AI-103/AI-200 security and Mibanco 2026 DevSecOps requirements.

### Negative / Trade-offs
- Network access is required for live SCA vulnerability database queries; if network is unavailable, dependency audit must be explicitly marked `DEPENDENCY_AUDIT_BLOCKED`.
