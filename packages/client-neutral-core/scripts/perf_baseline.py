#!/usr/bin/env python
"""WLGM-230/§4.3 performance baseline for observer collectors.

Measures real latency of the non-interfering collectors against the task-pack
budgets (single-project git query < 2s, heartbeat path < 100ms, collector
timeout 2-5s). Produces P50/P95 and a PASS/PENDING verdict. This is the
performance-comparison evidence for WLGM-240 (no agent task-duration impact is
measurable here without an external canary; that stays PENDING).
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

WORK = Path(r"D:\All projects\WORK-LAB")
SCRIPTS = WORK / "10-workflow" / "workflow-assistance" / "scripts" / "workflow"
sys.path.insert(0, str(SCRIPTS))

from git_collector import collect_git_observation  # noqa: E402
from product_project import ProductProject, RepositoryIdentity  # noqa: E402
from project_identity_resolver import ApprovedProjectIndex, GitProbe, resolve_execution_path  # noqa: E402


def percentile(samples: list[float], p: float) -> float:
    ordered = sorted(samples)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, int(len(ordered) * p / 100))
    return ordered[index]


def measure(fn, rounds: int = 20) -> dict[str, float]:
    samples: list[float] = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000)  # ms
    return {
        "p50_ms": round(percentile(samples, 50), 3),
        "p95_ms": round(percentile(samples, 95), 3),
        "max_ms": round(max(samples), 3),
        "samples": rounds,
    }


def main() -> int:
    report: dict[str, object] = {"schemaVersion": "worklab/perf-baseline/v1", "project": "work-lab"}

    git_stats = measure(lambda: collect_git_observation(WORK, include_dirty=True))
    report["git_collector_ms"] = git_stats

    project = ProductProject(project_id="work-lab")
    project.add_repository(RepositoryIdentity(repository_id="work-lab", remote_identity="github:DTALEX66/WORK-LAB"))
    index = ApprovedProjectIndex(projects=[project])
    probe = GitProbe()
    resolver_stats = measure(lambda: resolve_execution_path(str(WORK), index, git=probe), rounds=50)
    report["identity_resolver_ms"] = resolver_stats

    # Heartbeat path is a pure in-memory dict build (collector_scheduler emits
    # heartbeat events without IO); measure it directly.
    from execution_evidence import ExecutionEvidence  # noqa: E402

    heartbeat_stats = measure(
        lambda: ExecutionEvidence(
            event_id="hb", event_type="execution_heartbeat", occurred_at="2026-08-14T00:00:00Z",
        ).as_record(),
        rounds=200,
    )
    report["heartbeat_ms"] = heartbeat_stats

    budgets = {
        # §4.3: single-project git query < 2s.
        "git_collector_budget_2s": git_stats["p95_ms"] < 2000,
        # §4.3: heartbeat send budget < 100ms (async, non-blocking).
        "heartbeat_budget_100ms": heartbeat_stats["p95_ms"] < 100,
        # Resolver is a LOW-FREQUENCY identity path (15-30s sampling), not the
        # heartbeat; budget covers several git subprocess spawns on Windows.
        "resolver_low_freq_budget_500ms": resolver_stats["p95_ms"] < 500,
    }
    report["budgets"] = budgets
    report["verdict"] = "PASS" if all(budgets.values()) else "FAIL"
    report["external_canary_perf_impact"] = "PENDING (requires WORKLAB_CANARY_PROJECT_ROOTS + agent task duration baseline)"

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("\nPERF_BASELINE", report["verdict"])
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
