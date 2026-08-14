"""Contract tests for the four bounded collectors (WL3-510)."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from canonical_store import CanonicalStore
from collectors import (
    collect_git_ci,
    collect_source_quality,
    collect_task_ledger,
    collect_usage_files,
)


def _make_git_project(root: Path, name: str) -> Path:
    project = root / name
    project.mkdir(parents=True)
    (project / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-qm", "init"],
        cwd=project,
        check=True,
    )
    return project


class CollectorsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.store = CanonicalStore(self.root / "canonical.sqlite")

    def tearDown(self) -> None:
        self.store.close()
        self._temporary.cleanup()

    def test_task_ledger_collector(self) -> None:
        self.store.upsert_task({"task_id": "t1", "project_id": "p", "status": "PENDING"})
        self.store.upsert_task({"task_id": "t2", "project_id": "p", "status": "COMPLETED_LOCAL"})
        result = collect_task_ledger(self.store, "p")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0]["total"], 2)
        self.assertEqual(result.records[0]["task_counts"]["PENDING"], 1)
        repeated = collect_task_ledger(self.store, "p")
        self.assertEqual(result.records[0]["event_id"], repeated.records[0]["event_id"])
        self.store.append_telemetry(result.records[0])
        self.store.append_telemetry(repeated.records[0])
        self.assertEqual(self.store.projection()["telemetry_events"], 1)

    def test_git_ci_collector_reads_real_head_without_estimates(self) -> None:
        project = _make_git_project(self.root, "collector-demo")
        result = collect_git_ci(self.store, "collector-demo", project)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record["quality"], "EXACT_SOURCE")
        self.assertRegex(record["head_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(record["dirty_count"], 0)
        repeated = collect_git_ci(self.store, "collector-demo", project).records[0]
        self.assertEqual(record["row_id"], repeated["row_id"])
        self.store.append_quality(record)
        self.store.append_quality(repeated)
        self.assertEqual(len(self.store.list_source_quality()), 1)

    def test_usage_collector_accepts_only_explicit_counters(self) -> None:
        artifacts = self.root / ".hermes" / "task-artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "usage.jsonl").write_text(
            json.dumps(
                {
                    "provider": "deepseek",
                    "model": "deepseek-v4-flash",
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                    "api_key": "should-never-enter",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = collect_usage_files(self.store, "p", self.root)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record["total_tokens"], 15)
        self.assertNotIn("api_key", record)
        # Worker writes canonical facts; verify the record round-trips through the store.
        sample_id = self.store.record_usage_sample(record)
        self.assertTrue(sample_id)
        projection = self.store.projection()
        self.assertEqual(projection["usage_summary"][0]["tokens"], 15)

    def test_usage_collector_ignores_negative_and_non_numeric(self) -> None:
        artifacts = self.root / ".hermes" / "task-artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "usage.jsonl").write_text(
            json.dumps(
                {
                    "provider": "x",
                    "model": "m",
                    "input_tokens": -1,
                    "output_tokens": "many",
                    "total_tokens": 0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = collect_usage_files(self.store, "p", self.root)
        # total_tokens=0 is a legal explicit zero; input -1 and string dropped.
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.records[0]["total_tokens"], 0)

    def test_usage_polling_is_idempotent_and_preserves_identical_lines(self) -> None:
        artifacts = self.root / ".hermes" / "task-artifacts"
        artifacts.mkdir(parents=True)
        line = json.dumps(
            {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            }
        )
        (artifacts / "usage.jsonl").write_text(line + "\n" + line + "\n", encoding="utf-8")

        first = collect_usage_files(self.store, "p", self.root)
        second = collect_usage_files(self.store, "p", self.root)
        self.assertEqual(len(first.records), 2)
        self.assertEqual(
            [record["sample_id"] for record in first.records],
            [record["sample_id"] for record in second.records],
            "polling the same source must keep stable event identities",
        )
        self.assertEqual(len({record["sample_id"] for record in first.records}), 2)
        for record in first.records + second.records:
            self.store.record_usage_sample(record)
        projection = self.store.projection()
        self.assertEqual(projection["usage_summary"][0]["samples"], 2)
        self.assertEqual(projection["usage_summary"][0]["tokens"], 30)

    def test_source_quality_collector(self) -> None:
        project = _make_git_project(self.root, "quality-demo")
        result = collect_source_quality(self.store, "quality-demo", project)
        self.assertTrue(result.ok)
        self.assertEqual(result.records[0]["quality"], "EXACT_SOURCE")
        repeated = collect_source_quality(self.store, "quality-demo", project)
        self.assertEqual(result.records[0]["row_id"], repeated.records[0]["row_id"])
        self.store.append_quality(result.records[0])
        self.store.append_quality(repeated.records[0])
        self.assertEqual(len(self.store.list_source_quality()), 1)


if __name__ == "__main__":
    unittest.main()
