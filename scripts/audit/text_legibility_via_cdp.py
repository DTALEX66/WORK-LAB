#!/usr/bin/env python
"""Text legibility gate — measure the shipped bundle in a real browser: type floor, AA contrast, both themes.

DESIGN.md and SCREEN_SPEC.md state numeric clauses (no meaningful text below 12px, 4.5:1 normal / 3:1
large, in BOTH themes). Until this instrument existed nothing measured them: `verify_design_contract.py`
parses token files and `standard_validators.py` stores "text contrast >= 4.5:1" as a *string* and then
checks whether a caller declared it — both stay green over text a user cannot read. A standard nobody
measures is a description, not a contract.

Division of labour is deliberate: the browser harvests raw computed styles only, and every judgement
(parse the colour, composite the alpha, take the ratio, apply the large-text exemption) is pure Python
here, so it is unit-testable and falsifiable without launching anything (see
`tests/ci/test_text_legibility_gate.py`). The first version of this maths lived in a browser script and
carried a bug nobody could test — it dropped the foreground's alpha and scored 50%-transparent black
text as solid black, 21:1 instead of the 3.98:1 a user actually sees.

What it refuses to fake:
  * a sample that has not settled. The skins animate colour, so a read taken mid-transition returns
    interpolated values no user ever sees; two disagreeing samples exit 3, they do not average.
  * a thin harvest. Fewer than MIN_NODES text nodes means the page rendered nothing readable, which is
    reported as NOT_RUN — `scannedFileCount: 0` was a false green in this project once already.
  * an unparsable colour. A value this instrument cannot interpret is UNKNOWN and fails; it is never
    skipped into a pass.

Gradient backdrops are the one documented approximation: text over a `background-image` is measured
against the solid layer stack beneath it, and the affected node count is printed, not hidden.

Exit: 0 LEGIBILITY_GATE_PASS, 1 LEGIBILITY_GATE_FAIL, 3 LEGIBILITY_GATE_NOT_RUN.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEOMETRY = ROOT / "scripts" / "audit" / "topbar_geometry_via_cdp.py"
OUT_DIR = ROOT / ".project-local" / "artifacts" / "legibility"

WINDOW_SIZE = "1280,820"
THEMES = ("dark", "light")

FLOOR_PX = 12.0          # DESIGN.md: no text a user must read below 12px
AA_NORMAL = 4.5          # WCAG 2.2 SC 1.4.3
AA_LARGE = 3.0           # SC 1.4.3 large-text exemption
LARGE_PX = 24.0          # 18pt
LARGE_BOLD_PX = 18.66    # 14pt bold
MIN_NODES = 30           # a harvest thinner than this measured nothing

# Roles permitted below the floor. An entry must name a glyph that repeats information available
# elsewhere; `no_stale_floor_exception` fails any entry that matches nothing on the measured screen,
# and the list ships EMPTY because every role that used to claim an exception (.winctl-zoom, the
# first-frame strip, the brand caption) turns out to be text a user must read. Earning a slot here
# means proving the node is decorative, not that it is small.
FLOOR_EXCEPTIONS: list[tuple[str, str]] = []


def load_geometry():
    """Reuse the CDP client and the headless launcher the geometry gate already proved out."""
    spec = importlib.util.spec_from_file_location("topbar_geometry_via_cdp", GEOMETRY)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


# --------------------------------------------------------------------------- colour maths


_COLOR_RE = re.compile(r"rgba?\(([^)]+)\)")
_SRGB_RE = re.compile(r"color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*/\s*([\d.]+))?\)")


def parse_color(value: str) -> tuple[float, float, float, float] | None:
    """`rgb(14 171 188 / 0.7)` and `color(srgb 0.055 0.086 0.098)` to 0-255 channels plus alpha.

    Both forms are live in this bundle: Chrome reports computed colours as `rgb(...)`, and the B10
    skin writes `color(srgb R G B / A)` for its alpha-composited tokens. `color(srgb ...)` channels
    are 0-1 fractions, so reading them as 0-255 would silently make every such colour near-black.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text == "transparent":
        return (0.0, 0.0, 0.0, 0.0)
    if text == "currentcolor":
        return None
    srgb = _SRGB_RE.search(text)
    if srgb:
        alpha = 1.0 if srgb[4] is None else float(srgb[4])
        return tuple(float(srgb[i]) * 255.0 for i in (1, 2, 3)) + (alpha,)  # type: ignore[return-value]
    plain = _COLOR_RE.search(text)
    if not plain:
        return None
    parts = [p for p in re.split(r"[\s,/]+", plain[1].strip()) if p]
    if len(parts) < 3:
        return None
    channels: list[float] = []
    for piece in parts[:3]:
        if piece.endswith("%"):
            channels.append(float(piece[:-1]) * 2.55)
        else:
            channels.append(float(piece))
    alpha = 1.0
    if len(parts) >= 4:
        fourth = parts[3]
        alpha = float(fourth[:-1]) / 100.0 if fourth.endswith("%") else float(fourth)
    return (channels[0], channels[1], channels[2], alpha)


