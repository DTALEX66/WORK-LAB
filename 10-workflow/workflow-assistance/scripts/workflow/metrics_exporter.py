"""WORK-LAB Observer Prometheus metrics endpoint.

Reads canonical.sqlite (Workflow-owned facts) and exposes read-only Prometheus
metrics on :9100. Strictly read-only projection - never writes to canonical.

Boundary: runs inside WORK-LAB runtime root; binds loopback only.
"""
from __future__ import annotations

import os
import sqlite3
import time

from prometheus_client import Gauge, start_http_server

CANONICAL_DB = os.environ.get(
    "WL_CANONICAL_DB",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".hermes", "task-runtime", "canonical.sqlite"),
)


def _db() -> sqlite3.Connection | None:
    path = os.path.normpath(os.path.abspath(CANONICAL_DB))
    if not os.path.exists(path):
        return None
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=3)


def main() -> None:
    g_projects = Gauge("wlobs_projects", "Approved projects count", ["state"])
    g_executions = Gauge("wlobs_executions", "Execution instances", ["state"])
    g_usage_tokens = Gauge("wlobs_usage_tokens", "Token usage summary", ["kind"])
    g_cost = Gauge("wlobs_cost_estimate", "Cost estimate (USD)", [])
    g_platform = Gauge("wlobs_platform_observations", "Platform observations", ["project_id"])

    start_http_server(9100, addr="127.0.0.1")
    print("worklab-observer metrics on http://127.0.0.1:9100/metrics")

    while True:
        conn = _db()
        if conn is not None:
            try:
                cur = conn.cursor()
                rows = cur.execute(
                    "SELECT status, COUNT(*) FROM projects GROUP BY status"
                ).fetchall()
                g_projects.clear()
                for state, cnt in rows:
                    g_projects.labels(str(state or "unknown")).set(cnt)

                rows = cur.execute(
                    "SELECT state, COUNT(*) FROM execution_instances GROUP BY state"
                ).fetchall()
                g_executions.clear()
                for state, cnt in rows:
                    g_executions.labels(str(state or "unknown")).set(cnt)

                rows = cur.execute(
                    "SELECT COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), COALESCE(SUM(total_tokens),0) FROM usage_samples"
                ).fetchone()
                if rows:
                    g_usage_tokens.labels("input").set(rows[0] or 0)
                    g_usage_tokens.labels("output").set(rows[1] or 0)
                    g_usage_tokens.labels("total").set(rows[2] or 0)

                cost = cur.execute(
                    "SELECT COALESCE(SUM(cost_estimate),0) FROM usage_samples"
                ).fetchone()
                g_cost.set(cost[0] or 0)

                rows = cur.execute(
                    "SELECT project_id, COUNT(*) FROM platform_observations GROUP BY project_id"
                ).fetchall()
                g_platform.clear()
                for pid, cnt in rows:
                    g_platform.labels(str(pid)).set(cnt)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"metrics error: {exc}")
            finally:
                conn.close()
        time.sleep(10)


if __name__ == "__main__":
    main()
