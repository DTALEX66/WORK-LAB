#!/usr/bin/env python
"""Prove the pressed state paints a different transform, over the shipped bundle, with real CSS state.

CL-16's first step is one dimension: `:active`. The two tokens that name it (`--motion-pressed`,
`--pressed-scale`) were declared in `apps/observer/frontend/src/index.css` and consumed by nothing -- the
only pressed rule in the tree was `.node:active{cursor:grabbing}` in `apps/observer/frontend/src/skins/b10.css`,
a cursor and not a motion -- so a token could be renamed, retuned or deleted and no check would notice,
which is the failure mode this project has already recorded as "aspirational tokens".

A synthetic `dispatchEvent(new MouseEvent('mousedown'))` cannot light a CSS pseudo-class -- that is why the
four hover assertions in `scripts/audit/hud_strip_geometry_via_cdp.py` can never fail (recorded in the open
register, CL-17). So this instrument does not synthesise anything: it asks Chrome, over the CSS domain, to
force `:active` on a real node and then reads back `getComputedStyle`. The rule either reaches the painted
box or it does not.

Two launches of the same bundle, not two reads of one page:

  idle     no pseudo state forced  -- what the control looks like untouched
  pressed  `:active` forced        -- what the operator gets while the button is still down

Keeping them in separate processes is what makes "the delta is real" checkable: a page that reported the
same transform twice would be a broken readback, and a page that reported a pressed transform identical to
idle means the rule was never applied.

The expectation is DERIVED from the token, not pinned: `--pressed-scale` becomes the matrix diagonal the
browser must show, `--motion-pressed` becomes the `transition-duration` it must show. Retuning a token in
source therefore moves the floor with it instead of breaking a hardcoded number.

usage: python scripts/audit/pressed_state_motion_via_cdp.py [--json-out PATH] [--selector '.nav button']
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _entry in (ROOT / "scripts" / "audit", ROOT / "apps" / "observer" / "scripts"):
    sys.path.insert(0, str(_entry))

import bundle_provenance  # noqa: E402
import hud_strip_geometry_via_cdp as hud  # noqa: E402
import topbar_geometry_via_cdp as geometry  # noqa: E402

OUT_DIR = ROOT / ".project-local" / "artifacts" / "cl16-pressed-motion"
# `.nav button` is the sidebar's own navigation and renders on every console view, so it is the population
# the gate refuses to run without; the two button classes are the shell's action controls, asserted wherever
# they are present and reported by count where they are not (a count of zero is coverage, never a pass).
REQUIRED_SELECTOR = ".nav button"
DEFAULT_SELECTORS = (".nav button", ".primary-btn", ".ghost-btn", ".soft-btn")
WINDOW = "1280,820"

READ = """(function(selectors){
  var rootStyle = getComputedStyle(document.documentElement);
  var out = {selectors: [], tokens: {
    pressedScale: (rootStyle.getPropertyValue('--pressed-scale') || '').trim(),
    motionPressed: (rootStyle.getPropertyValue('--motion-pressed') || '').trim()
  },
  // Read the preference back FROM THE PAGE. The emulation is only known to have landed when the subject
  // itself says so; otherwise a runner whose default differs decides what the numbers mean.
  reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches};
  selectors.forEach(function(sel){
    var nodes = document.querySelectorAll(sel);
    var entry = {selector: sel, count: nodes.length, transform: null,
                 transitionDuration: null, tag: null, label: null};
    if (nodes.length) {
      var first = nodes[0];
      var cs = getComputedStyle(first);
      entry.transform = cs.transform;
      entry.transitionDuration = cs.transitionDuration;
      entry.tag = first.tagName.toLowerCase();
      // The accessible name is what tells the reader which control these numbers came from; a transform
      // measured on an unnamed node is a number with no referent.
      entry.label = (first.getAttribute('aria-label') || first.textContent || '').trim().slice(0, 40);
    }
    out.selectors.push(entry);
  });
  return JSON.stringify(out);
})(SELECTORS)"""


def read_expression(selectors: list[str]) -> str:
    return READ.replace("SELECTORS", json.dumps(selectors))


def matrix_scale(transform: str | None) -> float | None:
    """The uniform scale a computed transform carries, or None when there is no transform at all."""
    if not transform or transform == "none":
        return None
    match = re.match(r"matrix\(([^)]+)\)", transform)
    if not match:
        return None
    parts = [float(value) for value in match.group(1).split(",")]
    return parts[0] if len(parts) == 6 else None


def seconds(value: str | None) -> float | None:
    """`transition-duration` as a number of seconds: Chrome renders 80ms as `0.08s`."""
    if not value:
        return None
    first = value.split(",")[0].strip()
    if first.endswith("ms"):
        return float(first[:-2]) / 1000.0
    if first.endswith("s"):
        return float(first[:-1])
    return None


def token_expectations(tokens: dict) -> tuple[float | None, float | None, list[str]]:
    problems: list[str] = []
    scale = None
    duration = None
    try:
        scale = float(tokens.get("pressedScale") or "")
    except ValueError:
        problems.append(f"tokens.pressedScale={tokens.get('pressedScale')!r} is not a number")
    duration = seconds(tokens.get("motionPressed"))
    if duration is None:
        problems.append(f"tokens.motionPressed={tokens.get('motionPressed')!r} is not a duration")
    return scale, duration, problems


def emulate_motion(cdp, value: str) -> None:
    """Pin `prefers-reduced-motion` for the page, and return nothing.

    Measured on the CI runner (2026-10-26, job `observer`): headless Chrome reports `reduce` by default, and
    the L10b accessibility floor in `apps/observer/frontend/src/skins/b10.css` answers it with
    `transition:none !important; transform:none !important`. So the pressed transform legitimately comes back
    `none` there -- a reading of the environment, not of the rule. An instrument that measures a motion
    therefore has to say which motion preference it measured under, and the reduced side has to be asserted
    too instead of being tripped over by accident.
    """
    cdp.send("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-reduced-motion", "value": value}]})
    time.sleep(0.2)  # the media change has to recalc before anything is read


def force_active(cdp, selectors: list[str], required: str) -> dict:
    """Hold `:active` on the first node of EVERY probed selector, and report the node id chosen per selector.

    Forcing only the required control would read the others while they are still untouched, and their
    pressed transform would come back `none` -- a failure that belongs to the instrument, not the product.
    """
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    document = cdp.send("DOM.getDocument", {"depth": 1})
    root_node = (document.get("root") or {}).get("nodeId")
    if not root_node:
        raise RuntimeError(f"DOM.getDocument returned no root nodeId: {json.dumps(document)[:200]}")
    forced: dict[str, int] = {}
    for selector in selectors:
        found = cdp.send("DOM.querySelector", {"nodeId": root_node, "selector": selector})
        node_id = found.get("nodeId") or 0
        if not node_id:
            if selector == required:
                raise RuntimeError(f"no node matched the required selector {selector!r}")
            continue
        cdp.send("CSS.forcePseudoState", {"nodeId": node_id, "forcedPseudoClasses": ["active"]})
        forced[selector] = node_id
    time.sleep(0.2)  # the recalc has to land before the read
    return forced


def verdict(idle: dict, pressed: dict, required: str, reduced: dict | None = None) -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    add("motion-preference-emulated",
        idle.get("reducedMotion") is False and pressed.get("reducedMotion") is False,
        f"idle reducedMotion={idle.get('reducedMotion')} pressed reducedMotion={pressed.get('reducedMotion')}")

    scale, duration, problems = token_expectations(idle.get("tokens") or {})
    add("tokens-declared-and-parseable", not problems,
        json.dumps(idle.get("tokens") or {}) + ("" if not problems else " " + ";".join(problems)))

    idle_by = {row["selector"]: row for row in idle.get("selectors") or []}
    pressed_by = {row["selector"]: row for row in pressed.get("selectors") or []}

    add("required-control-rendered", (idle_by.get(required) or {}).get("count", 0) > 0,
        f"{required} count={json.dumps(idle_by.get(required))}")

    measured = 0
    for selector, pressed_row in pressed_by.items():
        if not pressed_row.get("count"):
            continue
        idle_row = idle_by.get(selector) or {}
        got_scale = matrix_scale(pressed_row.get("transform"))
        idle_scale = matrix_scale(idle_row.get("transform"))
        add(f"active-transform-matches-token[{selector}]",
            scale is not None and got_scale is not None and math.isclose(got_scale, scale, abs_tol=0.005),
            f"pressed transform={pressed_row.get('transform')!r} scale={got_scale} token={scale}")
        # A control already drawn at the pressed scale when nothing is forced would make the check above
        # pass for the wrong reason: the rule has to move the box, not sit under it.
        add(f"pressed-state-changes-the-paint[{selector}]",
            got_scale is not None and got_scale != idle_scale,
            f"idle={idle_row.get('transform')!r} scale={idle_scale} -> pressed scale={got_scale}")
        add(f"active-duration-matches-token[{selector}]",
            duration is not None and seconds(pressed_row.get("transitionDuration")) == duration,
            f"transitionDuration={pressed_row.get('transitionDuration')!r} token={duration}s")
        measured += 1

    add("at-least-one-control-measured", measured > 0,
        f"measured={measured} of {len(pressed_by)} declared selectors")

    if reduced is not None:
        # The L10b floor is a promise the shell makes to operators who asked for less motion: under
        # `reduce` the same forced press must paint NO transform. Asserting it here is what keeps the floor
        # from being deleted by someone who only ever tested the animated branch.
        reduced_by = {row["selector"]: row for row in reduced.get("selectors") or []}
        add("reduced-preference-observed", reduced.get("reducedMotion") is True,
            f"reducedMotion={reduced.get('reducedMotion')}")
        guarded = 0
        for selector, row in reduced_by.items():
            if not row.get("count"):
                continue
            add(f"no-pressed-transform-under-reduce[{selector}]",
                matrix_scale(row.get("transform")) is None,
                f"forced :active transform={row.get('transform')!r}")
            guarded += 1
        add("reduced-floor-covers-a-measured-control", guarded > 0, f"guarded selectors={guarded}")
    return {
        "passed": all(c["pass"] for c in checks),
        "checks": checks,
        "coverage": {selector: row.get("count") for selector, row in pressed_by.items()},
        "measuredControls": measured,
        "expectation": {"pressedScale": scale, "transitionSeconds": duration},
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--selector", action="append", default=None,
                    help=f"controls to probe (default: {' '.join(DEFAULT_SELECTORS)})")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    selectors = args.selector or list(DEFAULT_SELECTORS)
    if REQUIRED_SELECTOR not in selectors:
        selectors = [REQUIRED_SELECTOR] + selectors

    root = Path(args.root).resolve()
    dist = root / "apps" / "observer" / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        print(f"PRESSED_MOTION_GATE_NOT_RUN DIST_ABSENT {dist}")
        return 3
    browser = geometry.find_browser()
    if not browser:
        print("PRESSED_MOTION_GATE_NOT_RUN BROWSER_NOT_FOUND "
              "set WL_CHROME to a Chrome/Edge binary; a named category is not a pass")
        return 3

    geometry.OUT_DIR.mkdir(parents=True, exist_ok=True)
    u19 = geometry.load_u19()
    fixture = hud.SnapshotFixture(dist)
    fixture.start()
    url = fixture.url_for("")
    expression = read_expression(selectors)
    harvests: dict[str, dict] = {}
    forced_nodes: dict[str, int] = {}

    def make_hook(motion: str, force: bool):
        """One hook per launch: pin the media preference, then optionally hold `:active` on every control.

        Built as a function rather than a loop-scoped lambda, because the closure has to freeze the state it
        belongs to -- a late-bound lambda is how two launches end up measuring the same one.
        """
        def hook(cdp) -> None:
            emulate_motion(cdp, motion)
            if force:
                forced_nodes.update(force_active(cdp, selectors, REQUIRED_SELECTOR))
        return hook

    launches = (("idle", "no-preference", False),
                ("pressed", "no-preference", True),
                ("pressedReduced", "reduce", True))
    try:
        for state, motion, force in launches:
            # The forced node ids travel with the receipt: a reader who wants to know whether a control was
            # actually held down, rather than merely absent, has to be able to tell the two apart.
            hook = make_hook(motion, force)
            for attempt in range(2):
                try:
                    harvests[state] = geometry.serve_and_eval(
                        root, "/index.html", WINDOW, expression, browser, u19, None,
                        viewport=(1280, 820), serve_url=url, after_mount=hook)
                    break
                except Exception as exc:  # noqa: BLE001 — retried once, then reported by name
                    if attempt == 1:
                        print(f"PRESSED_MOTION_GATE_NOT_RUN {state.upper()}_MEASURE_FAILED {exc!r}")
                        return 3
                    time.sleep(1.0)
    finally:
        fixture.stop_server()

    result = verdict(harvests["idle"], harvests["pressed"], REQUIRED_SELECTOR,
                     harvests.get("pressedReduced"))
    result["startedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    result["browser"] = browser
    result["url"] = url
    result["servedBundle"] = bundle_provenance.describe(root)
    result["forcedActiveNodes"] = forced_nodes
    result["measured"] = harvests
    result["residue"] = list(geometry.RESIDUE)
    result["portAnnouncedMismatch"] = list(geometry.ANNOUNCED_MISMATCH)

    out = Path(args.json_out) if args.json_out else (OUT_DIR / f"pressed_{int(time.time())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    for check in result["checks"]:
        print(f"{check['check']:<52} {'PASS' if check['pass'] else 'FAIL'} {check['detail'][:150]}")
    print(f"PRESSED_MOTION_GATE_{'PASS' if result['passed'] else 'FAIL'} "
          f"controls={result['measuredControls']} coverage={json.dumps(result['coverage'])} "
          f"tokens={json.dumps(harvests['idle'].get('tokens'))} " + str(out))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
