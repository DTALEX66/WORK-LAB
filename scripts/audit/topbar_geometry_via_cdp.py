#!/usr/bin/env python
"""Measure the top row's real geometry against the window edge.

Silent by design: headless Chrome on the shipped dist, driven over CDP, so the
numbers come from the same bundle the release binary embeds without putting a
window on the desktop. `?shell=tauri` is kept in the URL because that is the
configuration the owner is looking at.
"""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\All projects\WORK-LAB")
OBS = ROOT / "apps" / "observer"
HERE = ROOT / ".project-local" / "runs" / "topbar-measure-20261006"
HERE.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location(
    "u19", OBS / "scripts" / "u19_webview_e2e.py")
u19 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u19)  # type: ignore[attr-defined]

CHROME = str(Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
             / "Google/Chrome/Application/chrome.exe")

SELECTORS = [".app", ".topbar", ".search", ".top-actions", ".winctl",
             ".winctl-btn", ".sidebar", ".main", "body"]

EXPR = """JSON.stringify((()=>{
  const out = {};
  for (const sel of SELECTORS) {
    const els = [...document.querySelectorAll(sel)];
    if (!els.length) { out[sel] = {absent: true}; continue; }
    out[sel] = els.slice(0,2).map(el=>{
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return {
        left: Math.round(r.left*10)/10, right: Math.round(r.right*10)/10,
        top: Math.round(r.top*10)/10, bottom: Math.round(r.bottom*10)/10,
        width: Math.round(r.width*10)/10, height: Math.round(r.height*10)/10,
        gapToViewportRight: Math.round((innerWidth - r.right)*10)/10,
        gapToViewportLeft: Math.round(r.left*10)/10,
        gapToViewportTop: Math.round(r.top*10)/10,
        padding: cs.padding, margin: cs.margin, position: cs.position,
        overflowX: cs.overflowX
      };
    });
  }
  out.__viewport = innerWidth + 'x' + innerHeight;
  out.__docScrollWidth = document.documentElement.scrollWidth;
  out.__elementsOverlappingRightEdge = [...document.querySelectorAll('body *')]
      .filter(e=>{const r=e.getBoundingClientRect();
        return r.width>0 && r.right > innerWidth - 2 && r.left < innerWidth - 2;})
      .slice(0,12).map(e=>e.tagName+'.'+(typeof e.className==='string'?e.className:'')
        +' right='+Math.round(e.getBoundingClientRect().right));
  out.__elementsAtTopEdge = [...document.querySelectorAll('body *')]
      .filter(e=>{const r=e.getBoundingClientRect();
        return r.width>0 && r.height>0 && r.top < 3;})
      .slice(0,12).map(e=>e.tagName+'.'+(typeof e.className==='string'?e.className:'')
        +' top='+Math.round(r0(e)));
  return out;
})())"""


def main() -> int:
    port = u19.pick_free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port),
                            "--bind", "127.0.0.1"],
                           cwd=str(OBS / "frontend" / "dist"),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cdp_port = u19.pick_free_port()
    udd = HERE / f"chrome-udf-{int(time.time())}"
    expr = EXPR.replace("SELECTORS", json.dumps(SELECTORS)).replace(
        "Math.round(r0(e))", "Math.round(e.getBoundingClientRect().top)")
    url = (f"http://127.0.0.1:{port}/index.html?view=full&mode=UNKNOWN"
           "&theme=dark&shell=tauri")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={udd}", "--window-size=1280,820",
         f"--remote-debugging-port={cdp_port}", "--remote-allow-origins=*",
         url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    report: dict = {"url": url}
    time.sleep(2.0)  # let the static server bind before Chrome asks for it
    try:
        time.sleep(3.0)  # let Chrome come up and finish loading
        ws = u19.discover_cdp_ws(cdp_port, tries=40)
        report["ws"] = ws
        cdp = u19.CDP(ws)
        cdp._send_cmd("Page.enable")
        time.sleep(1.0)
        report["measured"] = json.loads(cdp.evaluate(expr))
        png = HERE / "topbar.png"
        import base64
        png.write_bytes(base64.b64decode(
            cdp._send_cmd("Page.captureScreenshot", {"format": "png"}).get("data", "")))
        report["screenshot"] = str(png)
    except Exception as exc:  # noqa: BLE001
        report["error"] = repr(exc)
    finally:
        proc.kill()
        srv.kill()
    (HERE / "measure.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    m = report.get("measured", {})
    print("viewport:", m.get("__viewport"), "scrollWidth:", m.get("__docScrollWidth"))
    for sel in SELECTORS:
        v = m.get(sel)
        if isinstance(v, list):
            for e in v:
                print(f"{sel:<12} top={e.get('top')} left={e.get('left')} "
                      f"right-gap={e.get('gapToViewportRight')} "
                      f"w={e.get('width')} h={e.get('height')} pad={e.get('padding')}")
        else:
            print(f"{sel:<12} {v}")
    print("at right edge:", json.dumps(m.get("__elementsOverlappingRightEdge"),
                                       ensure_ascii=False)[:600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
