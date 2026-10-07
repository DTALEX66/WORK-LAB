#!/usr/bin/env python
"""Desktop geometry gate — measure the shipped bundle in a real browser and PASS or FAIL.

This instrument existed as a one-off measurement: it printed numbers, returned None, and nothing in
CI or in a test ever referenced it. That is the G3 finding in the UI prompt pack — a geometry probe
that cannot fail is not a gate. It is now a gate with three deliberate properties:

  1. the verdict is a PURE function of the measured geometry, so it is unit-testable without a
     browser, and the assertions are reviewable as text rather than as a screenshot;
  2. the browser is DISCOVERED, never assumed (env WL_CHROME, then PATH, then the vendor default
     install dirs). If none is found the script exits 3 and prints `GEOMETRY_GATE_NOT_RUN
     BROWSER_NOT_FOUND` — a named category, not a silent zero;
  3. the project root is resolved from this file, not hardcoded to the author's machine.

Silent by design: headless Chromium over CDP against the built `dist`, so the numbers come from the
same bundle the release binary embeds, without putting a window on the owner's desktop.

Exit: 0 GEOMETRY_GATE_PASS, 1 GEOMETRY_GATE_FAIL, 2 bad input, 3 GEOMETRY_GATE_NOT_RUN.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import re
import socket
import shutil
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

LISTEN_RE = re.compile(r"DevTools listening on ws://127\.0\.0\.1:(\d+)")

ROOT = Path(__file__).resolve().parents[2]
OBS = ROOT / "apps" / "observer"
DIST = OBS / "frontend" / "dist"
OUT_DIR = ROOT / ".project-local" / "runs" / "geometry-gate"

SELECTORS = [".app", ".topbar", ".search", ".top-actions", ".topbar-brand", ".winctl",
             ".winctl-btn", ".sidebar", ".main", ".kpi-grid", "body"]

# `top-actions` is the control row a user must be able to reach; a rule that hides it below some
# width is exactly the phone behaviour this shell no longer ships.
EXPR = """JSON.stringify((()=>{
  const out = {};
  for (const sel of SELECTORS) {
    const els = [...document.querySelectorAll(sel)];
    if (!els.length) { out[sel] = {absent: true}; continue; }
    out[sel] = els.slice(0,6).map(el=>{
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        left: Math.round(r.left*10)/10, right: Math.round(r.right*10)/10,
        top: Math.round(r.top*10)/10, bottom: Math.round(r.bottom*10)/10,
        width: Math.round(r.width*10)/10, height: Math.round(r.height*10)/10,
        gapToViewportRight: Math.round((innerWidth - r.right)*10)/10,
        display: cs.display,
      };
    });
  }
  out.__viewport = innerWidth + 'x' + innerHeight;
  out.__innerWidth = innerWidth;
  out.__docScrollWidth = document.documentElement.scrollWidth;
  out.__elementsOverlappingRightEdge = [...document.querySelectorAll('body *')]
      .filter(e=>{const r=e.getBoundingClientRect();
        return r.width>0 && r.right > innerWidth - 2 && r.left < innerWidth - 2;})
      .slice(0,12).map(e=>e.tagName+'.'+(typeof e.className==='string'?e.className:'')
        +' right='+Math.round(e.getBoundingClientRect().right));
  return out;
})())"""

TOPBAR_MAX_HEIGHT = 140.0
# The two windows are different surfaces with different sizes, so each is measured at its own
# declared shape: the main window at its default 1280x820, the floating panel at the 440x780
# non-resizable size tauri.conf.json gives it. Measuring the compact layout at desktop width would
# have proved nothing about the panel — the first PASS this script produced did exactly that, and
# the per-view height bound below is what a 440px bar actually needs.
WIN_SIZE = {"full": "1280,820", "compact": "440,780"}
MAX_HEIGHT = {"full": 140.0, "compact": 260.0}
RAIL_MIN_WIDTH = 200.0
RESIDUE: list[str] = []
ANNOUNCED_MISMATCH: list[str] = []


def load_u19():
    """Reuse the CDP client the release line already trusts, rather than a second websocket stack."""
    path = OBS / "scripts" / "u19_webview_e2e.py"
    spec = importlib.util.spec_from_file_location("u19", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def find_browser() -> str | None:
    env = os.environ.get("WL_CHROME") or os.environ.get("CHROME_PATH")
    candidates: list[str | None] = [env] if env else []
    candidates += [shutil.which(name) for name in
                   ("chrome", "chrome.exe", "msedge", "msedge.exe", "chromium", "chromium-browser")]
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")):
        if not base:
            continue
        candidates += [str(Path(base) / "Google/Chrome/Application/chrome.exe"),
                       str(Path(base) / "Microsoft/Edge/Application/msedge.exe")]
    for cand in candidates:
        if cand and Path(cand).is_file():
            return cand
    return None


def _send(ws: socket.socket, payload: bytes) -> None:
    """Client frames must be masked (RFC 6455); no padding, so every length fits 8 or 16 bytes."""
    header = bytearray([0x81])
    n = len(payload)
    if n < 126:
        header.append(0x80 | n)
    else:
        header.append(0x80 | 126)
        header += n.to_bytes(2, "big")
    mask = bytes([0x37, 0x7A, 0x51, 0x29])
    header += mask
    ws.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))


def _recv_text(ws: socket.socket, wanted_id: int, timeout: float) -> str:
    """Read frames until the response for `wanted_id` arrives, skipping event frames."""
    deadline = time.time() + timeout
    buffer = bytearray()

    def one_frame() -> bytes | None:
        nonlocal buffer
        while len(buffer) < 2:
            chunk = ws.recv(4096)
            if not chunk:
                return None
            buffer += chunk
        b1, b2 = buffer[0], buffer[1]
        length = b2 & 0x7F
        offset = 2
        if length == 126:
            while len(buffer) < offset + 2:
                buffer += ws.recv(4096)
            length = int.from_bytes(buffer[offset:offset + 2], "big")
            offset += 2
        elif length == 127:
            while len(buffer) < offset + 8:
                buffer += ws.recv(4096)
            length = int.from_bytes(buffer[offset:offset + 8], "big")
            offset += 8
        while len(buffer) < offset + length:
            buffer += ws.recv(4096)
        payload = bytes(buffer[offset:offset + length])
        del buffer[:offset + length]
        return payload if (b1 & 0x0F) in (0x1, 0x2) else b""

    while time.time() < deadline:
        frame = one_frame()
        if frame is None:
            break
        if not frame:
            continue
        try:
            message = json.loads(frame.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            continue
        if message.get("id") == wanted_id:
            if "error" in message:
                raise RuntimeError(f"CDP error: {message['error']}")
            return json.dumps(message)
    raise RuntimeError(f"no CDP response for id={wanted_id} before {timeout}s")


class ChromeCDP:
    """Minimal CDP-over-WebSocket client for the headless browser this gate drives.

    u19's client targets WebView2 through a proxy and is left alone (changing it would put the
    release line's desktop evidence at risk for a quirk that belongs to Chrome). Chrome 154 stalls
    any DevTools HTTP request without a User-Agent, or with a port in Host — measured side by side
    against one instance — so discovery uses `cdp_list`, and the websocket handshake below sends the
    headers a browser expects.
    """

    def __init__(self, ws_url: str, timeout: float = 60.0) -> None:
        parts = urllib.parse.urlsplit(ws_url)
        host, _, port = parts.netloc.partition(":")
        self.sock = socket.create_connection((host, int(port or 9222)), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        path = parts.path + ("?" + parts.query if parts.query else "")
        request = (f"GET {path} HTTP/1.1\r\nHost: {parts.netloc}\r\nUpgrade: websocket\r\n"
                   f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
                   f"Sec-WebSocket-Version: 13\r\nUser-Agent: worklab-geometry-gate\r\n\r\n")
        self.sock.sendall(request.encode("latin-1"))
        handshake = b""
        while b"\r\n\r\n" not in handshake:
            piece = self.sock.recv(4096)
            if not piece:
                raise RuntimeError("websocket handshake closed")
            handshake += piece
        status = handshake.split(b"\r\n", 1)[0].decode("latin-1", "replace")
        if "101" not in status:
            raise RuntimeError(f"websocket handshake failed: {status}")
        self._id = 0
        self.timeout = timeout

    def send(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        _send(self.sock, json.dumps({"id": self._id, "method": method,
                                     "params": params or {}}).encode("utf-8"))
        return json.loads(_recv_text(self.sock, self._id, self.timeout)).get("result", {})

    def evaluate(self, expression: str) -> str:
        result = self.send("Runtime.evaluate",
                           {"expression": expression, "returnByValue": True, "awaitPromise": True})
        if result.get("exceptionDetails"):
            raise RuntimeError(f"evaluate threw: {json.dumps(result['exceptionDetails'])[:400]}")
        value = result.get("result", {}).get("value")
        if value is None:
            # A missing value is not an empty measurement: report what the debugger did return
            # rather than letting json.loads(None) become the error message.
            raise RuntimeError(f"evaluate produced no value: {json.dumps(result)[:400]}")
        return value

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


def _first(measured: dict, selector: str) -> dict | None:
    value = measured.get(selector)
    if isinstance(value, list) and value:
        return value[0]
    return None


def verdict(measured: dict, view: str) -> dict:
    """Pure: no browser, no filesystem. Every check is one line of the acceptance contract."""
    width = measured.get("__innerWidth") or 0
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    scroll = measured.get("__docScrollWidth") or 0
    add("no_horizontal_overflow", scroll <= width + 1, f"scrollWidth={scroll} innerWidth={width}")

    topbar = _first(measured, ".topbar")
    add("topbar_measured", topbar is not None, "no .topbar element")
    if topbar:
        add("topbar_not_stacked", topbar["height"] <= MAX_HEIGHT[view],
            f"height={topbar['height']} limit={MAX_HEIGHT[view]}")

    brand = _first(measured, ".topbar-brand")
    add("brand_mark_present", bool(brand) and brand["width"] > 0,
        f"brand={brand and brand['width']}")

    actions = _first(measured, ".top-actions")
    add("actions_visible", bool(actions) and actions["display"] != "none",
        f"display={actions and actions['display']}")

    clipped = [e for e in (measured.get(".winctl-btn") or []) if isinstance(e, dict)
               and e.get("gapToViewportRight", 0) < -1]
    add("window_controls_reachable", bool(measured.get(".winctl-btn")) and not clipped,
        f"clipped={json.dumps(clipped, ensure_ascii=False)[:200]}")

    clipped_actions = [e for e in (measured.get(".top-actions") or []) if isinstance(e, dict)
                       and e.get("gapToViewportRight", 0) < -1]
    add("action_row_inside_viewport", not clipped_actions,
        f"gap={measured.get('.top-actions') and measured['.top-actions'][0].get('gapToViewportRight')}")

    rail = _first(measured, ".sidebar")
    if view == "full":
        # The desktop-only contract: the rail is the only navigation surface, so it must exist
        # at every width the main window can take — including a 125%-scaled narrow window.
        add("rail_always_present", bool(rail) and rail["width"] >= RAIL_MIN_WIDTH,
            f"rail={rail and rail['width']} min={RAIL_MIN_WIDTH}")
        add("rail_at_left_edge", bool(rail) and rail["left"] <= 1, f"left={rail and rail['left']}")
    else:
        add("compact_has_no_rail", rail is None, f"rail={rail}")

    return {"view": view, "viewport": measured.get("__viewport"),
            "passed": all(c["pass"] for c in checks), "checks": checks,
            "overlappingRightEdge": measured.get("__elementsOverlappingRightEdge") or []}


def cdp_list(port: int, path: str = "/json/list") -> list[dict]:
    """Chrome 154's DevTools HTTP endpoint stalls a request that carries no User-Agent, or that puts
    a port in Host: the socket accepts and never answers. Measured side by side against one running
    instance — u19's raw GET timed out while the same bytes plus `User-Agent`/`Accept` and a portless
    Host returned HTTP/1.1 200 at once. u19 keeps its own shape because WebView2 is served by it;
    the browser this gate drives is Chrome, so the gate speaks Chrome."""
    s = socket.create_connection(("127.0.0.1", port), timeout=6)
    try:
        s.sendall(f"GET {path} HTTP/1.1\r\nHost: 127.0.0.1\r\nUser-Agent: worklab-geometry-gate\r\n"
                  f"Accept: application/json\r\nConnection: close\r\n\r\n".encode("latin-1"))
        raw = b""
        head = None
        expected = None
        while True:
            piece = s.recv(65536)
            if not piece:
                break
            raw += piece
            if head is None:
                split = raw.find(b"\r\n\r\n")
                if split == -1:
                    continue
                head, body_start = raw[:split], split + 4
                match = re.search(rb"Content-Length:\s*(\d+)", head, re.IGNORECASE)
                expected = int(match.group(1)) if match else None
            if expected is not None and len(raw) - (raw.find(b"\r\n\r\n") + 4) >= expected:
                break
    finally:
        s.close()
    if head is None:
        raise RuntimeError(f"CDP {path}: no response head ({raw[:80]!r})")
    status_line = head.split(b"\r\n", 1)[0].decode("latin-1", "replace")
    parts = status_line.split()
    if len(parts) < 2 or parts[1] != "200":
        raise RuntimeError(f"CDP {path}: HTTP {status_line}")
    body = raw[len(head) + 4:]
    if expected is not None and len(body) < expected:
        # A short read is not a Chrome quirk to tolerate: a JSON document cut mid-list is exactly how
        # a `page` target silently disappears, which is the failure this function used to report.
        raise RuntimeError(f"CDP {path}: truncated body {len(body)} of {expected}")
    return json.loads(body.decode("utf-8", "replace"))


def discover_page_ws(port: int, tries: int = 20) -> str:
    last: Exception | None = None
    seen: list[str] = []
    for _ in range(tries):
        try:
            targets = cdp_list(port)
        except Exception as exc:  # noqa: BLE001 — retried, but the last reason is always reported
            last = exc
            time.sleep(0.5)
            continue
        seen = [f"{t.get('type')}:{(t.get('url') or '')[:40]}" for t in targets]
        for target in targets:
            url = target.get("webSocketDebuggerUrl") or ""
            if target.get("type") == "page" and url:
                # Chrome builds that URL from the request's Host header, so it echoes back whatever
                # authority was used — including a portless one, which refuses on connect (measured:
                # `ws://127.0.0.1/devtools/page/…`). The port this function was given is the truth.
                path = urllib.parse.urlsplit(url).path
                return f"ws://127.0.0.1:{port}{path}"
        time.sleep(0.5)
    raise RuntimeError(f"no CDP page target on 127.0.0.1:{port}; last_error={last!r}; "
                       f"targets_seen={seen[:6]}")


def connect_with_retry(port: int, attempts: int = 6):
    """Re-discover the page target before each websocket attempt.

    A refused connect after a successful /json/list is not contradiction: the target list is a
    snapshot, and a page target that has just been replaced (navigation, a crash-reload, or the
    first-run window settling) stops answering on its port while the browser endpoint keeps serving.
    Re-fetching is what makes that a retry rather than a refusal, and the last reason is reported
    rather than swallowed.
    """
    last_ws: str | None = None
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            ws = discover_page_ws(port, tries=6)
            last_ws = ws
            return ChromeCDP(ws), ws
        except (ConnectionRefusedError, OSError, RuntimeError) as exc:
            last_exc = exc
            time.sleep(1.0)
    raise RuntimeError(f"no usable CDP page session on port {port}; last_target={last_ws}; "
                       f"last_error={last_exc!r}")


def measure(root: Path, view: str, browser: str, u19, shot: Path | None) -> dict:
    port = u19.pick_free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                           cwd=str(root / "apps/observer/frontend/dist"),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    udf = OUT_DIR / f"udf-{int(time.time())}"
    log_path = OUT_DIR / f"chrome-{int(time.time())}.log"
    url = f"http://127.0.0.1:{port}/index.html?view={view}&mode=UNKNOWN&theme=dark&shell=tauri"
    requested_cdp = u19.pick_free_port()
    # Request a specific port and then believe what Chrome announces. `--remote-debugging-port=0`
    # announces a websocket port but serves no /json HTTP endpoint there, so discovery times out;
    # a requested port can also be re-bound by Chrome if the reservation races, and then the
    # requested number is the wrong one to query. The log line is the only authority.
    with log_path.open("wb") as log:
        proc = subprocess.Popen(
            [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
             # Without these the profile's first-run UI wins and no page target appears in time.
             "--no-first-run", "--no-default-browser-check", "--disable-extensions",
             f"--user-data-dir={udf}", f"--window-size={WIN_SIZE[view]}",
             f"--remote-debugging-port={requested_cdp}", "--remote-allow-origins=*", url],
            stdout=log, stderr=subprocess.STDOUT)
        cdp_port = None
        deadline = time.time() + 25
        while time.time() < deadline and cdp_port is None:
            time.sleep(0.5)
            match = LISTEN_RE.search(log_path.read_text(encoding="utf-8", errors="replace"))
            if match:
                cdp_port = int(match.group(1))
            if proc.poll() is not None:
                raise RuntimeError(f"chrome exited rc={proc.returncode}: "
                                   f"{log_path.read_text(encoding='utf-8', errors='replace')[:400]}")
        if cdp_port is None:
            proc.kill()
            srv.kill()
            raise RuntimeError("no `DevTools listening on` line in the chrome log")
        if cdp_port != requested_cdp:
            ANNOUNCED_MISMATCH.append(f"requested {requested_cdp}, announced {cdp_port}")
        time.sleep(2.0)  # the page target appears once the document has loaded
        try:
            cdp, _ws = connect_with_retry(cdp_port)
            try:
                cdp.send("Page.enable")
                time.sleep(1.0)
                raw = cdp.evaluate(EXPR.replace("SELECTORS", json.dumps(SELECTORS)))
                if shot is not None:
                    data = cdp.send("Page.captureScreenshot", {"format": "png"}).get("data", "")
                    shot.write_bytes(base64.b64decode(data))
                return json.loads(raw)
            finally:
                cdp.close()
        finally:
            proc.kill()
            srv.kill()
            try:
                shutil.rmtree(udf)
            except OSError as exc:
                # A profile dir the browser has not released yet is derived scratch, not evidence.
                # It is reported rather than swallowed, because ERR-140 exists for exactly that habit.
                RESIDUE.append(f"{udf} {exc!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--view", choices=("full", "compact"), action="append")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--screenshot", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / "apps/observer/frontend/dist/index.html").is_file():
        print(f"GEOMETRY_GATE_NOT_RUN DIST_ABSENT {root/'apps/observer/frontend/dist'}")
        return 3
    browser = find_browser()
    if not browser:
        print("GEOMETRY_GATE_NOT_RUN BROWSER_NOT_FOUND "
              "set WL_CHROME to a Chrome/Edge binary; a named category is not a pass")
        return 3

    views = args.view or ["full", "compact"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    u19 = load_u19()
    reports = []
    for view in views:
        shot = OUT_DIR / f"topbar-{view}.png" if args.screenshot else None
        try:
            measured = measure(root, view, browser, u19, shot)
        except Exception as exc:  # noqa: BLE001
            print(f"GEOMETRY_GATE_NOT_RUN MEASURE_FAILED {view} {exc!r}")
            return 3
        reports.append({"view": view, "verdict": verdict(measured, view),
                        "measured": measured, "browser": browser})

    out = Path(args.json_out) if args.json_out else (
        OUT_DIR / f"geometry_{int(time.time())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")

    ok = all(r["verdict"]["passed"] for r in reports)
    for r in reports:
        v = r["verdict"]
        for c in v["checks"]:
            print(f"{v['view']:<8} {c['check']:<28} {'PASS' if c['pass'] else 'FAIL'} {c['detail']}")
        print(f"{v['view']:<8} viewport={v['viewport']}")
    print(("GEOMETRY_GATE_PASS " if ok else "GEOMETRY_GATE_FAIL ") + str(out))
    if ANNOUNCED_MISMATCH:
        print("GEOMETRY_GATE_PORT_MISMATCH " + json.dumps(ANNOUNCED_MISMATCH))
    if RESIDUE:
        print("GEOMETRY_GATE_RESIDUE " + json.dumps(RESIDUE, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
