"""ArcheAxis thin contracts — WORK-LAB V2 three-project boundary seam.

These are the MINIMAL interfaces WORK-LAB keeps across the boundary.
They carry no knowledge truth, no memory store, no promotion decision —
only the "candidate + guard verdict" shape that crosses into
DTALEX66/ArcheAxis-Knowledge-OS, and the thin query surface that asks
ArcheAxis instead of storing locally.

Authority: .project/governance/three-project-boundary.json
Verifier: scripts/ci/verify_three_project_boundary.py

P2/P3 rule: no new caller may import services/memory or services/knowledge
as a local backend. New cross-project access goes through THIS module.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Knowledge side (services/knowledge -> ArcheAxis)
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeCandidate:
    """The ONLY thing WORK-LAB may emit toward ArcheAxis knowledge truth.

    WORK-LAB never emits 'Knowledge Truth' — it emits a candidate plus the
    guard's verdict. ArcheAxis makes the acceptance/classification/status
    decision. Keeping this dataclass here (not in services/knowledge) is
    what stops a second knowledge-truth owner from appearing in WORK-LAB.
    """
    source_id: str
    category: str                 # ch 37 whitelist label (candidate-level)
    evidence_level: str
    guard_verdict: str            # "allow" | "reject"
    guard_reasons: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)
    payload_digest: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)


class GuardVerdict:
    ALLOW = "allow"
    REJECT = "reject"


# ---------------------------------------------------------------------------
# Memory side (services/memory -> ArcheAxis)
# ---------------------------------------------------------------------------

@dataclass
class MemoryQuery:
    """Thin query surface — WORK-LAB asks ArcheAxis, it does NOT store."""
    query: str
    session_id: Optional[str] = None
    scope: str = "session"

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)


__all__ = [
    "KnowledgeCandidate", "GuardVerdict", "MemoryQuery",
]
