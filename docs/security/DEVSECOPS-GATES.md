# DevSecOps Gates

**DevSecOps (Development + Security + Operations)** integrates security into every
development stage. **Shift-left security** means finding defects earlier in the
**SDLC (Software Development Life Cycle)**, when remediation is cheaper and safer.

| Gate | Tool/check | Failure meaning | Status model |
|---|---|---|---|
| Lint/format | Ruff | code quality or import defect | executed locally/CI |
| Tests/contracts/E2E | pytest | behavior or compatibility defect | executed locally/CI |
| SAST | Bandit | AST pattern needs review | true positive, false positive, or accepted risk must be recorded |
| SCA | pip-audit | known dependency advisory | blocked is not PASS |
| SBOM | pip-audit CycloneDX JSON | dependency inventory | generated artifact |
| Secrets | tracked-file scanner | credential exposure risk | must fail on a match |
| Audit evidence | machine-readable reports | cannot reconstruct the gate | required for release review |

The initial Bandit baseline records only low-severity findings: an assertion in an MCP
boundary, a deliberately best-effort HOTL subscriber, non-cryptographic retry jitter,
fixed subprocess calls for the local Foundry CLI, and regex strings mistaken for
passwords. These are reviewed as false positives or accepted laboratory risks. The gate
fails on medium/high findings and the complete JSON report remains an artifact. No
finding is silently discarded.

**SAST (Static Application Security Testing)** scans source without running it. **SCA
(Software Composition Analysis)** inspects dependencies written by others. **SBOM
(Software Bill of Materials, lista de materiales de software)** inventories components;
it is not itself a vulnerability scan. These controls support Mibanco secure delivery
work and AI-103/AI-200 safeguards, but `LAB-COVERED` is not a banking certification.
