"""Measure how long the artifact-handle block takes to become visible on the evidence lane.

Closes the metric blueprint's remaining "should" gap (`.project-local/artifacts/standalone-run-20261019/
metric.json`, gap 5): every other legibility/geometry instrument asks whether a screen is readable once it
is there; none of them said anything about how long a reader waits for the block that carries the snapshot's
handle facts. This one uses the real chain -- `u19.start_sidecar()` serving the real v3 snapshot -- not a
stub, because the question is about the shipped projection's own timing.

What it can claim: per fresh page load, the milliseconds from navigation start until the handle row list is
in the DOM with at least one row, plus the same reading for the capacity line. What it cannot claim: paint
timing inside a compositor, or anything about a machine other than this one -- so it reports the median and
the worst of N loads and names its own sampling granularity (a 20 ms poll), because a threshold that ignores
the instrument's resolution is a guess.

Exit: 0 HANDLE_LATENCY_PASS, 1 HANDLE_LATENCY_FAIL, 3 HANDLE_LATENCY_NOT_RUN.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEOMETRY = ROOT / "scripts" / "audit" / "topbar_geometry_via_cdp.py"
POLL_MS = 20

EXPRESSION = r"""(async () => {
  const CFG = %s;
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  const t0 = performance.getEntriesByType('navigation')[0] ? performance.timeOrigin : Date.now();
  const since = () => Math.round(Date.now() - t0);
  const rows = () => document.querySelector('[data-testid="evidence-handles-rows"]');
  const out = {rowsMs: null, capacityMs: null, rowCount: 0, lane: null, problems: [],
               firstText: null, navType: null, domContentLoadedMs: null};
  const deadline = Date.now() + CFG.budgetMs;
  while (Date.now() - t0 < CFG.budgetMs) {
    const list = rows();
    if (list && !out.capacityMs
        && document.querySelector('[data-testid="evidence-handles-capacity"], '
                                  + '[data-testid="evidence-handles-window"]')) {
      out.capacityMs = since();
    }
    if (list && list.children.length && out.rowsMs === null) {
      out.rowsMs = since();
      out.rowCount = list.children.length;
      out.firstText = (list.children[0].textContent || '').trim().slice(0, 60);
      break;
    }
    await sleep(CFG.pollMs);
  }
  const nav = performance.getEntriesByType('navigation')[0];
  out.navType = nav ? nav.type : null;
  out.domContentLoadedMs = nav ? Math.round(nav.domContentLoadedEventEnd) : null;
  out.lane = new URLSearchParams(location.search).get('view');
  if (out.rowsMs === null) {
    out.problems.push('no handle row inside ' + CFG.budgetMs + 'ms -- the block never became visible, '
                      + 'so every number below is a missing measurement, not a fast one');
  }
  return JSON.stringify(out);
})()"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--budget-ms", type=int, default=8000,
                    help="how long one load may take before it is reported as never-visible")
    ap.add_argument("--fail-over-ms", type=int, default=None,
                    help="median budget; the gate fails above it. Unset means report-only, and says so.")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location("geometry", GEOMETRY)
    geometry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geometry)  # type: ignore[attr-defined]
    browser = geometry.find_browser()
    dist = ROOT / "apps/observer/frontend/dist/index.html"
    if not dist.is_file():
        print(f"HANDLE_LATENCY_NOT_RUN DIST_ABSENT {dist} (run npm run build in apps/observer/frontend)")
        return 3
    if not browser:
        print("HANDLE_LATENCY_NOT_RUN BROWSER_NOT_FOUND")
        return 3
    u19 = geometry.load_u19()

    sidecar, port, _thread, server = u19.start_sidecar()
    expr = EXPRESSION % json.dumps({"budgetMs": args.budget_ms, "pollMs": POLL_MS})
    path = f"/index.html?view=evidence&theme=dark&api=http://127.0.0.1:{port}"
    samples, problems = [], []
    try:
        for _ in range(max(1, args.samples)):
            try:
                got = geometry.serve_and_eval(ROOT, path, "1280,820", expr, browser, u19)
            except Exception:  # noqa: BLE001 -- a failed launch is reported, never counted as slow
                traceback.print_exc()
                print("HANDLE_LATENCY_NOT_RUN LAUNCH_FAILED")
                return 3
            body = json.loads(got) if isinstance(got, str) else got
            samples.append(body)
            problems.extend(body.get("problems") or [])
    finally:
        server.shutdown()

    rows_ms = [s["rowsMs"] for s in samples if s.get("rowsMs") is not None]
    cap_ms = [s["capacityMs"] for s in samples if s.get("capacityMs") is not None]
    report = {
        "instrument": "handle_block_visibility_via_cdp",
        "backend": "live sidecar on a dynamic loopback port",
        "browser": browser, "pollMs": POLL_MS, "budgetMs": args.budget_ms,
        "samples": samples,
        "rowsMs": {"n": len(rows_ms), "median": statistics.median(rows_ms) if rows_ms else None,
                   "worst": max(rows_ms) if rows_ms else None},
        "capacityMs": {"n": len(cap_ms), "median": statistics.median(cap_ms) if cap_ms else None,
                       "worst": max(cap_ms) if cap_ms else None},
        "rowCountObserved": [s.get("rowCount") for s in samples],
        "failOverMs": args.fail_over_ms,
    }
    if len(rows_ms) < len(samples):
        problems.append(f"{len(samples) - len(rows_ms)} of {len(samples)} loads never showed a row")
    if not rows_ms:
        problems.append("no sample produced a visible handle block -- nothing was measured")
    if args.fail_over_ms is None:
        print("HANDLE_LATENCY_BUDGET_NOT_SET reporting only; pass --fail-over-ms to make this a gate")
    elif rows_ms and statistics.median(rows_ms) > args.fail_over_ms:
        problems.append(f"median {statistics.median(rows_ms)}ms exceeds the stated budget "
                        f"{args.fail_over_ms}ms")

    report["problems"] = problems
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                       newline="\n")
    print(f"HANDLE_LATENCY rows n={len(rows_ms)} median={report['rowsMs']['median']} "
          f"worst={report['rowsMs']['worst']} capacity median={report['capacityMs']['median']} "
          f"rows={report['rowCountObserved']}")
    for p in problems:
        print("  PROBLEM", p)
    if problems:
        print("HANDLE_LATENCY_FAIL")
        return 1
    print(f"HANDLE_LATENCY_PASS -> {args.json_out or 'stdout only'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
