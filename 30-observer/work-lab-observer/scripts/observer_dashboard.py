from __future__ import annotations

import argparse
import html
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlsplit, parse_qs

# DEPRECATED / DEBUG-COMPAT ONLY (WL3-605)
# The single official Observer UI is web/ + Tauri. This Python server-rendered
# dashboard is retained as a debugging compatibility entry point only; it is
# not a second rendering implementation and must not be developed further.

# The documented root-level command executes this file directly, so bind the
# module's src directory explicitly instead of relying on test-only sys.path setup.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from observer_store import ObserverStore


MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]

VIEWS = ("full", "compact")
THEMES = ("dark", "light")


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    candidate = host.strip().strip("[]").lower()
    if candidate == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def _allowed_origin(origin: str) -> bool:
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError:
        return False
    browser_loopback = (
        parsed.scheme in {"http", "https"}
        and _is_loopback_host(parsed.hostname)
    )
    tauri_local = (
        (parsed.scheme == "tauri" and parsed.hostname == "localhost")
        or (parsed.scheme == "http" and parsed.hostname == "tauri.localhost")
    )
    return (
        (browser_loopback or tauri_local)
        and parsed.username is None
        and parsed.password is None
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
    )


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return ctypes.get_last_error() == 5
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _transport_projection(endpoint_path: Path | None) -> dict[str, Any]:
    offline = {"state": "offline", "source": "workflow-sidecar", "eventsUrl": None, "reconnectMs": 2000}
    if endpoint_path is None or not endpoint_path.is_file():
        return offline
    try:
        endpoint = json.loads(endpoint_path.read_text(encoding="utf-8"))
        events_url = endpoint.get("eventsUrl")
        parsed = urlsplit(events_url)
        if (
            endpoint.get("schemaVersion") != "workflow/sidecar-endpoint/v1"
            or not isinstance(endpoint.get("pid"), int)
            or not _pid_alive(endpoint["pid"])
            or parsed.scheme != "http"
            or not _is_loopback_host(parsed.hostname)
            or parsed.path != "/api/v1/events"
        ):
            return offline
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return offline
    return {"state": "discovered", "source": "workflow-sidecar", "eventsUrl": events_url, "reconnectMs": 2000}


