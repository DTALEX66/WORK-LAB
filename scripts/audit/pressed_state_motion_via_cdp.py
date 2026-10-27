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

Two surfaces, each read twice in its own browser process -- never two reads of one page:

  console  `…`                     the professional shell: `.nav button`, `.primary-btn`, `.ghost-btn`
  daily    `…&surface=daily`       the shell the desktop window shows: `nav[data-landmark="rail"] button`

  idle     no pseudo state forced  -- what the control looks like untouched
  pressed  `:active` forced        -- what the operator gets while the button is still down

Keeping idle and pressed in separate processes is what makes "the delta is real" checkable: a page that
reported the same transform twice would be a broken readback, and a page that reported a pressed transform
identical to idle means the rule was never applied. Measuring the daily surface separately is what keeps the
gate honest about coverage -- the first version of this instrument printed `controls=2` while the surface an
operator actually points at was matched by none of its selectors.

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
RAIL_SELECTOR = 'nav[data-landmark="rail"] button'
# Each surface names the control the gate refuses to run without. A selector that matches nothing would skip
# every assertion on it silently, so "which surface was actually measured" is part of the verdict, not a
# detail of the run. `.nav button` is the professional console's sidebar; the rail is the daily shell's own
# navigation -- the surface the desktop window really shows -- and it is styled with Tailwind utilities, so
# the B10 skin rules never reach it.
SURFACES = (
    {"name": "console", "query": "", "mount": ".app", "required": ".nav button",
     "selectors": (".nav button", ".primary-btn", ".ghost-btn", ".soft-btn")},
    {"name": "daily", "query": "surface=daily&shell=tauri", "mount": "[data-shell]",
     "required": RAIL_SELECTOR, "selectors": (RAIL_SELECTOR,)},
)
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


