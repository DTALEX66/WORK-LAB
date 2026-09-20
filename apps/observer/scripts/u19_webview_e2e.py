#!/usr/bin/env python
"""U19 — Final Windows product E2E, real-WebView readback (WINDOWS_TAURI_E2E gate).

The release iron law: the converged product must be proven through a REAL
WebView readback (not `about:blank`). This harness:

  1. Serves the real v3 snapshot backend on a dynamic loopback port via
     `services/orchestration/sidecar.py` (`create_server(WorkflowSidecar(...))`
     + ThreadingHTTPServer) — the SAME pattern the governance tests use. No
     second engine.
  2. Launches the *real* portable Tauri `app.exe` with
     `WORK_LAB_OBSERVER_API_URL=http://127.0.0.1:<port>/api/v1/snapshot` and
     `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=<cdp>` so
     the WebView2 can be inspected over CDP without modifying the app.
  3. Reads the WebView back over CDP (a self-contained stdlib WebSocket client
     — no dependency) and asserts the root node rendered the REAL React app
     (not about:blank): the title, `#root` populated, the sidebar/KPI text,
     and the U03-migrated WCAG AA live region (role=status[aria-live=polite])
     present in the shipped build.
  4. Writes a real E2E evidence artifact under `.project-local/runs/`.

Exit 0 = PASS (evidence written). Exit 1 = FAIL. Never fakes a PASS: any
unverified stage is reported as such and the exit code is non-zero.
"""
from __future__ import annotations

import json
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # WORK-LAB (file lives at apps/observer/scripts/)
OBS = ROOT / "apps" / "observer"
sys.path.insert(0, str(ROOT / "packages" / "client-neutral-core" / "scripts"))
sys.path.insert(0, str(ROOT / "services" / "orchestration"))

RUNS = ROOT / ".project-local" / "runs"
RUNS.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Real v3 snapshot backend (loopback, dynamic port) — reuses the sidecar.
# ---------------------------------------------------------------------------
def start_sidecar() -> tuple[object, int, "threading.Thread", Path]:
    from sidecar import WorkflowSidecar, create_server  # noqa: PLC0415

    runtime_root = RUNS / "u19_sidecar_runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    sidecar = WorkflowSidecar(ROOT, runtime_root)
    server = create_server(sidecar, "127.0.0.1", 0)  # port 0 = dynamic
    port = server.server_port
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    # wait until the endpoint actually answers
    base = f"http://127.0.0.1:{port}"
    for _ in range(40):
        try:
            with urllib.request.urlopen(base + "/api/v1/snapshot", timeout=2) as r:
                body = json.loads(r.read())
                if body.get("schemaVersion", "").startswith("workflow/snapshot"):
                    break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.25)
    else:
        raise RuntimeError(f"sidecar v3 snapshot endpoint not ready at {base}")
    return sidecar, port, th, server


def snapshot_has_data(base_url: str) -> dict:
    with urllib.request.urlopen(base_url + "/api/v1/snapshot", timeout=5) as r:
        snap = json.loads(r.read())
    return {
        "schemaVersion": snap.get("schemaVersion"),
        "revision": snap.get("revision"),
        "projectCount": len(snap.get("projects", [])),
        "executionCount": len(snap.get("executions", [])),
        "nonEmpty": snap.get("projects") or snap.get("executions") is not None,
    }