def _json_for_script(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")


def _freshness_state(freshness: str) -> str:
    """Map canonical mode vocabulary (LIVE/STALE/SNAPSHOT/...) onto the
    dashboard freshness vocabulary (fresh/stale/offline/unknown) so the
    server-rendered views and the SSE fixture agree."""
    return {
        "LIVE": "fresh",
        "STALE": "stale",
        "SNAPSHOT": "stale",
        "FIXTURE": "stale",
        "OFFLINE": "offline",
        "UNKNOWN": "unknown",
    }.get(str(freshness).upper(), str(freshness).lower())


def _quality_tone(quality: str) -> str:
    return {
        "source-exact": "#10b981",
        "fresh": "#10b981",
        "partial": "#f5b544",
        "delayed": "#f5b544",
        "stale": "#f5b544",
        "offline": "#8a8f98",
        "unknown": "#8a8f98",
    }.get(quality, "#8a8f98")


def _quality_cn(quality: str) -> str:
    return {
        "source-exact": "来源精确",
        "fresh": "实时",
        "partial": "部分",
        "delayed": "延迟",
        "stale": "滞后",
        "deduplicated": "去重",
        "offline": "离线",
        "unknown": "未知",
    }.get(quality, quality)


def _coverage_pill(coverage: str) -> str:
    if coverage == "full":
        return '<span class="pill pill-ok">全覆盖</span>'
    if coverage == "partial":
        return '<span class="pill pill-warn">部分</span>'
    return '<span class="pill pill-muted">未知</span>'


# Design Tokens — single source, shared by all four views. Theme flips via .theme.
_TOKENS = """
:root, .theme-dark {
  --bg:#08090a; --bg2:#0d0e12; --text:#f7f8f8; --text2:#d0d6e0; --muted:#8a8f98; --dim:#62666d;
  --card:rgba(255,255,255,.025); --card-border:rgba(255,255,255,.08); --line:rgba(255,255,255,.06);
  --accent:#5e6ad2; --accent-bright:#7170ff; --ok:#10b981; --warn:#f5b544;
  --glass:rgba(8,9,10,.72); --glass-border:rgba(255,255,255,.06); --shadow:rgba(0,0,0,.2);
  --band-bg:#f5f5f7; --band-text:#1d1d1f; --band-dim:rgba(0,0,0,.48); --band-note:rgba(0,0,0,.62);
}
.theme-light {
  --bg:#f5f5f7; --bg2:#ffffff; --text:#1d1d1f; --text2:#3a3d42; --muted:#62666d; --dim:#8a8f98;
  --card:#ffffff; --card-border:rgba(0,0,0,.1); --line:rgba(0,0,0,.08);
  --accent:#5e6ad2; --accent-bright:#7170ff; --ok:#0d9b6e; --warn:#b97e1a;
  --glass:rgba(255,255,255,.7); --glass-border:rgba(0,0,0,.08); --shadow:rgba(0,0,0,.12);
  --band-bg:#0d0e12; --band-text:#f7f8f8; --band-dim:#8a8f98; --band-note:#aeb6c9;
}
"""

_CSS = """
* { box-sizing:border-box; margin:0; padding:0; }
html, body { background:var(--bg); color:var(--text); }
body { font-family:system-ui,-apple-system,"SF Pro Text","Segoe UI",sans-serif; font-feature-settings:"cv01","ss03"; -webkit-font-smoothing:antialiased; min-height:100vh; }
::selection { background:color-mix(in srgb, var(--accent-bright) 28%, transparent); }
a { color:var(--accent-bright); text-decoration:none; }
/* Apple glass navigation */
.nav { height:56px; display:flex; align-items:center; justify-content:space-between; padding:0 clamp(14px,3vw,32px); position:sticky; top:0; z-index:10; background:var(--glass); backdrop-filter:saturate(180%) blur(20px); -webkit-backdrop-filter:saturate(180%) blur(20px); box-shadow:0 1px 0 var(--glass-border); }
.brand { display:flex; align-items:center; gap:11px; }
.brand-mark { width:24px; height:24px; border-radius:7px; display:grid; place-items:center; background:linear-gradient(135deg,var(--accent),var(--accent-bright)); color:#fff; font:700 12px/1 system-ui; box-shadow:0 0 0 1px var(--glass-border),0 4px 14px color-mix(in srgb, var(--accent-bright) 35%, transparent); }
.brand-name { font-size:13.5px; font-weight:590; letter-spacing:-.01em; }
.brand-sub { font:500 10px/1 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--dim); letter-spacing:.14em; text-transform:uppercase; margin-top:3px; }
.nav-right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.nav-chip { font:500 10.5px/1 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.1em; text-transform:uppercase; color:var(--text2); background:var(--card); border:1px solid var(--card-border); padding:7px 11px; border-radius:999px; }
.nav-chip.ok { color:var(--ok); border-color:color-mix(in srgb, var(--ok) 30%, transparent); background:color-mix(in srgb, var(--ok) 8%, transparent); }
.nav-link { font:500 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); padding:7px 11px; border-radius:999px; }
.nav-link:hover { background:var(--card); }
.nav-link.active { color:var(--accent-bright); background:color-mix(in srgb, var(--accent-bright) 8%, transparent); }
/* hero */
.hero { max-width:1180px; margin:0 auto; padding:clamp(40px,7vw,80px) clamp(14px,3vw,32px) 32px; }
.eyebrow { color:var(--accent-bright); font:500 11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.18em; text-transform:uppercase; }
h1 { margin:16px 0 0; font-size:clamp(34px,5.5vw,56px); line-height:.98; letter-spacing:-.035em; font-weight:590; }
.hero-line { display:block; }
.hero-sub { color:var(--muted); margin-top:18px; max-width:620px; font-size:16px; line-height:1.6; letter-spacing:-.011em; }
.hero-meta { display:flex; align-items:center; gap:10px; margin-top:22px; flex-wrap:wrap; }
.meta-pill { font:500 11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.08em; text-transform:uppercase; color:var(--text2); background:var(--card); border:1px solid var(--card-border); padding:8px 13px; border-radius:999px; }
.meta-pill.accent { color:var(--accent-bright); border-color:color-mix(in srgb, var(--accent-bright) 35%, transparent); background:color-mix(in srgb, var(--accent-bright) 8%, transparent); }
/* metrics */
.metrics { max-width:1180px; margin:0 auto; padding:0 clamp(14px,3vw,32px); display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
.metric { position:relative; background:var(--card); border:1px solid var(--card-border); border-radius:12px; padding:20px 18px; overflow:hidden; }
.metric::after { content:""; position:absolute; inset:0 0 auto 0; height:1px; background:linear-gradient(90deg,transparent,var(--line),transparent); }
.m-label { font:510 10.5px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.13em; text-transform:uppercase; color:var(--dim); }
.m-value { font-size:32px; line-height:1.1; letter-spacing:-.02em; font-weight:590; margin-top:10px; font-feature-settings:"tnum"; }
.m-sub { font:500 11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--muted); margin-top:6px; letter-spacing:.03em; }
/* panels */
.panels { max-width:1180px; margin:0 auto; padding:22px clamp(14px,3vw,32px) 0; display:grid; grid-template-columns:minmax(0,1.7fr) minmax(0,1fr); gap:12px; align-items:start; }
.panel { background:var(--card); border:1px solid var(--card-border); border-radius:12px; overflow:hidden; }
.panel-head { display:flex; align-items:center; justify-content:space-between; padding:16px 18px 13px; border-bottom:1px solid var(--line); }
.panel-title { font:510 14.5px/1.3 system-ui; letter-spacing:-.01em; }
.panel-title .mono { color:var(--dim); font-size:11px; margin-left:8px; letter-spacing:.08em; }
.panel-body { padding:4px 0 0; }
table { width:100%; border-collapse:collapse; }
th { font:510 10px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.11em; text-transform:uppercase; color:var(--dim); text-align:left; padding:11px 18px; border-bottom:1px solid var(--line); }
td { padding:12px 18px; border-bottom:1px solid var(--line); color:var(--text2); font-size:13px; }
tbody tr:last-child td { border-bottom:none; }
tbody tr:hover { background:var(--card); }
td.num { font-feature-settings:"tnum"; font-weight:550; }
.mono { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; }
.muted { color:var(--dim); }
.empty { color:var(--dim); text-align:center; padding:26px 18px; font:400 13px/1.6 system-ui; }
.stat-row { display:flex; justify-content:space-between; align-items:center; padding:13px 18px; border-bottom:1px solid var(--line); }
.stat-row:last-child { border-bottom:none; }
.stat-k { font:510 12px/1.4 system-ui; color:var(--text2); }
.stat-v { font:500 12px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--text); font-feature-settings:"tnum"; }
.pill { font:600 9.5px/1 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.1em; padding:5px 9px; border-radius:999px; }
.pill-ok { color:var(--ok); background:color-mix(in srgb, var(--ok) 10%, transparent); border:1px solid color-mix(in srgb, var(--ok) 30%, transparent); }
.pill-warn { color:var(--warn); background:color-mix(in srgb, var(--warn) 10%, transparent); border:1px solid color-mix(in srgb, var(--warn) 30%, transparent); }
.pill-muted { color:var(--muted); background:var(--card); border:1px solid var(--card-border); }
/* band */
.band { max-width:1180px; margin:14px auto 0; padding:0 clamp(14px,3vw,32px); }
.band-inner { background:var(--band-bg); color:var(--band-text); border-radius:14px; padding:24px 26px; box-shadow:var(--shadow) 3px 5px 30px 0; }
.band-inner h3 { font-size:14.5px; font-weight:600; letter-spacing:-.01em; margin-bottom:13px; }
.band-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
.band-k { font:600 10.5px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.11em; text-transform:uppercase; color:var(--band-dim); }
.band-v { font-size:22px; font-weight:600; letter-spacing:-.01em; margin-top:6px; font-feature-settings:"tnum"; }
.band-note { color:var(--band-note); font-size:12.5px; line-height:1.6; margin-top:14px; border-top:1px solid var(--band-note); padding-top:12px; }
/* footer */
.footer { max-width:1180px; margin:0 auto; padding:30px clamp(14px,3vw,32px) 52px; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; border-top:1px solid var(--line); }
.footer-left { font:500 11px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--dim); letter-spacing:.03em; }
.footer-right { display:flex; gap:8px; flex-wrap:wrap; }
/* Compact view overrides */
body.compact .nav { height:48px; }
body.compact .brand-sub, body.compact .nav-link { display:none; }
body.compact .hero { padding-top:28px; }
body.compact h1 { font-size:30px; }
body.compact .hero-sub { font-size:13.5px; }
body.compact .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px; }
body.compact .metric { padding:14px 13px; }
body.compact .m-value { font-size:24px; }
body.compact .m-sub { font-size:10px; }
body.compact .panels { grid-template-columns:minmax(0,1fr); gap:10px; }
body.compact .band-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
body.compact .band { display:none; }
body.compact .footer { padding:22px 14px 36px; }
@media (max-width:960px) { .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } .panels { grid-template-columns:minmax(0,1fr); } .band-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:560px) { .metrics { grid-template-columns:minmax(0,1fr); } .band-grid { grid-template-columns:minmax(0,1fr); } .brand-sub, .nav-link { display:none; } }
@media (prefers-reduced-motion: reduce) { * { transition:none !important; animation:none !important; } }
"""


def _nav(theme: str, view: str) -> str:
    other_theme = "light" if theme == "dark" else "dark"
    other_view = "compact" if view == "full" else "full"
    return f"""<nav class="nav">
  <div class="brand"><div class="brand-mark">W</div><div>
    <div class="brand-name">WORK-LAB</div><div class="brand-sub">观测台 · 可观测性</div>
  </div></div>
  <div class="nav-right">
    <span class="nav-chip ok">● 只读</span>
    <a class="nav-link" href="?view={other_view}&theme={theme}">{'紧凑' if view=='full' else '完整'}</a>
    <a class="nav-link" href="?view={view}&theme={other_theme}">{'浅色' if theme=='dark' else '深色'}</a>
  </div>
</nav>"""


def _render_full(projection: dict[str, Any]) -> str:
    summary = projection.get("summary", {})
    quality = projection.get("quality", {})
    usage = projection.get("usage", {})
    ci = projection.get("ci", {})
    projects = projection.get("projects", [])
    tasks = summary.get("tasks", {})
    task_count = sum(tasks.values()) if isinstance(tasks, dict) else 0
    event_count = int(quality.get("telemetryEvents") or 0)
    q = _freshness_state(str(quality.get("freshness", "unknown")))
    coverage = "full" if quality.get("integrity") == "ok" else "partial"
    quality_tone = _quality_tone(q)
    last_good = q

    project_rows = ""
    if projects:
        for p in projects:
            state = str(p.get("state") or p.get("status") or "unknown")
            project_rows += (
                "<tr>"
                f'<td>{html.escape(str(p.get("displayName") or p.get("projectId")))}</td>'
                f'<td><span class="pill {_state_pill(state)}">{html.escape(state)}</span></td>'
                f'<td class="mono muted">{html.escape(str(p.get("projectId")))}</td>'
                "</tr>"
            )
    else:
        project_rows = '<tr><td colspan="3" class="empty">暂无已注册项目 · 等待 workspace discovery</td></tr>'

    usage_rows = ""
    input_tokens = usage.get("inputTokens")
    output_tokens = usage.get("outputTokens")
    total_tokens = usage.get("totalTokens")
    series_count = len(usage.get("series") or [])

    return f"""
<header class="hero">
  <div class="eyebrow">WORK-LAB / 可观测性 / 观测台</div>
  <h1><span class="hero-line">看见工作。</span><span class="hero-line">守住边界。</span></h1>
  <p class="hero-sub">只读的任务、证据、质量与用量投影。页面从观测台自有事件库重建 —— 不执行、不批准、不写回，观测层绝不越权。</p>
  <div class="hero-meta">
    <span class="meta-pill accent">外部变更：false</span>
    <span class="meta-pill">仅 GET · 四视图共用同一投影</span>
  </div>
</header>

<div class="metrics">
  <div class="metric"><div class="m-label">任务</div><div class="m-value">{html.escape(str(task_count))}</div><div class="m-sub">已跟踪投影</div></div>
  <div class="metric"><div class="m-label">事件</div><div class="m-value">{html.escape(str(event_count))}</div><div class="m-sub">已接收观测事件</div></div>
  <div class="metric"><div class="m-label">质量</div><div class="m-value" style="color:{quality_tone}">{html.escape(_quality_cn(q))}</div><div class="m-sub">整体证据质量</div></div>
  <div class="metric"><div class="m-label">覆盖率</div><div class="m-value">{html.escape(coverage)}</div><div class="m-sub">最近良好 · <span class="mono">{html.escape(last_good)}</span></div></div>
</div>

<div class="panels">
  <section class="panel">
    <div class="panel-head"><span class="panel-title">项目投影<span class="mono">canonical</span></span></div>
    <div class="panel-body">
      <table><thead><tr><th>项目</th><th>状态</th><th>ID</th></tr></thead>
      <tbody>{project_rows}</tbody></table>
    </div>
  </section>
  <section class="panel">
    <div class="panel-head"><span class="panel-title">用量与成本<span class="mono">离线估算</span></span></div>
    <div class="panel-body">
      <table><thead><tr><th>指标</th><th>值</th></tr></thead>
      <tbody>
        <tr><td>输入 Token</td><td class="num">{html.escape(str(input_tokens if input_tokens is not None else 0))}</td></tr>
        <tr><td>输出 Token</td><td class="num">{html.escape(str(output_tokens if output_tokens is not None else 0))}</td></tr>
        <tr><td>总 Token</td><td class="num">{html.escape(str(total_tokens if total_tokens is not None else 0))}</td></tr>
        <tr><td>趋势点</td><td class="num">{html.escape(str(series_count))}</td></tr>
      </tbody></table>
    </div>
  </section>
</div>

<div class="band-grid">
  <section class="band">
    <div class="band-head"><span class="band-title">数据质量</span></div>
    <div class="band-body">
      <span class="pill {_quality_pill(quality.get('integrity', 'unknown'))}">完整性 {html.escape(str(quality.get("integrity", "unknown")))}</span>
      <span class="pill">事件 {html.escape(str(event_count))}</span>
    </div>
  </section>
  <section class="band">
    <div class="band-head"><span class="band-title">CI</span></div>
    <div class="band-body">
      {''.join(
        f'<span class="pill pill-ok">{html.escape(str(r.get("status")))} · {html.escape(str(r.get("conclusion")))} · {html.escape(str(r.get("runs")))} 次</span>'
        for r in (ci.get("runs") or [])
      ) or '<span class="pill pill-muted">暂无 CI 记录</span>'}
    </div>
  </section>
</div>
"""


def _state_pill(state: str) -> str:
    return {"running": "pill-ok", "blocked": "pill-warn", "failed": "pill-warn", "waiting": "pill-warn"}.get(state, "pill-muted")


def _quality_pill(value: str) -> str:
    return "pill-ok" if value == "ok" else "pill-warn"


def _render_compact(projection: dict[str, Any]) -> str:
    summary = projection.get("summary", {})
    quality = projection.get("quality", {})
    usage = projection.get("usage", {})
    projects = projection.get("projects", [])
    event_count = int(quality.get("telemetryEvents") or 0)
    q = _freshness_state(str(quality.get("freshness", "unknown")))
    q_cn = _quality_cn(q)
    quality_tone = _quality_tone(q)
    last_good = q
    total_tokens = usage.get("totalTokens")

    project_rows = ""
    if projects:
        for p in projects[:6]:
            state = str(p.get("state") or p.get("status") or "unknown")
            project_rows += (
                "<tr>"
                f'<td>{html.escape(str(p.get("displayName") or p.get("projectId")))}</td>'
                f'<td><span class="pill {_state_pill(state)}">{html.escape(state)}</span></td>'
                "</tr>"
            )
    else:
        project_rows = '<tr><td colspan="2" class="empty">暂无已注册项目</td></tr>'

    # Task count must come from summary.tasks (canonical counts), never from the
    # project list length — projects and tasks are different facts.
    summary_tasks = projection.get("summary", {}).get("tasks", {})
    task_count = sum(summary_tasks.values()) if isinstance(summary_tasks, dict) else len(projects)

    return f"""
<header class="hero">
  <div class="eyebrow">WORK-LAB 观测台</div>
  <h1><span class="hero-line">看见工作。</span><span class="hero-line">守住边界。</span></h1>
  <p class="hero-sub">严格只读 · 跨项目观测</p>
</header>

<div class="metrics">
  <div class="metric"><div class="m-label">项目</div><div class="m-value">{html.escape(str(task_count))}</div><div class="m-sub">已登记投影</div></div>
  <div class="metric"><div class="m-label">事件</div><div class="m-value">{html.escape(str(event_count))}</div><div class="m-sub">已接收</div></div>
  <div class="metric"><div class="m-label">质量</div><div class="m-value" style="color:{quality_tone}">{html.escape(q_cn)}</div><div class="m-sub">整体质量</div></div>
  <div class="metric"><div class="m-label">Token</div><div class="m-value">{html.escape(str(total_tokens if total_tokens is not None else 0))}</div><div class="m-sub">总用量</div></div>
</div>

<div class="panels">
  <section class="panel">
    <div class="panel-head"><span class="panel-title">项目投影<span class="mono">canonical</span></span></div>
    <div class="panel-body">
      <table><thead><tr><th>项目</th><th>状态</th></tr></thead>
      <tbody>{project_rows}</tbody></table>
    </div>
  </section>
  <section class="panel">
    <div class="panel-head"><span class="panel-title">用量<span class="mono">离线</span></span></div>
    <div class="panel-body">
      <div class="stat-row"><span class="stat-k">输入</span><span class="stat-v">{html.escape(str(usage.get("inputTokens") or 0))}</span></div>
      <div class="stat-row"><span class="stat-k">输出</span><span class="stat-v">{html.escape(str(usage.get("outputTokens") or 0))}</span></div>
      <div class="stat-row"><span class="stat-k">总 Token</span><span class="stat-v">{html.escape(str(total_tokens if total_tokens is not None else 0))}</span></div>
      <div class="stat-row"><span class="stat-k">最近观测</span><span class="stat-v mono muted">{html.escape(last_good)}</span></div>
    </div>
  </section>
</div>
"""


def _render_dashboard(projection: dict[str, Any], *, view: str = "full", theme: str = "dark") -> str:
    if view not in VIEWS:
        view = "full"
    if theme not in THEMES:
        theme = "dark"
    body = _render_full(projection) if view == "full" else _render_compact(projection)
    payload = _json_for_script(projection)
    # color-scheme for native scrollbars/inputs
    scheme = "dark" if theme == "dark" else "light"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WORK-LAB Observer · {view} · {theme}</title>
<style>:root {{ color-scheme:{scheme}; }} {_TOKENS} {_CSS}</style>
</head>
<body class="theme-{theme} {view}">
{_nav(theme, view)}
{body}
<footer class="footer">
  <div class="footer-left">WORK-LAB 观测台 · 严格只读投影 · 外部变更：{html.escape(str(projection.get("mutationSurface", {}).get("externalMutation", False)).lower())}</div>
  <div class="footer-right"><span class="pill pill-muted">{view} / {theme}</span><span class="pill pill-muted">GET /</span><span class="pill pill-muted">/api/dashboard</span><span class="pill pill-muted">/healthz</span></div>
</footer>
<script id="dashboard-data" type="application/json">{payload}</script>
</body>
</html>"""


def make_handler(store: ObserverStore, endpoint_path: Path | None = None):
    class ObserverDashboardHandler(BaseHTTPRequestHandler):
        server_version = "WORK-LAB-Observer/1"

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            origin = self.headers.get("Origin")
            if origin and _allowed_origin(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        def _send_405(self) -> None:
            self._send(405, "application/json; charset=utf-8", b'{"status":"method_not_allowed"}')

        def do_GET(self) -> None:  # noqa: N802
            origin = self.headers.get("Origin")
            if origin and not _allowed_origin(origin):
                self._send(403, "application/json; charset=utf-8", b'{"status":"origin_not_allowed"}')
                return
            parsed = urlsplit(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            view = (query.get("view") or ["full"])[0]
            theme = (query.get("theme") or ["dark"])[0]
            try:
                projection = store.rebuild_projection()
                transport = _transport_projection(endpoint_path)
                projection = {
                    **projection,
                    "mode": "LIVE" if transport["state"] == "discovered" else projection.get("mode", "SNAPSHOT"),
                    "transport": transport,
                }
            except Exception as exc:  # fail closed without exposing event contents
                self._send(500, "application/json; charset=utf-8", json.dumps({"status": "observer_error", "error": type(exc).__name__}).encode())
                return
            if path == "/":
                self._send(200, "text/html; charset=utf-8", _render_dashboard(projection, view=view, theme=theme).encode("utf-8"))
            elif path == "/api/dashboard":
                self._send(200, "application/json; charset=utf-8", json.dumps(projection, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/api/projects":
                projects = projection.get("projects", [])
                self._send(200, "application/json; charset=utf-8", json.dumps({"count": len(projects), "projects": projects}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/api/tasks":
                tasks = projection.get("summary", {}).get("tasks", {})
                self._send(200, "application/json; charset=utf-8", json.dumps({"tasks": tasks}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/api/usage":
                self._send(200, "application/json; charset=utf-8", json.dumps({"usage": projection.get("usage", {}), "cost": projection.get("cost", {})}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/api/quality":
                self._send(200, "application/json; charset=utf-8", json.dumps({"quality": projection.get("quality", {}), "dataQuality": projection.get("dataQuality", {})}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/api/ci":
                # CI/GitHub status is derived from governance/quality view; no write, no credentials.
                self._send(200, "application/json; charset=utf-8", json.dumps({"status": "read-only-view", "source": "governance", "mutationSurface": projection.get("mutationSurface", {})}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/api/governance":
                self._send(200, "application/json; charset=utf-8", json.dumps({"mutationSurface": projection.get("mutationSurface", {}), "overview": projection.get("overview", {})}, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            elif path == "/healthz":
                self._send(200, "application/json; charset=utf-8", b'{"status":"ok","readOnly":true}')
            else:
                self._send(404, "application/json; charset=utf-8", b'{"status":"not_found"}')

        def do_POST(self) -> None:  # noqa: N802
            self._send_405()

        def do_PUT(self) -> None:  # noqa: N802
            self._send_405()

        def do_PATCH(self) -> None:  # noqa: N802
            self._send_405()

        def do_DELETE(self) -> None:  # noqa: N802
            self._send_405()

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ObserverDashboardHandler


class _ObserverHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, store: ObserverStore) -> None:
        self.store = store
        super().__init__(address, handler)

    def server_close(self) -> None:
        try:
            super().server_close()
        finally:
            self.store.close()


def create_server(project_root: Path, canonical_path: Path, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    if not _is_loopback_host(host):
        raise ValueError("observer host must be loopback-only")
    store = ObserverStore(canonical_path, project_root=project_root)
    endpoint_path = canonical_path.parent / "sidecar-endpoint.json"
    return _ObserverHTTPServer((host, port), make_handler(store, endpoint_path), store)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the read-only WORK-LAB Observer dashboard (4 views)")
    parser.add_argument("--project-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--canonical-store", type=Path)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    canonical_path = (args.canonical_store or project_root / ".hermes" / "task-runtime" / "workflow" / "canonical.sqlite").resolve()
    server = create_server(project_root, canonical_path, args.host, args.port)
    print(
        f"OBSERVER_DASHBOARD_READY url=http://{args.host}:{server.server_port}/ read_only=true views=full,compact themes=dark,light",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
