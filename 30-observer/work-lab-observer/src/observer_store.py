from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from observer_canonical import CanonicalProjectionReader, open_canonical_reader
from observer_runtime import ObserverInputError


class ObserverStore:
    """Strictly read-only facade over Workflow-owned canonical SQLite."""

    def __init__(self, canonical_path: Path, *, project_root: Path) -> None:
        self.project_root = Path(project_root).resolve()
        if not (self.project_root / ".git").exists():
            raise ValueError("Observer store project root must be a Git project")
        self.path = Path(canonical_path).resolve()
        expected = (
            self.project_root / ".hermes" / "task-runtime" / "workflow" / "canonical.sqlite"
        ).resolve()
        if self.path != expected:
            raise ValueError("Observer must read the Workflow-owned canonical SQLite path")
        self.reader: CanonicalProjectionReader = open_canonical_reader(self.path)

    def rebuild_projection(self) -> dict[str, Any]:
        projection = self.reader.to_dashboard()
        # Enrich governance with REAL repo inventory (skills/adapters/rules from
        # CURRENT_STATE.json / adapter-registry.json / 00-governance/rules) so the
        # dashboard never shows an empty governance pane when the repo is present.
        from observer_runtime import load_governance

        skills_dim, adapters_dim, rules_count = load_governance(self.project_root)
        projection["governance"] = {
            "rules": {"current": rules_count, "drift": None, "quarantined": None, "conflicts": None, "stale": None},
            "skills": skills_dim,
            "adapters": adapters_dim,
            "memoryContext": {"current": None, "drift": None, "quarantined": None, "conflicts": None, "stale": None},
        }
        return projection

    def read_events(self) -> list[dict[str, Any]]:
        """Legacy event access is retired; canonical projections replace it."""
        return []

    def append(self, incoming: Iterable[dict[str, Any]]) -> int:
        raise ObserverInputError(
            "Observer is read-only: canonical writes belong to Workflow Assistance"
        )

    def close(self) -> None:
        self.reader.store.close()
