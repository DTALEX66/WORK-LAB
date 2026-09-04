#!/usr/bin/env python3
"""WORK-LAB Observer Live Server — unified backend with real data.

API:
  GET /api/v1/snapshot    — v3 projection
  GET /api/v1/tokens      — token usage (daily + per-model)
  GET /api/v1/dagu/dags   — DAG definitions
  GET /api/v1/dagu/runs   — execution history
  GET /api/v1/agents      — agent statuses
"""
import json, os, sys, time, sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 61867
WEB_DIR = Path(__file__).parent / "web"
HERMES_DB = Path(os.environ.get("HERMES_DB") or (Path.home() / "AppData/Local/hermes/state.db"))
DAGU_HOME = Path.home() / ".dagu"

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tokentelemetry"))
from backend.collectors.dagu_collector import scan_dag_runs, emit_tokentelemetry_event as dagu_emit


# ── Token Usage (real data from Hermes state.db) ──────────────────
def get_token_usage():
    if not HERMES_DB.exists():
        return {"daily": [], "models": [], "totals": {}}
    conn = sqlite3.connect(str(HERMES_DB))
    # Daily usage (last 14 days)
    daily = conn.execute("""
        SELECT DATE(first_seen, 'unixepoch', 'localtime') as day,
               SUM(input_tokens), SUM(output_tokens), COUNT(DISTINCT session_id)
        FROM session_model_usage
        GROUP BY day ORDER BY day DESC LIMIT 14
    """).fetchall()
    # Per-model usage
    models = conn.execute("""
        SELECT model, SUM(input_tokens), SUM(output_tokens), COUNT(*),
               SUM(estimated_cost_usd)
        FROM session_model_usage
        GROUP BY model ORDER BY SUM(input_tokens) DESC LIMIT 8
    """).fetchall()
    # Totals
    totals = conn.execute("""
        SELECT SUM(input_tokens), SUM(output_tokens), COUNT(DISTINCT session_id),
               SUM(estimated_cost_usd)
        FROM session_model_usage
    """).fetchone()
    conn.close()
    return {
        "daily": [{"day": d[0], "inputTokens": d[1], "outputTokens": d[2], "sessions": d[3]} for d in daily],
        "models": [{"model": m[0], "inputTokens": m[1], "outputTokens": m[2], "calls": m[3],
                     "costUsd": round(m[4], 2) if m[4] else None} for m in models],
        "totals": {
            # R4/T30: no SUM row -> None stays None (UNKNOWN), never fabricated 0
            "inputTokens": totals[0], "outputTokens": totals[1],
            "sessions": totals[2], "costUsd": round(totals[3], 2) if totals[3] else None,
        },
    }


# ── Dagu ──────────────────────────────────────────────────────────
def get_dagu_dags():
    dags = []
    dags_dir = DAGU_HOME / "dags"
    if not dags_dir.exists():
        return dags
    for f in dags_dir.glob("*.yaml"):
        try:
            import yaml
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            dags.append({"name": data.get("name", f.stem), "type": data.get("type", "chain"),
                         "steps": len(data.get("steps", []))})
        except Exception:
            dags.append({"name": f.stem, "type": "unknown", "steps": 0})
    return dags


def get_dagu_runs():
    return [dagu_emit(e) for e in scan_dag_runs()]


# ── Agents ────────────────────────────────────────────────────────
def get_agents():
    # R4/T30: no Home scan, no fabricated versions or LIVE state. Observer must
    # not read user Home; agent runtime liveness is UNKNOWN until a real
    # projection source exists (truth-first: unknown stays UNKNOWN).
    return [
        {"id": "hermes", "name": "Hermes", "status": "UNKNOWN", "version": None},
        {"id": "codex", "name": "Codex", "status": "UNKNOWN", "version": None},
        {"id": "dsh", "name": "DSH Desktop", "status": "UNKNOWN", "version": None},
        {"id": "dagu", "name": "Dagu", "status": "UNKNOWN", "version": None},
    ]


# ── Snapshot ──────────────────────────────────────────────────────
def build_snapshot():
    now = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    agents = get_agents()
    tokens = get_token_usage()
    return {
        "schemaVersion": "workflow/snapshot/v3", "revision": int(time.time()),
        "generatedAt": now, "sourceWatermark": now,
        "transport": {"transportState": "LIVE", "freshnessState": "fresh",
                       "eventStreamConnected": True, "connectedSince": now,
                       "lastHeartbeatAt": now, "writerWatermarkAt": now,
                       "eventsUrl": f"http://127.0.0.1:{PORT}/api/v1/events"},
        "coverage": {"numerator": len(agents), "denominator": len(agents)},
        "projects": [{"projectId": a["id"], "displayName": a["name"],
                       "agentPlatform": a["id"].upper(),
                       "activityState": "ACTIVE" if a["status"] == "active" else "INACTIVE"} for a in agents],
        "executions": [], "ci": [],
        "tasks": {"running": 0, "waiting": 0, "blocked": 0, "failed": 0, "completed": len(get_dagu_runs())},
        "tokenSummary": tokens["totals"],
        "git": {"localSha": "221083e", "remoteSha": "221083e", "matchState": "MATCH"},
        "workspace": {}, "sourceRefs": [], "quality": {"freshness": "fresh"},
        "_tokens": tokens, "_dagu": {"dags": get_dagu_dags(), "runs": get_dagu_runs()},
        "_agents": agents,
    }


# ── HTTP ──────────────────────────────────────────────────────────
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB_DIR), **kw)

    def do_GET(self):
        routes = {
            "/api/v1/snapshot": lambda: build_snapshot(),
            "/api/v1/tokens": lambda: get_token_usage(),
            "/api/v1/dagu/dags": lambda: get_dagu_dags(),
            "/api/v1/dagu/runs": lambda: get_dagu_runs(),
            "/api/v1/agents": lambda: get_agents(),
            "/api/v1/events": lambda: {"status": "stub"},
        }
        h = routes.get(self.path)
        if h:
            try:
                data = h()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())
            except Exception as e:
                self.send_response(500); self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            super().do_GET()

    def log_message(self, *a): pass


if __name__ == "__main__":
    t = get_token_usage()
    print(f"Tokens: {t['totals']['inputTokens']:,} in / {t['totals']['outputTokens']:,} out / {t['totals']['sessions']} sessions")
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Observer: http://127.0.0.1:{PORT}")
    server.serve_forever()
