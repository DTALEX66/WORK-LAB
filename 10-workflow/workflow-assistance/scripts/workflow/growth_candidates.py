#!/usr/bin/env python3
"""Fail-closed lifecycle operations for local growth-candidate contracts."""

from __future__ import annotations

import copy
import re
from typing import Any

SCHEMA_VERSION = "workflow/growth-candidate/v1"
CLASSIFICATIONS = {"curator", "learn", "manual", "hub", "upstream", "deployment"}
RISKS = {"low", "medium", "high", "critical"}
STATES = {"discovered", "isolated", "scanned", "evaluated", "candidate", "approved", "blocked", "retired"}
REQUIRED = {"schema_version", "candidateId", "origin", "classification", "status", "risk"}
ALLOWED = REQUIRED | {"sourceDigest"}
TRANSITIONS = {
    "discovered": {"isolated", "blocked"},
    "isolated": {"scanned", "blocked"},
    "scanned": {"evaluated", "blocked"},
    "evaluated": {"candidate", "blocked"},
    "candidate": {"approved", "blocked"},
    "approved": {"retired"},
    "blocked": set(),
    "retired": set(),
}
DIGEST = re.compile(r"^[a-f0-9]{64}$")


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("candidate must be an object")
    unexpected = set(candidate) - ALLOWED
    if unexpected:
        raise ValueError(f"additional candidate properties: {sorted(unexpected)}")
    missing = REQUIRED - set(candidate)
    if missing:
        raise ValueError(f"candidate missing required properties: {sorted(missing)}")
    if candidate["schema_version"] != SCHEMA_VERSION:
        raise ValueError("candidate schema version mismatch")
    for key in ("candidateId", "origin"):
        if not isinstance(candidate[key], str) or not candidate[key]:
            raise ValueError(f"candidate {key} must be non-empty")
    if candidate["classification"] not in CLASSIFICATIONS:
        raise ValueError("invalid candidate classification")
    if candidate["status"] not in STATES:
        raise ValueError("invalid candidate status")
    if candidate["risk"] not in RISKS:
        raise ValueError("invalid candidate risk")
    if "sourceDigest" in candidate and not isinstance(candidate["sourceDigest"], str):
        raise ValueError("candidate digest must be a string")
    if "sourceDigest" in candidate and not DIGEST.fullmatch(candidate["sourceDigest"]):
        raise ValueError("candidate digest must be 64 lowercase hexadecimal characters")
    return candidate


def discover(candidate_id: str, origin: str, classification: str, risk: str) -> dict[str, Any]:
    candidate = {
        "schema_version": SCHEMA_VERSION,
        "candidateId": candidate_id,
        "origin": origin,
        "classification": classification,
        "status": "discovered",
        "risk": risk,
    }
    return validate_candidate(candidate)


def transition(candidate: dict[str, Any], target: str, *, source_digest: str | None = None) -> dict[str, Any]:
    validate_candidate(candidate)
    current = candidate["status"]
    if target not in STATES or target not in TRANSITIONS[current]:
        raise ValueError(f"invalid candidate transition {current} -> {target}")
    updated = copy.deepcopy(candidate)
    if target != "blocked" and "sourceDigest" not in updated:
        if source_digest is None or not DIGEST.fullmatch(source_digest):
            raise ValueError("source digest is required before lifecycle promotion")
        updated["sourceDigest"] = source_digest
    updated["status"] = target
    return validate_candidate(updated)


def promote(candidate: dict[str, Any], *, approval: bool = False) -> dict[str, Any]:
    if not approval:
        raise ValueError("explicit approval is required before promotion")
    return transition(candidate, "approved")


def quarantine(candidate: dict[str, Any]) -> dict[str, Any]:
    return transition(candidate, "blocked")


def rollback(candidate: dict[str, Any]) -> dict[str, Any]:
    return transition(candidate, "retired")
