from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit

# The documented root-level command executes this file directly, so bind the
# module's src directory explicitly instead of relying on test-only sys.path setup.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from observer_store import ObserverStore


MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")


def _render_dashboard(projection: dict[str, Any]) -> str:
    overview = projection.get("overview", {})
    quality = projection.get("quality", {})
    data_quality = projection.get("dataQuality", {})
    payload = _json_for_script(projection)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WORK-LAB Observer</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; background:#08090a; color:#f7f8f8; font-feature-settings:"cv01","ss03"; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#08090a; min-height:100vh; }}
.nav {{ height:52px; display:flex; align-items:center; justify-content:space-between; padding:0 28px; position:sticky; top:0; z-index:2; background:rgba(0,0,0,.78); backdrop-filter:saturate(180%) blur(20px); box-shadow:0 1px 0 rgba(255,255,255,.08); }}
.brand {{ display:flex; align-items:center; gap:10px; font-size:13px; font-weight:590; letter-spacing:-.13px; }}
.brand-mark {{ width:20px; height:20px; border-radius:6px; display:grid; place-items:center; background:#5e6ad2; color:#fff; font-size:11px; font-weight:700; }}
.nav-meta {{ color:#8a8f98; font:12px ui-monospace,SFMono-Regular,Menlo,monospace; }}
main {{ max-width:1200px; margin:0 auto; padding:72px 28px 96px; }}
.hero {{ display:flex; justify-content:space-between; align-items:flex-end; gap:28px; margin-bottom:48px; }}
.eyebrow {{ color:#7170ff; font:500 11px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.08em; text-transform:uppercase; }}
h1 {{ margin:12px 0 0; font-size:52px; line-height:1; letter-spacing:-1.5px; font-weight:590; }}
.subtitle {{ color:#8a8f98; margin-top:16px; max-width:580px; font-size:17px; line-height:1.6; letter-spacing:-.16px; }}
.badge {{ display:inline-flex; align-items:center; gap:8px; border:1px solid rgba(255,255,255,.08); color:#d0d6e0; background:rgba(255,255,255,.03); padding:8px 12px; border-radius:9999px; font:510 12px/1.4 system-ui,sans-serif; white-space:nowrap; }}
.badge::before {{ content:""; width:7px; height:7px; border-radius:50%; background:#10b981; box-shadow:0 0 0 3px rgba(16,185,129,.12); }}
.grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
.card {{ background:rgba(255,255,255,.025); border:1px solid rgba(255,255,255,.08); border-radius:10px; padding:20px; box-shadow:0 0 0 1px rgba(0,0,0,.2); }}
.metric {{ min-height:132px; display:flex; flex-direction:column; justify-content:space-between; }}
.label {{ color:#8a8f98; font:510 11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.06em; text-transform:uppercase; }}
.value {{ font-size:30px; line-height:1; letter-spacing:-.7px; font-weight:590; }}
section {{ margin-top:20px; }}
h2 {{ font-size:20px; line-height:1.33; letter-spacing:-.24px; font-weight:590; margin:0 0 18px; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ text-align:left; padding:14px 10px; border-bottom:1px solid rgba(255,255,255,.06); }}
th {{ color:#62666d; font:510 11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.05em; text-transform:uppercase; }}
td {{ color:#d0d6e0; font-size:14px; }}
tbody tr:hover {{ background:rgba(255,255,255,.025); }}
.note {{ color:#8a8f98; line-height:1.6; font-size:15px; }}
.empty {{ color:#62666d; padding:24px 10px; }}
.quality-panel {{ background:#f5f5f7; color:#1d1d1f; border:0; box-shadow:rgba(0,0,0,.22) 3px 5px 30px 0; }}
.quality-panel h2 {{ color:#1d1d1f; }}
.quality-panel .note {{ color:rgba(0,0,0,.62); }}
@media(max-width:760px) {{ main {{ padding:48px 16px 64px; }} .nav {{ padding:0 16px; }} .hero {{ display:block; }} h1 {{ font-size:40px; }} .badge {{ margin-top:24px; }} .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} table {{ min-width:680px; }} section.card {{ overflow:auto; }} }}
</style>
</head>
<body>
<nav class="nav"><div class="brand"><span class="brand-mark">W</span><span>WORK-LAB Observer</span></div><span class="nav-meta">READ-ONLY / LOCAL PROJECTION</span></nav>
<main>
<header class="hero"><div><div class="eyebrow">WORK-LAB / OBSERVABILITY</div><h1>See the work.<br>Keep the boundary.</h1><div class="subtitle">只读任务、证据、质量与 usage projection。页面从 Observer-owned event store 重建，不执行、不批准、不写回。</div></div><div class="badge">EXTERNAL MUTATION: FALSE</div></header>
<div class="grid">
<div class="card metric"><div class="label">Tasks</div><div class="value">{html.escape(str(overview.get("taskCount", 0)))}</div></div>
<div class="card metric"><div class="label">Events</div><div class="value">{html.escape(str(overview.get("eventCount", 0)))}</div></div>
<div class="card metric"><div class="label">Quality</div><div class="value">{html.escape(str(quality.get("quality", "unknown")))}</div></div>
<div class="card metric"><div class="label">Coverage</div><div class="value">{html.escape(str(overview.get("coverage", "unknown")))}</div></div>
</div>
<section class="card"><h2>Task projection</h2><table><thead><tr><th>Task</th><th>Events</th><th>Last event</th><th>Quality</th><th>Observed</th></tr></thead><tbody id="tasks"><tr><td colspan="5" class="empty">Loading…</td></tr></tbody></table></section>
<section class="card quality-panel"><h2>Data quality</h2><p class="note">Partial events: {html.escape(str(data_quality.get("partialEvents", 0)))} · Unknown events: {html.escape(str(data_quality.get("unknownEvents", 0)))} · Last source-exact: {html.escape(str(data_quality.get("lastGood", "unknown")))}</p><p class="note">该入口只提供 GET 页面和 GET JSON projection；不执行任务、不批准动作、不写回 Ledger。</p></section>
<script id="dashboard-data" type="application/json">{payload}</script>
<script>
const projection = JSON.parse(document.getElementById('dashboard-data').textContent);
const rows = Object.values(projection.tasks || {{}});
const body = document.getElementById('tasks');
body.textContent = '';
if (!rows.length) {{ const row=document.createElement('tr'); const cell=document.createElement('td'); cell.colSpan=5; cell.className='empty'; cell.textContent='暂无观测事件；等待 Workflow Assistance evidence envelope。'; row.appendChild(cell); body.appendChild(row); }}
for (const task of rows) {{ const row=document.createElement('tr'); for (const key of ['taskId','events','lastEventType','quality','observedAt']) {{ const cell=document.createElement('td'); cell.textContent=String(task[key] ?? 'unknown'); row.appendChild(cell); }} body.appendChild(row); }}
</script>
</main>
</body>
</html>"""


def make_handler(store: ObserverStore):
    class ObserverDashboardHandler(BaseHTTPRequestHandler):
        server_version = "WORK-LAB-Observer/1"

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            try:
                projection = store.rebuild_projection()
            except Exception as exc:  # fail closed without exposing event contents
                self._send(500, "application/json; charset=utf-8", json.dumps({"status": "observer_error", "error": type(exc).__name__}).encode())
                return
            if path == "/":
                self._send(200, "text/html; charset=utf-8", _render_dashboard(projection).encode("utf-8"))
            elif path == "/api/dashboard":
                self._send(200, "application/json; charset=utf-8", json.dumps(projection, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/healthz":
                self._send(200, "application/json; charset=utf-8", b'{"status":"ok","readOnly":true}')
            else:
                self._send(404, "application/json; charset=utf-8", b'{"status":"not_found"}')

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ObserverDashboardHandler


def create_server(project_root: Path, runtime_root: Path, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    runtime_root.mkdir(parents=True, exist_ok=True)
    store = ObserverStore(runtime_root, project_root=project_root)
    return ThreadingHTTPServer((host, port), make_handler(store))


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the read-only WORK-LAB Observer dashboard")
    parser.add_argument("--project-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    runtime_root = project_root / ".hermes" / "task-runtime" / "observer"
    server = create_server(project_root, runtime_root, args.host, args.port)
    print(f"OBSERVER_DASHBOARD_READY url=http://{args.host}:{args.port}/ read_only=true")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
