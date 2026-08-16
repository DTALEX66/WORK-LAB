"""Stable Prefix and ContextBundle (WL3-330 / MR-10).

Deterministic context bundles: stable vs volatile separation, selector-driven
incremental file reads and diffs, versioned digests with required-field
validation.

Contract rules (taskpack §MR-10 acceptance):
- same input twice => byte-identical stable prefix
- timestamps, temp paths, random ids never pollute the stable prefix
- rule revision change invalidates explicitly
- project switch never hits another project's bundle
- digest missing boundary/acceptance => fail closed
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "workflow/context-bundle/v1"
BOUNDARY_MARKER = "BOUNDARY"
ACCEPTANCE_MARKER = "ACCEPTANCE"

# Volatile patterns that must never enter the stable digest.
_VOLATILE_RE = re.compile(
    r"(?:20\d{2}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
    r"|(?:[0-9a-f]{32})"
    r"|(?:tmp[\\/][A-Za-z0-9_.-]+)"
    r"|(?:__pycache__)"
)


class ContextBundle:
    def __init__(self, project_id: str, rules_revision: str) -> None:
        self.project_id = project_id
        self.rules_revision = rules_revision

    # -- stable digest -------------------------------------------------------
    def stable_digest(self, source_text: str, revision: str | None = None) -> str:
        """Deterministic digest over de-volatilized source text."""
        normalized = self._normalize(source_text)
        effective_revision = revision or self.rules_revision
        payload = f"{self.project_id}\0{effective_revision}\0{normalized}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _normalize(text: str) -> str:
        """Strip volatile tokens; JSON key order preserved as-is."""
        cleaned = _VOLATILE_RE.sub("", text)
        return cleaned.rstrip("\n")

    # -- bundle assembly -----------------------------------------------------
    def build(self, files: dict[str, str], boundary: str, acceptance: str,
              volatile: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build a context bundle with stable + volatile sections.

        files: {relative_path: content}. boundary/acceptance are required
        contract markers; missing either fails closed.
        """
        if not boundary.strip():
            raise ValueError("context_bundle_missing_boundary")
        if not acceptance.strip():
            raise ValueError("context_bundle_missing_acceptance")

        stable_lines: list[str] = []
        for rel in sorted(files):
            content = files[rel]
            stable_lines.append(f"=== {rel} ===")
            stable_lines.append(self._normalize(content))

        stable_block = "\n".join(stable_lines)
        stable_digest = self.stable_digest(stable_block, self.rules_revision)

        return {
            "schema_version": SCHEMA_VERSION,
            "project_id": self.project_id,
            "rules_revision": self.rules_revision,
            "boundary": boundary,
            "acceptance": acceptance,
            "stable_prefix": stable_block,
            "stable_digest": stable_digest,
            "volatile": volatile or {},
            "volatile_absent": volatile is None,
        }

    # -- validation ----------------------------------------------------------
    @staticmethod
    def validate(bundle: dict[str, Any]) -> tuple[bool, str]:
        required = ("schema_version", "project_id", "rules_revision",
                    "boundary", "acceptance", "stable_prefix", "stable_digest")
        for key in required:
            if key not in bundle:
                return False, f"missing required field: {key}"
        if not bundle.get("boundary"):
            return False, "boundary empty (fail closed)"
        if not bundle.get("acceptance"):
            return False, "acceptance empty (fail closed)"
        return True, "bundle valid"

    # -- project isolation ---------------------------------------------------
    @staticmethod
    def project_mismatch(bundle: dict[str, Any], project_id: str) -> bool:
        return bundle.get("project_id") != project_id

    # -- revision invalidation ------------------------------------------------
    @staticmethod
    def revision_changed(bundle: dict[str, Any], current_revision: str) -> bool:
        return bundle.get("rules_revision") != current_revision


def build_from_directory(bundle: ContextBundle, root: Path,
                         selectors: list[str], boundary: str, acceptance: str) -> dict[str, Any]:
    """Read selected files (relative-path selectors) into a bundle. Read-only."""
    files: dict[str, str] = {}
    for selector in selectors:
        path = (root / selector).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            raise ValueError(f"path escape rejected: {selector}")
        if path.is_file():
            files[selector] = path.read_text(encoding="utf-8", errors="replace")
    return bundle.build(files, boundary, acceptance)


if __name__ == "__main__":
    b = ContextBundle("work-lab", "rev-1")
    bundle = b.build(
        {"rules.md": "No E: drive.\n2026-08-16T00:00:00Z temp/abc"},
        boundary="project root only",
        acceptance="tests pass",
    )
    print(json.dumps({k: v for k, v in bundle.items() if k != "stable_prefix"}, ensure_ascii=False, indent=2))
    print("valid:", ContextBundle.validate(bundle))
