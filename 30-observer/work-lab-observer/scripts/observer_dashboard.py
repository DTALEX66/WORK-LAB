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
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#0b1020; color:#e7ecff; }}
body {{ margin:0; background:radial-gradient(circle at 15% 0%,#182653 0,#0b1020 48%); min-height:100vh; }}
main {{ max-width:1180px; margin:0 auto; padding:32px 20px 56px; }}
header {{ display:flex; justify-content:space-between; align-items:flex-end; gap:20px; margin-bottom:24px; }}
h1 {{ margin:0; font-size:30px; letter-spacing:.02em; }}
.subtitle {{ color:#9ba9d8; margin-top:8px; }}
.badge {{ border:1px solid #3f6f65; color:#9bf0c5; padding:7px 11px; border-radius:999px; font-size:12px; }}
.grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }}
.card {{ background:#121a31; border:1px solid #27345d; border-radius:14px; padding:18px; box-shadow:0 10px 32px #05091466; }}
.label {{ color:#91a0ce; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
.value {{ font-size:26px; font-weight:700; margin-top:8px; }}
section {{ margin-top:22px; }}
h2 {{ font-size:18px; margin:0 0 12px; }}
table {{ width:100%; border-collapse:collapse; }}
th,td {{ text-align:left; padding:12px 10px; border-bottom:1px solid #27345d; }}
th {{ color:#91a0ce; font-size:12px; }}
.note {{ color:#aeb9dd; line-height:1.6; }}
.empty {{ color:#91a0ce; padding:16px 0; }}
@media(max-width:760px) {{ .grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} header {{ display:block; }} .badge {{ display:inline-block; margin-top:14px; }} }}
</style>
</head>
<body>
<main>
<header><div><h1>WORK-LAB Observer</h1><div class="subtitle">只读任务、证据、质量与 usage projection</div></div><div class="badge">EXTERNAL MUTATION: FALSE</div></header>
<div class="grid">
<div class="card"><div class="label">Tasks</div><div class="value">{html.escape(str(overview.get("taskCount", 0)))}</div></div>
<div class="card"><div class="label">Events</div><div class="value">{html.escape(str(overview.get("eventCount", 0)))}</div></div>
<div class="card"><div class="label">Quality</div><div class="value">{html.escape(str(quality.get("quality", "unknown")))}</div></div>
<div class="card"><div class="label">Coverage</div><div class="value">{html.escape(str(overview.get("coverage", "unknown")))}</div></div>
</div>
<section class="card"><h2>Task projection</h2><table><thead><tr><th>Task</th><th>Events</th><th>Last event</th><th>Quality</th><th>Observed</th></tr></thead><tbody id="tasks"><tr><td colspan="5" class="empty">Loading…</td></tr></tbody></table></section>
<section class="card"><h2>Data quality</h2><p class="note">Partial events: {html.escape(str(data_quality.get("partialEvents", 0)))} · Unknown events: {html.escape(str(data_quality.get("unknownEvents", 0)))} · Last source-exact: {html.escape(str(data_quality.get("lastGood", "unknown")))}</p><p class="note">该入口只提供 GET 页面和 GET JSON projection；不执行任务、不批准动作、不写回 Ledger。</p></section>
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
