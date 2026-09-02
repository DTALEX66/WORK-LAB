"""Durable local worker loop for the Workflow Assistance control plane.

Single-instance, resumable background worker. Uses the canonical SQLite WAL
store for leases, checkpoints, heartbeats and fencing. Drives the task loop:

    acquire -> heartbeat -> checkpoint -> intent -> side effect
    -> readback -> reconcile -> release / defer / retry / block

and runs bounded collectors (task / git-ci / usage / source-quality) that only
write canonical facts. No model dependency, no cloud database; degraded to
UNAVAILABLE/OFFLINE/STALE when a collector's source is missing.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# CLI may run this file directly (python durable_worker.py ...); resolve the
# shared module roots (canonical_store / sidecar_lock live under
# packages/client-neutral-core/scripts after the directory convergence).
_ROOT = Path(__file__).resolve().parents[2]
_CNC = _ROOT / "packages" / "client-neutral-core" / "scripts"
if str(_CNC) not in sys.path:
    sys.path.insert(0, str(_CNC))

from canonical_store import CanonicalStore
from sidecar_lock import SingleInstanceLock

DEFAULT_TICK_SECONDS = 30.0
MAX_RETRIES_PER_FINGERPRINT = 3
WINDOW_SECONDS = 3600.0


class CollectorError(RuntimeError):
    pass


@dataclass
class CollectorResult:
    kind: str
    ok: bool
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    degraded: str | None = None


CollectorFn = Callable[[CanonicalStore, str], CollectorResult]


def fingerprint(cause: str) -> str:
    import hashlib

    return hashlib.sha256(cause.encode("utf-8", errors="replace")).hexdigest()


class DurableWorker:
    """Runs one bounded worker tick; safe to call from a thread or process."""

    def __init__(
        self,
        store: CanonicalStore,
        project_id: str = "work-lab",
        tick_seconds: float = DEFAULT_TICK_SECONDS,
        lease_ttl_seconds: int = 300,
        collectors: list[CollectorFn] | None = None,
        task_handler: Callable[[CanonicalStore, dict[str, Any]], None] | None = None,
    ) -> None:
        self.store = store
        self.project_id = project_id
        self.tick_seconds = tick_seconds
        self.lease_ttl_seconds = lease_ttl_seconds
        self.holder = f"worker-{uuid.uuid4().hex[:12]}"
        self.collectors = collectors or []
        self.task_handler = task_handler
        self._retries: dict[str, int] = {}
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def run_once(self) -> dict[str, Any]:
        """Execute one tick: reclaim zombies, run collectors, drive one task."""
        results: dict[str, Any] = {"tick": time.time(), "holder": self.holder}

        reclaimed = self.store.claim_expired_tasks(self.holder, self.lease_ttl_seconds)
        results["zombie_reclaimed"] = reclaimed

        collector_outcomes: list[dict[str, Any]] = []
        for collector in self.collectors:
            name = str(getattr(collector, "collector_name", getattr(collector, "__name__", "unknown")))
            try:
                outcome = collector(self.store, self.project_id)
                for record in outcome.records:
                    self._write_record(outcome.kind, record)
                self._record_collector_health(name, ok=outcome.ok)
                collector_outcomes.append(
                    {
                        "kind": outcome.kind,
                        "ok": outcome.ok,
                        "records": len(outcome.records),
                        "degraded": outcome.degraded,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - one source must not kill the durable loop
                self._record_collector_health(name, ok=False)
                collector_outcomes.append({"kind": name, "ok": False, "error": str(exc)[:500]})
        results["collectors"] = collector_outcomes

        if self.task_handler is not None:
            results["task"] = self._drive_task()
        return results

    def _write_record(self, kind: str, record: dict[str, Any]) -> None:
        if kind == "telemetry":
            self.store.append_telemetry(record)
        elif kind == "usage":
            self.store.record_usage_sample(record)
        elif kind == "ci":
            self.store.record_ci_run(record)
        elif kind == "quality":
            self.store.append_quality(record)

    def _record_collector_health(self, name: str, *, ok: bool) -> None:
        previous = {row["name"]: row for row in self.store.list_collector_health()}.get(name, {})
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        failures = 0 if ok else int(previous.get("consecutive_failures") or 0) + 1
        self.store.upsert_collector_health(
            {
                "name": name,
                "totalRuns": int(previous.get("total_runs") or 0) + 1,
                "lastRunAt": now,
                "lastSuccessAt": now if ok else previous.get("last_success_at"),
                "consecutiveFailures": failures,
                "circuitOpenUntil": previous.get("circuit_open_until"),
                "droppedCount": int(previous.get("dropped_count") or 0),
            }
        )

    def _drive_task(self) -> dict[str, Any]:
        """Pick one ready task, lease it transactionally, run, reconcile."""
        ready = [task for task in self.store.list_tasks() if task["status"] in {"PENDING", "RETRYING", "RUNNING", "FAILED_RECOVERABLE"}]
        if not ready:
            return {"status": "idle", "holder": self.holder}
        task = ready[0]
        task_id = task["task_id"]
        acquired = self.store.acquire_lease(task_id, self.holder, self.lease_ttl_seconds)
        if not acquired:
            return {"status": "lease_busy", "task": task_id}
        try:
            # Heartbeat before side effect so a slow handler keeps the lease.
            self.store.heartbeat(task_id, self.holder, self.lease_ttl_seconds)
            checkpoint = task.get("checkpoint") or {}
            checkpoint["last_attempt_holder"] = self.holder
            self.store.upsert_task(
                {
                    "task_id": task_id,
                    "project_id": task.get("project_id", self.project_id),
                    "status": "RUNNING",
                    "checkpoint": checkpoint,
                    "lease_holder": self.holder,
                }
            )
            self.task_handler(self.store, task)
            self.store.upsert_task(
                {
                    "task_id": task_id,
                    "project_id": task.get("project_id", self.project_id),
                    "status": "COMPLETED_LOCAL",
                    "checkpoint": {**checkpoint, "completed_by": self.holder},
                }
            )
            self._retries.pop(fingerprint(task_id), None)
            return {"status": "completed", "task": task_id}
        except Exception as exc:  # noqa: BLE001 - worker must never die
            cause = f"{task_id}:{type(exc).__name__}:{exc}"
            fp = fingerprint(cause)
            attempts = self._retries.get(fp, 0) + 1
            self._retries[fp] = attempts
            new_status = "FAILED_RECOVERABLE" if attempts <= MAX_RETRIES_PER_FINGERPRINT else "BLOCKED_POLICY"
            self.store.upsert_task(
                {
                    "task_id": task_id,
                    "project_id": task.get("project_id", self.project_id),
                    "status": new_status,
                    "checkpoint": {
                        **checkpoint,
                        "last_error": str(exc)[:500],
                        "error_fingerprint": fp,
                        "attempts": attempts,
                    },
                }
            )
            return {"status": new_status, "task": task_id, "attempts": attempts}
        finally:
            self.store.release_lease(task_id, self.holder)

    def run_forever(self) -> None:
        while not self._stopped:
            try:
                self.run_once()
                self._record_collector_health("worker_loop", ok=True)
            except Exception:  # noqa: BLE001 - supervisor loop must recover on the next tick
                try:
                    self._record_collector_health("worker_loop", ok=False)
                except Exception:
                    pass
            deadline = time.time() + self.tick_seconds
            while time.time() < deadline and not self._stopped:
                time.sleep(0.25)


class WorkerSupervisor:
    """Owns the single-instance lock and the worker; runs one supervisor."""

    def __init__(self, runtime_root: Path, worker: DurableWorker) -> None:
        self.runtime_root = runtime_root.resolve()
        self.worker = worker
        self._lock = SingleInstanceLock(self.runtime_root / "worker.lock")

    def start(self) -> None:
        self._lock.acquire()

    def stop(self) -> None:
        self._lock.release()


def make_worker(
    store: CanonicalStore,
    *,
    project_id: str = "work-lab",
    tick_seconds: float = DEFAULT_TICK_SECONDS,
    collectors: list[CollectorFn] | None = None,
    task_handler: Callable[[CanonicalStore, dict[str, Any]], None] | None = None,
) -> DurableWorker:
    return DurableWorker(
        store,
        project_id=project_id,
        tick_seconds=tick_seconds,
        collectors=collectors,
        task_handler=task_handler,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the durable Workflow Assistance worker")
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--project-id", default="work-lab")
    parser.add_argument("--tick", type=float, default=DEFAULT_TICK_SECONDS)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    runtime_root = args.runtime_root.resolve()
    project_root = args.project_root.resolve()
    store = CanonicalStore(runtime_root / "canonical.sqlite")
    store.register_project(args.project_id, str(project_root), display_name=project_root.name)
    from collectors import build_standard_collectors

    worker = make_worker(
        store,
        project_id=args.project_id,
        tick_seconds=args.tick,
        collectors=build_standard_collectors(project_root),
    )
    supervisor = WorkerSupervisor(runtime_root, worker)
    supervisor.start()
    try:
        if args.once:
            print(json.dumps(worker.run_once(), ensure_ascii=False, default=str))
        else:
            print(f"WORKFLOW_WORKER_READY holder={worker.holder} tick={args.tick}")
            worker.run_forever()
    finally:
        worker.stop()
        supervisor.stop()
        store.close()
