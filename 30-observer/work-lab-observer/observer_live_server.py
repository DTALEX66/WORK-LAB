#!/usr/bin/env python3
"""WORK-LAB Observer Live Server — real-time data from all 5 agents.

Run: python observer_live_server.py
Serves: http://localhost:9900 (static) + /api/v1/snapshot (live JSON)
Auto-refreshes collectors every 30s.
"""
import json, os, sys, time, threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 61867
WEB_DIR = Path(__file__).parent / "web"
SNAPSHOT_PATH = WEB_DIR / "assets" / "live-snapshot.json"

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tokentelemetry"))
from backend.collectors.dagu_collector import scan_dag_runs, emit_tokentelemetry_event as dagu_emit
from backend.collectors.github_collector import collect_actions_usage, collect_rate_limit, emit_tokentelemetry_event as gh_emit


def build_snapshot():
    """Build a live snapshot from all collectors."""
    dagu_events = [dagu_emit(e) for e in scan_dag_runs()]
    gh_events = [gh_emit(e) for e in collect_actions_usage("DTALEX66/WORK-LAB")]
    rl = collect_rate_limit()
    if rl: gh_events.append(gh_emit(rl))

    snapshot = {
        "schemaVersion": "work-lab/observer-projection/v2",
        "mode": "LIVE",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "summary": {
            "registeredProjects": 5, "activeProjects": 5,
            "daguRuns": len(dagu_events),
            "githubActions": len([e for e in gh_events if (e.get("model") or "").startswith("github-actions")]),
            "agentCoverage": ["hermes", "codex", "dsh", "dagu", "github"],
        },
        "projects": []
    }

    for e in dagu_events:
        snapshot["projects"].append({
            "projectId": f"dagu-{(e.get('metadata') or {}).get('dag_name','?')}",
            "displayName": f"Dagu: {(e.get('metadata') or {}).get('dag_name','?')}",
            "agentPlatform": "DAGU",
            "task": f"DAG ({(e.get('metadata') or {}).get('step_count',0)} steps)",
            "state": e.get("outcome", "unknown"),
            "quality": {"evidenceCompleteness": "complete", "dataQuality": "exact", "freshness": "fresh"},
        })

    for e in gh_events:
        m = e.get("metadata") or {}
        if (e.get("model") or "").startswith("github-actions"):
            snapshot["projects"].append({
                "projectId": f"gh-run-{e.get('sessionId','?')}",
                "displayName": f"GitHub: {m.get('workflow','?')}",
                "agentPlatform": "GITHUB",
                "task": m.get("workflow", "Actions"),
                "state": e.get("outcome", "unknown"),
                "branch": m.get("branch"),
                "quality": {"evidenceCompleteness": "complete", "dataQuality": "exact", "freshness": "fresh"},
            })

    # Keep Hermes/Codex/DSH entries if they exist in existing snapshot
    if SNAPSHOT_PATH.exists():
        try:
            old = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
            for p in old.get("projects", []):
                if p.get("agentPlatform") in ("HERMES", "CODEX", "DSH"):
                    snapshot["projects"].append(p)
        except Exception:
            pass

    return snapshot


def refresh_loop():
    """Background thread: refresh snapshot every 30s."""
    while True:
        try:
            snap = build_snapshot()
            SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            SNAPSHOT_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[refresh] error: {e}")
        time.sleep(30)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/v1/snapshot":
            try:
                snap = build_snapshot()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(snap, ensure_ascii=False).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress request logs


if __name__ == "__main__":
    # Initial snapshot
    print("Building initial snapshot...")
    snap = build_snapshot()
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Snapshot: {len(snap.get('projects',[]))} agents")

    # Start refresh thread
    t = threading.Thread(target=refresh_loop, daemon=True)
    t.start()

    # Start server
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Observer Live: http://127.0.0.1:{PORT}")
    print(f"API endpoint: http://127.0.0.1:{PORT}/api/v1/snapshot")
    print("Auto-refresh every 30s. Ctrl+C to stop.")
    server.serve_forever()
