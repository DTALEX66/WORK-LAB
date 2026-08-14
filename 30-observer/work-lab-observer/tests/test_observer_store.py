from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "10-workflow" / "workflow-assistance" / "scripts" / "workflow"))

from canonical_store import CanonicalStore  # noqa: E402
from observer_runtime import ObserverInputError  # noqa: E402
from observer_store import ObserverStore  # noqa: E402


class ObserverStoreTests(unittest.TestCase):
    def make_root(self, raw: str) -> tuple[Path, Path]:
        project = Path(raw)
        (project / ".git").mkdir()
        path = project / ".hermes" / "task-runtime" / "workflow" / "canonical.sqlite"
        writer = CanonicalStore(path)
        writer.register_project("work-lab", "<redacted>")
        writer.upsert_task({"task_id": "t1", "project_id": "work-lab", "status": "RUNNING"})
        writer.close()
        return project, path

    def test_reads_canonical_projection_without_mutating_database(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_root(raw)
            before = (path.stat().st_mtime_ns, path.stat().st_size)
            store = ObserverStore(path, project_root=project)
            projection = store.rebuild_projection()
            store.close()
            after = (path.stat().st_mtime_ns, path.stat().st_size)
            self.assertEqual(projection["schemaVersion"], "workflow/snapshot/v3")
            self.assertIn("executions", projection)
            self.assertIn("tokenSummary", projection)
            self.assertEqual(before, after)
            self.assertFalse((path.parent.parent / "observer").exists())

    def test_append_is_always_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_root(raw)
            store = ObserverStore(path, project_root=project)
            with self.assertRaises(ObserverInputError):
                store.append([{"eventId": "forbidden"}])
            store.close()

    def test_rejects_noncanonical_or_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_root(raw)
            with self.assertRaises(ValueError):
                ObserverStore(path.parent / "observer-events.jsonl", project_root=project)
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                ObserverStore(path, project_root=project)

    def test_rebuild_enriches_governance_from_real_repo(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project, path = self.make_root(raw)
            store = ObserverStore(path, project_root=project)
            projection = store.rebuild_projection()
            store.close()
            gov = projection.get("governance", {})
            # Governance must carry real repo inventory dimensions, never all-None
            # placeholders once the repo exists.
            self.assertIsInstance(gov.get("rules", {}).get("current"), (int, type(None)))
            self.assertIsInstance(gov.get("skills", {}).get("current"), (int, type(None)))
            self.assertIsInstance(gov.get("adapters", {}).get("current"), (int, type(None)))


if __name__ == "__main__":
    unittest.main()