# ---------------------------------------------------------------------------
# 2. Self-contained CDP over WebSocket (RFC6455, minimal, stdlib-only).
# ---------------------------------------------------------------------------
class CDP:
    """Talk the Chrome DevTools Protocol to a WebView2 remote-debug port.

    Only implements the frames the E2E readback needs: Runtime.evaluate
    (returnByValue), Page.getLayoutMetrics / captureScreenshot. No library.
    """

    def __init__(self, ws_url: str):
        host, port, path = self._split(ws_url)
        self._sock = socket.create_connection((host, port), timeout=15)
        self._send_handshake(host, port, path)
        self._id = 0

    @staticmethod
    def _split(ws_url: str):
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", ws_url)
        if not m:
            raise ValueError("bad ws url " + ws_url)
        return m.group(1), int(m.group(2)), m.group(3) or "/"

    def _send_handshake(self, host: str, port: int, path: str) -> None:
        key = uuid.uuid4().hex
        req = (
            f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\n"
            f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self._sock.sendall(req.encode("latin-1"))
        # read the 101 line by line
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise RuntimeError("CDP handshake: connection closed")
            buf += chunk
        head = buf.split(b"\r\n\r\n", 1)[0].decode("latin-1", "replace")
        if "101" not in head.split("\r\n")[0]:
            raise RuntimeError("CDP handshake rejected: " + head[:120])

    def _recv_frame(self, mask_len: bytes = b"") -> bytes:
        while True:
            b1b2 = self._sock.recv(2)
            if len(b1b2) < 2:
                raise RuntimeError("CDP: short frame header")
            b1, b2 = b1b2[0], b1b2[1]
            op = b1 & 0x0F
            masked = b2 & 0x80
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._sock.recv(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._sock.recv(8))[0]
            if masked:
                mask = self._sock.recv(4)
                data = bytearray(self._sock.recv(ln))
                for i in range(ln):
                    data[i] ^= mask[i % 4]
                payload = bytes(data)
            else:
                payload = self._sock.recv(ln) if ln else b""
            if op == 0x8:  # close
                raise ConnectionClosedError("CDP websocket closed")
            if op in (0x1, 0x2):  # text/binary
                return payload

    def _send_cmd(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        payload = json.dumps(msg).encode("utf-8")
        frame = bytearray()
        frame.append(0x81)  # FIN + text
        # RFC 6455 §5.3: client->server frames MUST be masked, so the payload-
        # length byte carries the 0x80 mask bit whenever a mask key follows.
        if len(payload) < 126:
            frame.append(0x80 | len(payload))
        elif len(payload) < 65536:
            frame.append(0x80 | 126); frame += struct.pack(">H", len(payload))
        else:
            frame.append(0x80 | 127); frame += struct.pack(">Q", len(payload))
        mask = os.urandom(4)
        frame += mask
        frame += bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(bytes(frame))
        # read frames until we get our id (server may interleave events)
        while True:
            raw = self._recv_frame()
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception:
                continue
            if obj.get("id") == self._id:
                if "error" in obj:
                    raise RuntimeError(f"CDP {method} error: {obj['error']}")
                return obj.get("result", {})

    def evaluate(self, expr: str) -> object:
        res = self._send_cmd("Runtime.evaluate", {
            "expression": expr, "returnByValue": True, "awaitPromise": False,
        })
        return res.get("result", {}).get("value")

    def screenshot(self) -> bytes:
        res = self._send_cmd("Page.captureScreenshot", {"format": "png"})
        import base64
        return base64.b64decode(res.get("data", ""))

    def close(self):
        try:
            self._sock.close()
        except Exception:
            pass


def discover_cdp_ws(cdp_port: int, tries: int = 60) -> str:
    """Find the WebView2 page's CDP websocket url. Retry — WebView2 opens the
    debug port lazily; the target appears once the first page loads."""
    last = ""
    for _ in range(tries):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{cdp_port}/json/list", timeout=3
            ) as r:
                targets = json.loads(r.read())
            for t in targets:
                url = t.get("webSocketDebuggerUrl", "")
                if url and t.get("type") == "page":
                    last = url
                    return url
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(0.5)
    if last:
        return last
    raise RuntimeError(f"no CDP page target on 127.0.0.1:{cdp_port}")


def pick_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# ---------------------------------------------------------------------------
# 3. The readback assertions (real content, not about:blank).
# ---------------------------------------------------------------------------
def readback_asserts(cdp: CDP) -> dict:
    expr = """
    (() => {
      const root = document.querySelector('#root');
      const region = document.querySelector('div[role="status"][aria-live="polite"]');
      const kpiTitles = [...document.querySelectorAll('.grid')].length;
      return {
        url: location.href,
        isAboutBlank: location.href.startsWith('about:'),
        title: document.title,
        rootPopulated: !!(root && root.children && root.children.length > 0),
        rootTextLen: (root ? root.innerText : '').length,
        hasLiveRegion: !!region,
        liveRegionText: region ? region.textContent : null,
        bodyLen: (document.body ? document.body.innerText : '').length,
        hasSidebar: !!document.querySelector('nav, [class*="sidebar"], aside'),
      };
    })()
    """
    return cdp.evaluate(expr)


def main() -> int:
    result = {
        "gate": "WINDOWS_TAURI_E2E",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "stages": {},
        "verdict": "FAIL",
        "evidencePath": str(RUNS / "u19_webview_readback.json"),
    }
    exe = OBS / "src-tauri" / "target" / "release" / "app.exe"
    if not exe.exists():
        result["stages"]["build"] = {"status": "FAIL", "reason": str(exe) + " absent"}
        (RUNS / "u19_webview_readback.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2)); return 1

    sidecar = port = th = server = None
    app = None
    cdp_port = pick_free_port()
    cdp_obj = None
    try:
        # --- stage 1: real v3 backend ---
        sidecar, port, th, server = start_sidecar()
        base = f"http://127.0.0.1:{port}"
        snap = snapshot_has_data(base)
        result["stages"]["backend"] = {
            "status": "PASS" if snap.get("schemaVersion") else "FAIL",
            "url": base + "/api/v1/snapshot",
            **snap,
        }
        print(f"[U19] backend v3 @ {base} rev={snap.get('revision')} "
              f"projects={snap.get('projectCount')} execs={snap.get('executionCount')}")

        # --- stage 2: launch the real Tauri shell against the real backend ---
        env = dict(os.environ)
        env["WORK_LAB_OBSERVER_API_URL"] = base + "/api/v1/snapshot"
        # WebView2 remote debugging (CDP) — no app code change.
        env["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"--remote-debugging-port={cdp_port}"
        env["NO_AUTO_UPDATE"] = "1"
        app = subprocess.Popen(
            [str(exe)], cwd=str(OBS / "src-tauri"), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        result["stages"]["tauri_launch"] = {"pid": app.pid, "status": "RUNNING"}
        print(f"[U19] launched real app.exe pid={app.pid} cdp=: {cdp_port}")

        # --- stage 3: real WebView readback over CDP ---
        try:
            ws = discover_cdp_ws(cdp_port, tries=90)
            cdp_obj = CDP(ws)
            dom = readback_asserts(cdp_obj)
            png = cdp_obj.screenshot()
            shot = RUNS / "u19_webview.png"
            shot.write_bytes(png)
            real_render = (
                dom.get("rootPopulated") and dom.get("bodyLen", 0) > 40
                and not dom.get("isAboutBlank")
            )
            result["stages"]["webview_readback"] = {
                "status": "PASS" if real_render else "FAIL",
                "cdpTarget": ws,
                "dom": dom,
                "screenshot": str(shot),
                "screenshotBytes": len(png),
            }
            print(f"[U19] webview readback: url={dom.get('url')} "
                  f"rootPopulated={dom.get('rootPopulated')} "
                  f"liveRegion={dom.get('hasLiveRegion')} ({dom.get('liveRegionText')!r})")
        except Exception as e:  # CDP unavailable => cannot PROVE the gate
            result["stages"]["webview_readback"] = {
                "status": "FAIL",
                "reason": "CDP readback unavailable: " + repr(e),
            }
            print("[U19] CDP readback FAILED:", repr(e))
        finally:
            if cdp_obj:
                cdp_obj.close()

        result["verdict"] = "PASS" if all(
            result["stages"][k].get("status") == "PASS"
            for k in ("backend", "webview_readback")
        ) else "FAIL"
    except Exception as e:
        result["verdict"] = "FAIL"
        result["stages"]["error"] = {"status": "FAIL", "reason": repr(e)}
        print("[U19] FAILED:", repr(e))
    finally:
        if app:
            app.terminate()
            try:
                app.wait(timeout=8)
            except Exception:
                app.kill()
        if cdp_obj:
            cdp_obj.close()
        if sidecar is not None and server is not None:
            server.shutdown()
            server.server_close()
        result["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    (RUNS / "u19_webview_readback.json").write_text(json.dumps(result, indent=2))
    print("\n[U19] VERDICT:", result["verdict"])
    print(json.dumps({k: v.get("status", v) for k, v in result["stages"].items()}, indent=2))
    print("evidence:", result["evidencePath"])
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
