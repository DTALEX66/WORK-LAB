"""NF-01 rule semantic: what may legally transfer vs. what stays forbidden.

Clarifies the broad root-rule phrasing ("inside the project Git root" and
"no prompt/response bodies") WITHOUT weakening the data boundary:

  * A *user-published business artifact* (audit / task document the user
    explicitly selected to ship, or an immutable task-package / receipt
    reference) may flow to an authorized target material space.
  * *Private session libraries, native conversation logs, telemetry bodies
    and credentials* are NEVER auto-mirrored.  Telemetry keeps only
    references + minimal metadata.
  * A project's *temporary* offline / model preference is scoped to that
    project (or a task) and never becomes a global forcing on another
    project.

Pure and deterministic: no filesystem, no network, no native private store
is read.  Every decision carries its reason so callers fail-closed on the
sensitive path while non-sensitive work keeps moving.  Unknown artifact
kinds are never silently allowed.
"""
from __future__ import annotations

import re
from typing import Any

# Business artifact classes that MAY transfer when the user authorized the batch.
ALLOWED_ARTIFACT_KINDS = frozenset({
    "user_published_audit",
    "user_published_task",
    "immutable_task_package_ref",
    "receipt_ref",
})

# Classes that are NEVER auto-mirrored, even when an `authorized` flag is set.
FORBIDDEN_ARTIFACT_KINDS = frozenset({
    "private_session",
    "conversation_log",
    "telemetry_body",
    "credential",
    "account_key",
    "browser_data",
})

DECISIONS = ("ALLOW", "PENDING_AUTHORIZATION", "ISOLATE", "REJECT")

# Secret-ish key names (checked anywhere in the nested payload, not just top level).
_SECRET_KEY_RE = re.compile(
    r"(api_?key|access_?token|auth_?token|secret|password|passwd|cvc|private_?key|credential|bearer)",
    re.IGNORECASE,
)
# High-entropy / provider token value patterns (so a value buried in a
# "goal" / "next_step" free-text field is still caught, not only the top key).
_SECRET_VALUE_RE = re.compile(
    r"^(Bearer\s+\S+|ghp_\S+|gho_\S+|ghs_\S+|sk-[A-Za-z0-9_-]{20,}"
    r"|AKIA[A-Z0-9]{16}|[A-Za-z0-9+/]{64,}={0,2})$"
)


def _walk_keys(node: Any, path: str = "") -> list[tuple[str, Any]]:
    """Yield (dotted_path, value) for every leaf / nested mapping entry."""
    out: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            dotted = f"{path}.{key}" if path else str(key)
            if isinstance(value, (dict, list)):
                out.extend(_walk_keys(value, dotted))
            else:
                out.append((dotted, value))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            dotted = f"{path}[{idx}]" if path else f"[{idx}]"
            out.extend(_walk_keys(value, dotted))
    return out


def find_nested_secrets(artifact: dict[str, Any]) -> list[str]:
    """Return the dotted paths that carry a secret key or value.

    Matches key names anywhere (top level, nested, list elements, and artifact
    path query params) plus provider-token *values* buried in free-text fields
    such as ``goal`` / ``next_step``.  Only the top key being removed is NOT
    sufficient — a secret hidden one level down is still caught.
    """
    hits: list[str] = []
    for path, value in _walk_keys(artifact):
        if _SECRET_KEY_RE.search(path):
            hits.append(path)
            continue
        if isinstance(value, str) and _SECRET_VALUE_RE.match(value.strip()):
            hits.append(path)
    return sorted(hits)


def classify_flow(artifact: dict[str, Any], *, authorized: bool) -> dict[str, Any]:
    """Decide whether one artifact may flow to an authorized material space.

    Fail-closed order: forbidden class -> REJECT; unknown class or missing
    authorization -> PENDING_AUTHORIZATION; authorized business artifact that
    still carries a nested secret -> ISOLATE (quarantined, secret not leaked);
    otherwise -> ALLOW.
    """
    kind = artifact.get("artifact_kind")
    result: dict[str, Any] = {
        "artifact_kind": kind,
        "authorized": authorized,
        "decision": None,
        "reasons": [],
    }
    if kind in FORBIDDEN_ARTIFACT_KINDS:
        result["decision"] = "REJECT"
        result["reasons"].append(
            f"{kind} is a forbidden auto-transfer class (private session library / "
            "telemetry body / credential); it never flows, even with an authorized flag"
        )
        return result
    if kind not in ALLOWED_ARTIFACT_KINDS:
        result["decision"] = "PENDING_AUTHORIZATION"
        result["reasons"].append(
            f"unknown artifact kind {kind!r}; not on the allowlist, so it is not "
            "auto-transferred"
        )
        return result
    if not authorized:
        result["decision"] = "PENDING_AUTHORIZATION"
        result["reasons"].append(
            "the user has not selected / authorized this batch for external transfer"
        )
        return result
    leaked = find_nested_secrets(artifact)
    if leaked:
        result["decision"] = "ISOLATE"
        result["reasons"].append(
            "authorized business artifact still carries nested secret(s): "
            + ", ".join(leaked)
        )
        result["leaked_keys"] = leaked
        return result
    result["decision"] = "ALLOW"
    result["reasons"].append("authorized business artifact, desensitized")
    return result


def is_project_scoped(pref: dict[str, Any]) -> bool:
    """A project-local temporary offline / model preference is scoped, not global."""
    return pref.get("scope") in ("project", "task") and not pref.get("global", False)


def effective_for_project(pref: dict[str, Any], target_project: str) -> dict[str, Any]:
    """The preference fields that actually apply to ``target_project``.

    A project/task-scoped preference applies ONLY to its own project; it is
    never carried to another project.  A deliberate global preference
    (``global=True``) is the one case that applies project-wide, and only that
    case is propagated — so a project A temporary offline setting cannot force
    project B's model behavior.
    """
    if is_project_scoped(pref) and pref.get("project_id") != target_project:
        return {}  # scoped to another project: zero fields reach the target
    if pref.get("global") or pref.get("project_id") == target_project:
        return dict(pref)
    return {}


def does_project_pref_leak(a_pref: dict[str, Any], target_project: str) -> bool:
    """True when a project A temporary preference would wrongly force project B.

    ``target_project`` is B.  A project/task-scoped A preference produces no
    fields for B (no leak).  It leaks only if it was deliberately marked
    global, which is a separate authorization — reported here so the caller
    can hold it, never auto-applied.
    """
    return bool(effective_for_project(a_pref, target_project)) and not is_project_scoped(a_pref)


def decide(artifact: dict[str, Any], *, authorized: bool) -> dict[str, Any]:
    """Stable public alias for :func:`classify_flow` (one call, one decision)."""
    return classify_flow(artifact, authorized=authorized)
