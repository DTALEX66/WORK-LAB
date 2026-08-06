from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from observer_evidence import open_design_benchmark_event, workflow_evidence_events  # noqa: E402
from observer_runtime import ObserverInputError  # noqa: E402
from observer_store import ObserverStore  # noqa: E402


class ObserverEvidenceTests(unittest.TestCase):
    def envelope(self, *, state: str = "PASS") -> dict:
        digest = hashlib.sha256(b"artifact").hexdigest()
        return {
            "schema_version": "workflow/evidence-envelope/v1",
            "evidence_id": "evidence-001",
            "task_id": "WA-001",
            "state": state,
            "level": "E2",
            "source": {"kind": "isolated", "identity": "local-test"},
            "artifacts": [{"path": "tests/test.py", "sha256": digest, "kind": "test"}],
            "redaction": {"policy": "secrets-never-stored", "secrets_stored": False},
            "checks": ["targeted-test"],
        }

    def registry(self) -> dict:
        return {
            "schema_version": "open-design/benchmark-registry/v1",
            "repeatability": {"human_calibration_required_for_promotion": True},
            "benchmarks": [{"id": "bench-layout", "discipline": "layout"}],
        }

    def test_normalizes_workflow_and_design_inputs_without_payloads(self) -> None:
        workflow = workflow_evidence_events([self.envelope()])[0]
        design = open_design_benchmark_event(self.registry())
        self.assertEqual(workflow["eventType"], "evidence.pass")
        self.assertEqual(workflow["sourceModule"], "workflow-assistance")
        self.assertEqual(design["sourceModule"], "open-design")
        self.assertNotIn("artifacts", workflow)
        self.assertEqual(len(workflow["contentDigest"]), 64)
        self.assertEqual(len(design["contentDigest"]), 64)

    def test_persists_and_rebuilds_cross_module_projection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / ".git").mkdir()
            root = project / ".hermes" / "task-runtime" / "observer"
            root.mkdir(parents=True)
            store = ObserverStore(root, project_root=project)
            self.assertEqual(store.append(workflow_evidence_events([self.envelope()])), 1)
            self.assertEqual(store.append([open_design_benchmark_event(self.registry())]), 1)
            restarted = ObserverStore(root, project_root=project)
            projection = restarted.rebuild_projection()
            self.assertEqual(projection["tasks"]["WA-001"]["events"], 1)
            self.assertEqual(projection["tasks"]["OD-BENCHMARK-REGISTRY"]["events"], 1)

    def test_reads_the_tracked_open_design_registry_contract(self) -> None:
        registry_path = (
            Path(__file__).resolve().parents[3]
            / "20-design/open-design/opendesign-assistance/evals/benchmarks/benchmark-registry.json"
        )
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        event = open_design_benchmark_event(registry)
        self.assertEqual(event["sourceId"], "benchmark-registry")
        self.assertEqual(len(event["evidenceRefs"]), 12)

    def test_sensitive_and_unsafe_states_fail_closed(self) -> None:
        unsafe = self.envelope()
        unsafe["payload"] = {"prompt": "redacted"}
        with self.assertRaises(ObserverInputError):
            workflow_evidence_events([unsafe])
        unsafe_state = self.envelope(state="APPROVED")
        with self.assertRaises(ObserverInputError):
            workflow_evidence_events([unsafe_state])
        registry = self.registry()
        registry["repeatability"]["human_calibration_required_for_promotion"] = False
        with self.assertRaises(ObserverInputError):
            open_design_benchmark_event(registry)


if __name__ == "__main__":
    unittest.main()