def verdict(readings: dict[str, dict]) -> dict:
    """Judge every surface on its own numbers, then require that each one actually moved something.

    A single aggregate "controls=2" is what let the first version of this instrument pass while the surface
    the desktop window shows was measured by nothing: a selector matching zero nodes contributes no check, so
    the totals stay green and the coverage line is the only place the hole shows. Per-surface assertions make
    an unmeasured surface fail by name.
    """
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    coverage: dict[str, int] = {}
    expectation: dict[str, object] = {}
    for surface_name, surface in readings.items():
        idle = surface["idle"]
        pressed = surface["pressed"]
        reduced = surface.get("pressedReduced")
        scale, duration, problems = token_expectations(idle.get("tokens") or {})
        expectation = {"pressedScale": scale, "transitionSeconds": duration}

        add(f"motion-preference-emulated[{surface_name}]",
            idle.get("reducedMotion") is False and pressed.get("reducedMotion") is False,
            f"idle reducedMotion={idle.get('reducedMotion')} pressed reducedMotion={pressed.get('reducedMotion')}")
        add(f"tokens-declared-and-parseable[{surface_name}]", not problems,
            json.dumps(idle.get("tokens") or {}) + ("" if not problems else " " + ";".join(problems)))

        idle_by = {row["selector"]: row for row in idle.get("selectors") or []}
        pressed_by = {row["selector"]: row for row in pressed.get("selectors") or []}
        required = surface["required"]
        add(f"required-control-rendered[{surface_name}]", (idle_by.get(required) or {}).get("count", 0) > 0,
            f"{required} count={json.dumps(idle_by.get(required))}")

        measured = 0
        for selector, pressed_row in pressed_by.items():
            coverage[f"{surface_name}/{selector}"] = int(pressed_row.get("count") or 0)
            if not pressed_row.get("count"):
                continue
            idle_row = idle_by.get(selector) or {}
            got_scale = matrix_scale(pressed_row.get("transform"))
            idle_scale = matrix_scale(idle_row.get("transform"))
            add(f"active-transform-matches-token[{surface_name}:{selector}]",
                scale is not None and got_scale is not None and math.isclose(got_scale, scale, abs_tol=0.005),
                f"pressed transform={pressed_row.get('transform')!r} scale={got_scale} token={scale}")
            # A control already drawn at the pressed scale when nothing is forced would make the check above
            # pass for the wrong reason: the rule has to move the box, not sit under it.
            add(f"pressed-state-changes-the-paint[{surface_name}:{selector}]",
                got_scale is not None and got_scale != idle_scale,
                f"idle={idle_row.get('transform')!r} scale={idle_scale} -> pressed scale={got_scale}")
            add(f"active-duration-matches-token[{surface_name}:{selector}]",
                duration is not None and seconds(pressed_row.get("transitionDuration")) == duration,
                f"transitionDuration={pressed_row.get('transitionDuration')!r} token={duration}s")
            measured += 1

        add(f"surface-measured-a-control[{surface_name}]", measured > 0,
            f"measured={measured} of {len(pressed_by)} declared selectors")

        if reduced is not None:
            # The L10b floor is a promise the shell makes to operators who asked for less motion: under
            # `reduce` the same forced press must paint NO transform. Asserting it here is what keeps the
            # floor from being deleted by someone who only ever tested the animated branch.
            reduced_by = {row["selector"]: row for row in reduced.get("selectors") or []}
            add(f"reduced-preference-observed[{surface_name}]", reduced.get("reducedMotion") is True,
                f"reducedMotion={reduced.get('reducedMotion')}")
            guarded = 0
            for selector, row in reduced_by.items():
                if not row.get("count"):
                    continue
                add(f"no-pressed-transform-under-reduce[{surface_name}:{selector}]",
                    matrix_scale(row.get("transform")) is None,
                    f"forced :active transform={row.get('transform')!r}")
                guarded += 1
            add(f"reduced-floor-covers-a-measured-control[{surface_name}]", guarded > 0,
                f"guarded selectors={guarded}")
    return {
        "passed": all(c["pass"] for c in checks),
        "checks": checks,
        "coverage": coverage,
        "surfaces": sorted(readings),
        "expectation": expectation,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--surface", action="append", default=None,
                    help=f"surfaces to probe (default: {' '.join(s['name'] for s in SURFACES)})")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    wanted = args.surface or [s["name"] for s in SURFACES]
    unknown = sorted(set(wanted) - {s["name"] for s in SURFACES})
    if unknown:
        # Validated before anything is looked for on disk: a misspelled surface is bad input whatever the
        # machine happens to have built, and silently probing nothing would report as a pass.
        print(f"PRESSED_MOTION_GATE_NOT_RUN UNKNOWN_SURFACE {json.dumps(unknown)}")
        return 2
    surfaces = [s for s in SURFACES if s["name"] in wanted]

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
    readings: dict[str, dict] = {}
    forced_nodes: dict[str, int] = {}
    urls: dict[str, str] = {}

    def make_hook(motion: str, force: bool, selectors: list[str], required: str):
        """One hook per launch: pin the media preference, then optionally hold `:active` on every control.

        Built as a function rather than a loop-scoped lambda, because the closure has to freeze the state it
        belongs to -- a late-bound lambda is how two launches end up measuring the same one.
        """
        def hook(cdp) -> None:
            emulate_motion(cdp, motion)
            if force:
                forced_nodes.update(force_active(cdp, selectors, required))
        return hook

    try:
        for spec in surfaces:
            url = fixture.url_for(spec["query"])
            urls[spec["name"]] = url
            expression = read_expression(list(spec["selectors"]))
            per_surface: dict[str, dict] = {"required": spec["required"]}
            states = [("idle", "no-preference", False), ("pressed", "no-preference", True)]
            if spec["name"] == surfaces[0]["name"]:
                # The reduced branch is the same stylesheet floor on every surface; measuring it once keeps
                # the browser starts bounded without letting the floor go unasserted.
                states.append(("pressedReduced", "reduce", True))
            for state, motion, force in states:
                # The forced node ids travel with the receipt: a reader who wants to know whether a control
                # was actually held down, rather than merely absent, has to be able to tell the two apart.
                hook = make_hook(motion, force, list(spec["selectors"]), spec["required"])
                for attempt in range(2):
                    try:
                        per_surface[state] = geometry.serve_and_eval(
                            root, "/index.html", WINDOW, expression, browser, u19, None,
                            viewport=(1280, 820), serve_url=url, after_mount=hook,
                            mount_selector=spec["mount"])
                        break
                    except Exception as exc:  # noqa: BLE001 — retried once, then reported by name
                        if attempt == 1:
                            print(f"PRESSED_MOTION_GATE_NOT_RUN "
                                  f"{spec['name'].upper()}_{state.upper()}_MEASURE_FAILED {exc!r}")
                            return 3
                        time.sleep(1.0)
            readings[spec["name"]] = per_surface
    finally:
        fixture.stop_server()

    result = verdict(readings)
    result["startedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    result["browser"] = browser
    result["urls"] = urls
    result["servedBundle"] = bundle_provenance.describe(root)
    result["forcedActiveNodes"] = forced_nodes
    result["measured"] = readings
    result["residue"] = list(geometry.RESIDUE)
    result["portAnnouncedMismatch"] = list(geometry.ANNOUNCED_MISMATCH)

    out = Path(args.json_out) if args.json_out else (OUT_DIR / f"pressed_{int(time.time())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    for check in result["checks"]:
        print(f"{check['check']:<52} {'PASS' if check['pass'] else 'FAIL'} {check['detail'][:150]}")
    print(f"PRESSED_MOTION_GATE_{'PASS' if result['passed'] else 'FAIL'} "
          f"surfaces={json.dumps(result['surfaces'])} coverage={json.dumps(result['coverage'])} "
          f"tokens={json.dumps(readings[surfaces[0]['name']]['idle'].get('tokens'))} " + str(out))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
