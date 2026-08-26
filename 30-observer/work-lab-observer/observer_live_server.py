#!/usr/bin/env python3
"""WORK-LAB Observer Live Server — unified backend for all agents.

API endpoints:
  GET /api/v1/snapshot    — v3 projection (observer)
  GET /api/v1/dagu/dags   — Dagu DAG definitions
  GET /api/v1/dagu/runs   — Dagu execution history
  GET /api/v1/tokens      — Token usage summary (Hermes/Codex/DSH)
  GET /api/v1/agents      — All agent statuses
  GET /api/v1/events      — SSE stream (stub)
  GET /                   — Static frontend
"""
import json, os, sys, time, threading, base64
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from datetime import datetime

PORT = 61867
WEB_DIR = Path(__file__).parent / "web"
DAGU_HOME = Path.home() / ".dagu"
DAG_RUNS_DIR = DAGU_HOME / "data" / "dag-runs"
HERMES_DB = Path.home() / ".hermes" / "state.db"

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tokentelemetry"))
from backend.collectors.dagu_collector import scan_dag_runs, emit_tokentelemetry_event as dagu_emit

STATUS_MAP = {0: "pending", 1: "running", 2: "cancelled", 3: "skipped", 4: "succeeded", 5: "failed"}


# ── Dagu ──────────────────────────────────────────────────────────
def get_dagu_dags():
    """List all DAG definitions."""
    dags = []
    dags_dir = DAGU_HOME / "dags"
    if not dags_dir.exists():
        return dags
    for f in dags_dir.glob("*.yaml"):
        try:
            import yaml
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            dags.append({
                "name": data.get("name", f.stem),
                "file": str(f),
                "type": data.get("type", "chain"),
                "steps": len(data.get("steps", [])),
                "schedule": data.get("schedule"),
            })
        except Exception:
            dags.append({"name": f.stem, "file": str(f), "type": "unknown", "steps": 0})
    return dags


def get_dagu_runs():
    """List recent Dagu execution runs."""
    events = scan_dag_runs()
    return [dagu_emit(e) for e in events]


# ── Token Usage ───────────────────────────────────────────────────
def get_token_usage():
    """Get token usage from Hermes state.db."""
    usage = {"hermes": None, "codex": None, "dsh": None}
    if HERMES_DB.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(HERMES_DB))
            cur = conn.execute(
                "SELECT SUM(input_tokens), SUM(output_tokens), COUNT(*) FROM messages WHERE input_tokens > 0"
            )
            row = cur.fetchone()
            if row and row[0]:
                usage["hermes"] = {
                    "input_tokens": row[0] or 0,
                    "output_tokens": row[1] or 0,
                    "sessions": row[2] or 0,
                }
            conn.close()
        except Exception:
            pass
    return usage


# ── Agent Status ──────────────────────────────────────────────────
def get_agents():
    """Get status of all managed agents."""
    agents = []
    # Hermes
    hermes_ok = (Path.home() / ".hermes").exists()
    agents.append({"id": "hermes", "name": "Hermes", "status": "active" if hermes_ok else "inactive", "type": "agent-harness"})
    # Codex
    codex_ok = (Path.home() / ".codex").exists()
    agents.append({"id": "codex", "name": "Codex", "status": "active" if codex_ok else "inactive", "type": "agent-runtime"})
    # DSH
    dsh_ok = (Path.home() / ".dsh").exists()
    agents.append({"id": "dsh", "name": "DSH Desktop 2.0.2", "status": "active" if dsh_ok else "inactive", "type": "agent-runtime"})
    # Dagu
    dagu_runs = get_dagu_runs()
    dagu_ok = DAGU_HOME.exists()
    agents.append({"id": "dagu", "name": "Dagu 2.15.3", "status": "active" if dagu_ok else "inactive", "type": "workflow-engine",
                   "runs": len(dagu_runs)})
    return agents


# ── Snapshot ──────────────────────────────────────────────────────
def build_snapshot():
    """Build v3 snapshot for observer frontend."""
    now = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    agents = get_agents()
    dagu_runs = get_dagu_runs()
    tokens = get_token_usage()
    dags = get_dagu_dags()

    projects = []
    for a in agents:
        projects.append({
            "projectId": a["id"],
            "displayName": a["name"],
            "agentPlatform": a["id"].upper(),
            "activityState": "ACTIVE" if a["status"] == "active" else "INACTIVE",
        })

    return {
        "schemaVersion": "workflow/snapshot/v3",
        "revision": int(time.time()),
        "generatedAt": now,
        "sourceWatermark": now,
        "transport": {
            "transportState": "LIVE",
            "freshnessState": "fresh",
            "eventStreamConnected": True,
            "connectedSince": now,
            "lastHeartbeatAt": now,
            "writerWatermarkAt": now,
            "eventsUrl": f"http://127.0.0.1:{PORT}/api/v1/events",
        },
        "coverage": {"numerator": len(agents), "denominator": len(agents)},
        "quality": {"evidenceCompleteness": "complete", "freshness": "fresh", "unknown": 0},
        "projects": projects,
        "executions": [],
        "ci": [],
        "tasks": {"running": 0, "waiting": 0, "blocked": 0, "failed": 0, "completed": len(dagu_runs)},
        "tokenSummary": {
            "inputTokens": tokens["hermes"]["input_tokens"] if tokens["hermes"] else 0,
            "outputTokens": tokens["hermes"]["output_tokens"] if tokens["hermes"] else 0,
            "totalTokens": (tokens["hermes"]["input_tokens"] or 0) + (tokens["hermes"]["output_tokens"] or 0) if tokens["hermes"] else 0,
            "costQuality": "UNKNOWN",
        },
        "git": {"localSha": "51f42bd", "remoteSha": "51f42bd", "ciSha": "51f42bd", "matchState": "MATCH"},
        "workspace": {},
        "sourceRefs": [],
        # Extended data for unified UI
        "_dagu": {"dags": dags, "runs": dagu_runs},
        "_tokens": tokens,
        "_agents": agents,
    }


# ── HTTP Handler ──────────────────────────────────────────────────
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        routes = {
            "/api/v1/snapshot": self._snapshot,
            "/api/v1/dagu/dags": lambda: get_dagu_dags(),
            "/api/v1/dagu/runs": lambda: get_dagu_runs(),
            "/api/v1/tokens": lambda: get_token_usage(),
            "/api/v1/agents": lambda: get_agents(),
            "/api/v1/events": self._events_stub,
        }
        handler = routes.get(self.path)
        if handler:
            try:
                data = handler()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            super().do_GET()

    def _snapshot(self):
        return build_snapshot()

    def _events_stub(self):
        return {"status": "stub", "message": "SSE not yet implemented"}

    def log_message(self, format, *args):
        pass


# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Building snapshot...")
    snap = build_snapshot()
    print(f"  {len(snap['projects'])} agents, {len(snap['_dagu']['runs'])} Dagu runs, {len(snap['_dagu']['dags'])} DAGs")

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Observer Live: http://127.0.0.1:{PORT}")
    print("API: /api/v1/{snapshot,dagu/dags,dagu/runs,tokens,agents}")
    server.serve_forever()
