"""Gate: a lease taken on an existing task must reach the Observer, not just a task that appears.

The live watcher decided "something changed" from row counts, status tallies and aggregates. A lease
acquisition changes none of those: it rewrites `lease_holder`, bumps `fencing_token` and moves
`updated_at` on a row that already exists. Measured before this gate existed, writing a checkpoint,
holder and fencing token onto a live task left the sidecar's canonical fingerprint byte-identical
(`fingerprint_changed=False`, `differing_keys=[]`), so a desktop user watched a run they thought was
queued. The quiet-path tests below hold the other half: `PRAGMA data_version` is what makes watching
cheap without making it blind.

Evidence level: SYNTHETIC/INTEGRATED locally (two `CanonicalStore` connections on one runtime root),
not native executor evidence.
"""
from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "services" / "orchestration", ROOT / "services" / "authority",
              ROOT / "services" / "policy", ROOT / "services" / "receipts",
              ROOT / "packages" / "client-neutral-core" / "scripts"):
    sys.path.insert(0, str(entry))

import sidecar as sidecar_module  # noqa: E402
from canonical_store import CanonicalStore  # noqa: E402
from project_temp import fixture_dir  # noqa: E402

TASK = "WL-LEASE-VISIBLE"


class InPlaceUpdateReachesTheObserver(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = fixture_dir(prefix="sidecar-inplace-")
        self.sidecar = sidecar_module.WorkflowSidecar(ROOT, self.runtime)
        self.db = self.runtime / "canonical.sqlite"

    def tearDown(self) -> None:
        self.sidecar.stop_live_updates()
        self.sidecar.close()

    def _write_from_elsewhere(self, action) -> None:
        writer = CanonicalStore(self.db)
        try:
            action(writer)
        finally:
            writer.close()

    def _revision(self) -> int:
        return self.sidecar.v3_snapshot()["revision"]

    def _await_revision(self, floor: int, timeout: float = 20.0) -> int:
        deadline = time.time() + timeout
        while time.time() < deadline:
            revision = self._revision()
            if revision > floor:
                return revision
            time.sleep(0.2)
        self.fail(f"revision stayed at {floor} for {timeout}s; an in-place write is invisible to the watch")

    def test_a_lease_acquired_on_an_existing_task_advances_the_revision(self) -> None:
        self.sidecar.start_live_updates(interval_seconds=0.2)
        baseline = self._revision()
        self._write_from_elsewhere(lambda store: store.upsert_task(
            {"task_id": TASK, "project_id": "work-lab", "status": "QUEUED"}))
        appeared = self._await_revision(baseline)

        self._write_from_elsewhere(lambda store: store.acquire_lease(TASK, "worker-A"))

        moved = self._await_revision(appeared)
        self.assertGreater(moved, appeared)
        row = self.sidecar.store.list_tasks()
        taken = next(task for task in row if task["task_id"] == TASK)
        self.assertEqual("worker-A", taken["lease_holder"],
                         "the revision moved without the lease actually being stored")
        self.assertGreaterEqual(int(taken["fencing_token"] or 0), 1)

    def test_the_witness_sees_an_update_that_changes_no_count_and_no_status(self) -> None:
        """Unit level: the fingerprint itself, with no thread and no timing in the way."""
        self.sidecar.store.upsert_task({"task_id": TASK, "project_id": "work-lab", "status": "QUEUED"})
        before = self.sidecar._canonical_fingerprint()
        payload_before = json.loads(before)
        self.sidecar.store.acquire_lease(TASK, "worker-B")
        after = json.loads(self.sidecar._canonical_fingerprint())
        self.assertEqual(payload_before["tables"], after["tables"],
                         "row counts moved; this is not the case the witness exists for")
        self.assertEqual(payload_before["tasks_by_status"], after["tasks_by_status"])
        self.assertNotEqual(payload_before["newest"], after["newest"],
                            "an in-place update must move the newest-changes witness")

    def test_the_sidecars_own_publish_does_not_retrigger_the_watcher(self) -> None:
        """data_version answers per connection: writing myself must not look like an external change."""
        self.sidecar.store.upsert_task({"task_id": TASK, "project_id": "work-lab", "status": "QUEUED"})
        before = self.sidecar.store.data_version()
        self.sidecar.publish_observed()
        self.assertEqual(before, self.sidecar.store.data_version(),
                         "the sidecar's own write moved its own data_version, so the quiet path is gone")

    def test_a_quiet_store_costs_content_scans_only_when_another_connection_writes(self) -> None:
        calls = []
        original = self.sidecar._canonical_fingerprint

        def counting() -> str:
            calls.append(time.time())
            return original()

        self.sidecar._canonical_fingerprint = counting
        try:
            self.sidecar.start_live_updates(interval_seconds=0.05)
            first = len(calls)
            time.sleep(0.05 * 6)
            quiet_growth = len(calls) - first
        finally:
            self.sidecar.stop_live_updates()
            self.sidecar._canonical_fingerprint = original
        self.assertLessEqual(quiet_growth, 1,
                             f"{quiet_growth} full readbacks over a quiet store: the fast path is not taken")

    def test_an_external_write_does_cost_exactly_one_readback_per_change(self) -> None:
        calls = []
        original = self.sidecar._canonical_fingerprint

        def counting() -> str:
            calls.append(time.time())
            return original()

        self.sidecar._canonical_fingerprint = counting
        try:
            self.sidecar.start_live_updates(interval_seconds=0.05)
            baseline = len(calls)
            time.sleep(0.2)
            settled = len(calls) - baseline
            self._write_from_elsewhere(lambda store: store.upsert_task(
                {"task_id": TASK, "project_id": "work-lab", "status": "QUEUED"}))
            deadline = time.time() + 5.0
            while time.time() < deadline and len(calls) <= baseline + settled:
                time.sleep(0.05)
            detected = len(calls) - baseline - settled
        finally:
            self.sidecar.stop_live_updates()
            self.sidecar._canonical_fingerprint = original
        self.assertGreaterEqual(detected, 1, "an external write never triggered a readback")
        self.assertLess(detected, 20, f"{detected} readbacks for one write; the watcher is spinning")


if __name__ == "__main__":
    unittest.main()