def channel_linear(value: float) -> float:
    s = value / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (channel_linear(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[float, float, float], bg: tuple[float, float, float]) -> float:
    hi, lo = max(fg, bg, key=relative_luminance), min(fg, bg, key=relative_luminance)
    light, dark = relative_luminance(hi), relative_luminance(lo)
    return round(((light + 0.05) / (dark + 0.05)) * 100) / 100


def over(fg: tuple[float, float, float, float], bg: tuple[float, float, float]) -> tuple[float, float, float]:
    """Source-over compositing of a translucent colour onto an opaque backdrop."""
    alpha = max(0.0, min(1.0, fg[3]))
    return tuple(fg[i] * alpha + bg[i] * (1.0 - alpha) for i in range(3))  # type: ignore[return-value]


def composite_backdrop(layers: list[str], page_background: str) -> tuple[tuple[float, float, float] | None, bool]:
    """Composite the ancestor background stack from the page root down to the element.

    Returns (rgb, ok). `ok=False` means one layer could not be parsed, which the caller must report as
    UNKNOWN rather than treat as absent — a dropped layer silently moves the answer by several points.
    """
    stack = list(reversed(layers)) + [page_background]
    base = parse_color(stack[-1])
    if base is None:
        return None, False
    current = (base[0], base[1], base[2])
    for raw in stack[:-1]:
        layer = parse_color(raw)
        if layer is None:
            return None, False
        if layer[3] <= 0:
            continue
        current = over(layer, current)
    return current, True


def required_ratio(size_px: float, weight: str) -> float:
    """WCAG large text: 18pt (24px) at any weight, or 14pt bold (18.66px at 700+)."""
    try:
        bold = int(re.sub(r"[^\d]", "", weight or "") or 400) >= 700
    except ValueError:
        bold = False
    if size_px >= LARGE_PX or (size_px >= LARGE_BOLD_PX and bold):
        return AA_LARGE
    return AA_NORMAL


def node_contrast(node: dict, page_background: str) -> dict:
    """Attach `renderedRatio`, `requiredRatio`, `pass`, `floorOk` and a `status` to one harvested node.

    Every branch sets `floorOk`: a node whose colour cannot be read still has a font size, and an
    unreadable node must not slip out of the floor census as well as the contrast one.
    """
    size = float(node.get("size") or 0)
    base = {**node, "floorOk": size >= FLOOR_PX}
    fg = parse_color(node.get("color") or "")
    bg, ok = composite_backdrop(node.get("bg") or [], page_background)
    if fg is None or not ok:
        return {**base, "status": "unknown-colour", "pass": False}
    if fg[3] <= 0:
        return {**base, "status": "invisible-foreground", "pass": False}
    need = required_ratio(size, str(node.get("weight") or ""))
    # Ancestor `opacity` multiplies into the painted glyph's alpha; the browser composites the whole
    # subtree, and folding it here is the same arithmetic seen a pixel further down.
    effective_alpha = fg[3] * float(node.get("opacity") or 1)
    ratio = contrast_ratio(over((fg[0], fg[1], fg[2], effective_alpha), bg), bg)
    return {**base, "status": "ok", "renderedRatio": ratio, "requiredRatio": need,
            "pass": ratio >= need}


def exception_matches(path: str) -> str | None:
    for pattern, reason in FLOOR_EXCEPTIONS:
        if re.search(pattern, path or ""):
            return reason
    return None


# --------------------------------------------------------------------------- harvest


HARVEST = """JSON.stringify((()=>{
  const nodes = [];
  const pathOf = (el) => {
    const bits = [];
    let node = el;
    for (let depth = 0; node && node !== document.documentElement && depth < 4; depth += 1) {
      const name = node.tagName ? node.tagName.toLowerCase() : '';
      const cls = (typeof node.className === 'string' ? node.className.trim() : '')
          .split(/\\s+/).filter(Boolean).slice(0, 3).join('.');
      bits.push(name + (cls ? '.' + cls : ''));
      node = node.parentElement;
    }
    return bits.join(' > ');
  };
  for (const el of document.querySelectorAll('body *')) {
    const own = Array.from(el.childNodes)
        .filter((n) => n.nodeType === 3 && n.textContent.trim().length)
        .map((n) => n.textContent.trim());
    if (!own.length) continue;                       // text containers are judged by their leaf
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;             // nothing painted, nothing to read
    if (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const bg = [];
    let gradient = false;
    let opacity = 1;
    for (let node = el; node; node = node.parentElement) {
      const style = getComputedStyle(node);
      bg.push(style.backgroundColor);
      if (style.backgroundImage && style.backgroundImage !== 'none') gradient = true;
      opacity *= parseFloat(style.opacity || '1');
    }
    const hiddenByAria = !!(el.closest && el.closest('[aria-hidden="true"]'));
    nodes.push({
      text: own[0].slice(0, 60), size: Math.round(parseFloat(cs.fontSize) * 100) / 100,
      weight: cs.fontWeight, color: cs.color, bg: bg, gradient: gradient,
      opacity: Math.round(opacity * 1000) / 1000, path: pathOf(el),
      ariaHidden: hiddenByAria ? 'true' : null, role: el.getAttribute('role') || null,
      rect: { w: Math.round(r.width), h: Math.round(r.height) },
    });
  }
  return {
    viewport: innerWidth + 'x' + innerHeight,
    theme: document.documentElement.className || 'dark',
    pageBackground: getComputedStyle(document.body).backgroundColor,
    htmlBackground: getComputedStyle(document.documentElement).backgroundColor,
    nodes: nodes,
  };
})())"""


def harvest_settled(root: Path, browser: str, u19, u19_geometry, theme: str) -> dict:
    """Load one theme and require two identical samples before reporting anything.

    `.nav button`, `.list-item`, `.panel` and the buttons carry `transition:.2s ease` in the pinned
    skin, so the first sample after load can still be interpolating. Two equal samples is the minimum
    evidence that what was read is what a user sees.
    """
    path = f"/index.html?view=full&mode=UNKNOWN&theme={theme}&shell=tauri"
    first = u19_geometry.serve_and_eval(root, path, WINDOW_SIZE, HARVEST, browser, u19)
    second = u19_geometry.serve_and_eval(root, path, WINDOW_SIZE, HARVEST, browser, u19)
    a = {(n["path"], n["text"]): (n["color"], n["size"]) for n in first["nodes"]}
    b = {(n["path"], n["text"]): (n["color"], n["size"]) for n in second["nodes"]}
    shared = set(a) & set(b)
    moved = sorted(str(key) + f" {a[key]} vs {b[key]}" for key in shared if a[key] != b[key])
    if moved:
        raise RuntimeError(f"NOT_SETTLED {len(moved)} of {len(shared)} nodes changed colour between "
                           f"samples: {moved[:3]}")
    if len(second["nodes"]) < MIN_NODES:
        raise RuntimeError(f"THIN_HARVEST only {len(second['nodes'])} text nodes (need {MIN_NODES})")
    return second


def verdict(theme: str, harvest: dict) -> dict:
    """Pure: no browser, no filesystem. Every check is one line of the written standard."""
    page_background = harvest.get("pageBackground") or harvest.get("htmlBackground") or "rgb(0,0,0)"
    scored = [node_contrast(n, page_background) for n in harvest.get("nodes") or []]
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    add("harvest_is_dense_enough", len(scored) >= MIN_NODES,
        f"nodes={len(scored)} floor={MIN_NODES}")

    # A theme that did not apply would make the whole light-theme column meaningless and green.
    announced = harvest.get("theme")
    add("theme_actually_applied", announced == theme,
        f"asked={theme} html.class={announced!r}")

    below = [n for n in scored if not n["floorOk"]]
    unexcepted = [n for n in below if exception_matches(n["path"]) is None]
    add("no_text_below_the_type_floor", not unexcepted,
        f"below={len(below)} unexcepted={len(unexcepted)} "
        + json.dumps([f"{n['size']}px {n['path'][:60]} {n['text'][:24]!r}" for n in unexcepted[:6]],
                     ensure_ascii=False))

    unknown = [n for n in scored if n["status"] == "unknown-colour"]
    add("no_unparsable_colour", not unknown,
        f"unknown={len(unknown)} "
        + json.dumps([f"{n['path'][:40]} color={n.get('color')} bg={(n.get('bg') or [None])[0]}"
                      for n in unknown[:5]], ensure_ascii=False))

    failed_aa = [n for n in scored if n["status"] != "unknown-colour"
                 and n["status"] != "invisible-foreground" and not n["pass"]]
    invisible = [n for n in scored if n["status"] == "invisible-foreground"]
    add("every_text_node_meets_AA", not failed_aa and not invisible,
        f"aa_failures={len(failed_aa)} invisible={len(invisible)} worst="
        + json.dumps([f"{n['renderedRatio']}:1 need {n['requiredRatio']} {n['size']}px "
                      f"{n['path'][:44]} {n['text'][:20]!r}"
                      for n in sorted(failed_aa, key=lambda x: x["renderedRatio"])[:6]],
                     ensure_ascii=False))

    stale = [(pattern, reason) for pattern, reason in FLOOR_EXCEPTIONS
             if not any(exception_matches(n["path"]) == reason for n in below)]
    add("no_stale_floor_exception", not stale,
        f"stale={[p for p, _ in stale]} (an exception that matches nothing is dead weight, not a rule)")

    gradient = [n for n in scored if n.get("gradient")]
    return {
        "theme": theme, "viewport": harvest.get("viewport"), "harvestedTheme": harvest.get("theme"),
        "passed": all(c["pass"] for c in checks), "checks": checks,
        "counts": {"nodes": len(scored), "belowFloor": len(below),
                   "unexceptedBelowFloor": len(unexcepted), "aaFailures": len(failed_aa),
                   "unknownColour": len(unknown), "gradientBackdrop": len(gradient),
                   "floorExceptions": len(below) - len(unexcepted)},
        "worst": [{"text": n["text"], "path": n["path"], "size": n["size"],
                   "ratio": n.get("renderedRatio"), "need": n.get("requiredRatio")}
                  for n in sorted((n for n in scored if "renderedRatio" in n),
                                  key=lambda x: x["renderedRatio"])[:10]],
    }


def crossfade_verdict(theme: str, samples: dict) -> dict:
    """Pure: judge the samples a theme switch produced, including the frames in between.

    The settled state is one clause of the standard; the other says the switch must not *pass through*
    colours nobody chose, which the first version of this instrument could not see — it deliberately
    refuses unsettled samples. The pinned skin eased colour for ~200-300ms and nav text measured 1.22:1
    inside that window, so `App.tsx` now holds transitions off for the two frames the swap needs. That
    is a mechanism, and a mechanism is only evidence if something reads the rendered values.
    """
    checks: list[dict] = []
    rows = []
    for label, nodes in (samples.get("samples") or []):
        for node in nodes:
            scored = node_contrast(node, samples.get("pageBackground") or "rgb(0,0,0)")
            rows.append({**scored, "sample": label,
                         "instant": node.get("instant"), "duration": node.get("duration")})

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    add("switch_was_observed", any(r["sample"] != "before" for r in rows),
        f"samples={len({r['sample'] for r in rows})}")

    mid = [r for r in rows if r["sample"] != "before"]
    sub_aa = [r for r in mid if "renderedRatio" in r and r["renderedRatio"] < r["requiredRatio"]]
    add("theme_switch_has_no_sub_aa_frame", bool(mid) and not sub_aa,
        f"mid_frames={len(mid)} sub_aa={len(sub_aa)} min="
        + str(min([r["renderedRatio"] for r in mid if "renderedRatio" in r], default=None))
        + " worst=" + json.dumps([f"{r['sample']} {r['renderedRatio']}:1 {r['path'][:30]}"
                                  for r in sub_aa[:4]], ensure_ascii=False))

    held = [r for r in mid if r.get("instant")]
    leaking = [r for r in held if (r.get("duration") or "0s") not in ("0s", "0.00s")]
    add("transitions_are_held_off_while_switching", bool(held) and not leaking,
        f"held_samples={len(held)} leaking={len(leaking)} "
        + json.dumps(sorted({r.get('duration') for r in leaking})[:4]))

    return {"theme": theme, "mode": "crossfade", "passed": all(c["pass"] for c in checks),
            "checks": checks, "counts": {"samples": len({r["sample"] for r in rows}),
                                         "nodes": len(rows)}}


CROSSFADE = """(async () => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const pick = () => Array.from(document.querySelectorAll('.nav button, .brand small, .topbar .search span'))
      .filter((el) => (el.textContent || '').trim().length)
      .slice(0, 40).map((el) => {
        const cs = getComputedStyle(el);
        const bg = [];
        for (let node = el; node; node = node.parentElement) bg.push(getComputedStyle(node).backgroundColor);
        return {
          text: (el.textContent || '').trim().slice(0, 30), size: parseFloat(cs.fontSize),
          weight: cs.fontWeight, color: cs.color, bg: bg, opacity: 1, gradient: false,
          path: el.tagName.toLowerCase() + '.' + (typeof el.className === 'string'
                ? el.className.trim().split(/\\s+/)[0] : ''),
          instant: document.documentElement.classList.contains('theme-instant'),
          duration: cs.transitionDuration,
        };
      });
  const toggle = Array.from(document.querySelectorAll('button'))
      .find((b) => /浅色|深色/.test((b.textContent || '')));
  if (!toggle) return JSON.stringify({error: 'NO_THEME_TOGGLE'});
  const out = [['before', pick()]];
  toggle.click();
  let elapsed = 0;
  for (const step of [0, 16, 50, 100, 200, 400]) {
    if (step) { await sleep(step); elapsed += step; }
    out.push(['t+' + elapsed + 'ms', pick()]);
  }
  await sleep(400);                       // let the new palette settle before the switch is undone
  toggle.click();
  await sleep(400);
  return JSON.stringify({
    samples: out,
    pageBackground: getComputedStyle(document.body).backgroundColor,
    themeAtStart: document.documentElement.className || 'dark',
  });
})()"""


def crossfade_measure(root: Path, browser: str, u19, geometry) -> dict:
    """Click the theme control in one live session and keep every frame the switch produced."""
    raw = geometry.serve_and_eval(root, "/index.html?view=full&mode=UNKNOWN&theme=dark&shell=tauri",
                                  WINDOW_SIZE, CROSSFADE, browser, u19)
    if raw.get("error"):
        raise RuntimeError(f"CROSSFADE_{raw['error']}")
    if not raw.get("samples"):
        raise RuntimeError("CROSSFADE_NO_SAMPLES")
    return raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--crossfade", action="store_true",
                    help="click the theme control and judge the frames it produces, not the settled page")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / "apps/observer/frontend/dist/index.html").is_file():
        print(f"LEGIBILITY_GATE_NOT_RUN DIST_ABSENT {root/'apps/observer/frontend/dist'}")
        return 3
    geometry = load_geometry()
    browser = geometry.find_browser()
    if not browser:
        print("LEGIBILITY_GATE_NOT_RUN BROWSER_NOT_FOUND set WL_CHROME to a Chrome/Edge binary")
        return 3
    u19 = geometry.load_u19()

    if args.crossfade:
        try:
            raw = crossfade_measure(root, browser, u19, geometry)
        except Exception as exc:  # noqa: BLE001
            print(f"LEGIBILITY_GATE_NOT_RUN CROSSFADE {exc!r}")
            return 3
        reports = [{"theme": "dark->light", "verdict": crossfade_verdict("dark->light", raw),
                    "samples": raw, "browser": browser}]
    else:
        reports = []
        for theme in THEMES:
            try:
                harvest = harvest_settled(root, browser, u19, geometry, theme)
            except Exception as exc:  # noqa: BLE001 — a failed measurement is NOT_RUN, never a silent pass
                print(f"LEGIBILITY_GATE_NOT_RUN {theme} {exc!r}")
                return 3
            reports.append({"theme": theme, "verdict": verdict(theme, harvest),
                            "harvest": harvest, "browser": browser})

    out = Path(args.json_out) if args.json_out else (
        OUT_DIR / f"legibility_{int(time.time())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")

    ok = all(r["verdict"]["passed"] for r in reports)
    for report in reports:
        v = report["verdict"]
        print(f"{v['theme']:<12} viewport={v.get('viewport', '-')} "
              f"counts={json.dumps(v['counts'])}")
        for check in v["checks"]:
            print(f"  {check['check']:<34} {'PASS' if check['pass'] else 'FAIL'} {check['detail']}")
        if "harvestedTheme" in v and v["harvestedTheme"] != v["theme"]:
            print(f"  THEME_ANNOUNCEMENT_MISMATCH asked={v['theme']} html.class={v['harvestedTheme']}")
    print(("LEGIBILITY_GATE_PASS " if ok else "LEGIBILITY_GATE_FAIL ") + str(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
