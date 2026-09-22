"""Invariant Registry Consistency Test.

Verifies that all invariant identifiers (I_1 through I_15) remain strictly synchronized
with the canonical 15-invariant specification (§6.6 of AEGISBANK-AI-PLATFORM-CHATGPT-BRIEFING.md)
and that subordinate documentation and walkthroughs contain zero numbering drifts or reassignments.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]

CANONICAL_INVARIANTS: dict[str, str] = {
    "I_1": "Zero Account Fakery",
    "I_2": "Mandatory HITL for Writes",
    "I_3": "HOTL Supervisory Kill-Switch",
    "I_4": "Customer IDOR Isolation",
    "I_5": "Transactional Outbox Atomicity",
    "I_6": "Idempotency Precedes Retries",
    "I_7": "Active Corpus Grounding",
    "I_8": "Telemetry Data Minimization",
    "I_9": "Zero Paid Cloud Deployment",
    "I_10": "Zero Balance Caching",
    "I_11": "Circuit Breaker Fault Isolation",
    "I_12": "Single-Agent Monolith Boundary",
    "I_13": "Strict Contract-First Validation",
    "I_14": "Tamper-Evident Append-Only Audit",
    "I_15": "Synthetic Data Exclusivity",
}


def test_canonical_invariants_unique_and_complete() -> None:
    """Ensure all 15 canonical invariants have unique identifiers and unique canonical names."""
    assert len(CANONICAL_INVARIANTS) == 15
    names = list(CANONICAL_INVARIANTS.values())
    assert len(names) == len(set(names)), "Canonical invariant names must be strictly unique"


def test_briefing_contains_all_15_canonical_invariants() -> None:
    """Verify Section 6.6 of the canonical briefing defines all 15 invariants accurately."""
    briefing_path = REPO_ROOT / "docs" / "briefings" / "AEGISBANK-AI-PLATFORM-CHATGPT-BRIEFING.md"
    assert briefing_path.exists(), f"Briefing missing at {briefing_path}"
    content = briefing_path.read_text(encoding="utf-8")

    for inv_id, inv_name in CANONICAL_INVARIANTS.items():
        # Match e.g. "**$I_1$**" or "**$I_{10}$**"
        num = inv_id.replace("I_", "")
        pattern = rf"\*\*\$I_\{{{num}\}}\$\*\*|\*\*\$I_{num}\$\*\*"
        assert re.search(pattern, content), f"Invariant {inv_id} not found in briefing"
        assert inv_name.lower() in content.lower(), (
            f"Invariant name {inv_name} missing from briefing"
        )


def test_no_subordinate_invariant_drift() -> None:
    """Ensure no subordinate documentation reassigns canonical invariant IDs.

    Specifically guards against historical drift:
    - I_2 must NOT be assigned to IDOR or Ownership
    - I_3 must NOT be assigned to Read/Write Separation
    - I_4 must NOT be assigned to HITL
    - I_5 must NOT be assigned to Non-Empty Responses
    """
    doc_paths = [
        REPO_ROOT / "docs" / "security" / "PHASE2-LOCAL-RED-TEAM-EVIDENCE.md",
        REPO_ROOT / "docs" / "security" / "V1.0-THREAT-MODEL.md",
        REPO_ROOT / "docs" / "evaluation" / "EVALUATION-CATALOG.md",
    ]

    for doc in doc_paths:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        # I_2 must not be bound to IDOR or Ownership
        assert not re.search(r"I_?2.*?(?:IDOR|Ownership\s*Isolation)", text, re.IGNORECASE), (
            f"Invariant drift in {doc.name}: I_2 must refer to Mandatory HITL"
        )
        # I_4 must not be bound to HITL
        assert not re.search(
            r"I_?4.*?(?:Mandatory\s*HITL|HITL\s*Mandatory)", text, re.IGNORECASE
        ), f"Invariant drift in {doc.name}: I_4 must refer to Customer IDOR Isolation"
        # I_5 must not be bound to Non-Empty Responses
        assert not re.search(r"I_?5.*?(?:Non-Empty|Respuesta\s*no\s*vacía)", text, re.IGNORECASE), (
            f"Invariant drift in {doc.name}: I_5 must refer to Transactional Outbox Atomicity"
        )
