"""Gate: the legibility probe judges the measurement, and the maths behind it is testable without a browser.

DESIGN.md promises a 12px floor and AA contrast in both themes. This test pins the arithmetic that turns
that promise into a verdict — colour parsing, alpha compositing, the large-text exemption, and the
check list — against values derivable by hand. The browser only produces the raw computed styles; every
number is recomputed here, so a wrong instrument is caught by a failing test rather than by a screenshot.

Two planted faults are deliberate and are the reason this file exists:
  * translucent text must not be scored as opaque (the first version of this maths did, and reported
    21:1 for text that renders at 3.98:1);
  * a floor exception that matches nothing must fail, or the allowlist rots into a permanent excuse.
"""
from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "text_legibility_via_cdp.py"

spec = importlib.util.spec_from_file_location("text_legibility", SCRIPT)
legibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legibility)  # type: ignore[attr-defined]

WHITE = "rgb(255, 255, 255)"
BLACK = "rgb(0, 0, 0)"


def node(path="div.panel > span.body", text="hello", size=14.0, weight="400",
         color=BLACK, bg=None, opacity=1.0, gradient=False) -> dict:
    return {"text": text, "path": path, "size": size, "weight": weight, "color": color,
            "bg": bg if bg is not None else [WHITE, WHITE], "opacity": opacity,
            "gradient": gradient, "ariaHidden": None, "role": None, "rect": {"w": 80, "h": 18}}


def clean_harvest(count: int = 34, theme: str = "dark") -> dict:
    """A harvest shaped like the real `view=full` screen after the type-floor sweep: nothing sub-12px.

    It deliberately contains no below-floor node, because the shipped `FLOOR_EXCEPTIONS` is empty and
    `no_stale_floor_exception` reads that list against the measurement. A fixture that excused itself
    with a role the product no longer ships would hide the very check this file exists to prove.
    """
    nodes = [node(path=f"div.view{i % 3} > span.body", text=f"label {i}")
             for i in range(count)]
    return {"viewport": "1280x820", "theme": theme, "pageBackground": WHITE,
            "htmlBackground": WHITE, "nodes": nodes}


def checks_of(verdict: dict) -> dict:
    return {c["check"]: c for c in verdict["checks"]}


class ColourParsingTests(unittest.TestCase):
    def test_rgb_and_rgba_forms_are_read(self) -> None:
        self.assertEqual(legibility.parse_color("rgb(14, 171, 188)"), (14.0, 171.0, 188.0, 1.0))
        self.assertEqual(legibility.parse_color("rgb(14 171 188 / 0.5)"), (14.0, 171.0, 188.0, 0.5))
        self.assertEqual(legibility.parse_color("rgba(0, 0, 0, 0.25)"), (0.0, 0.0, 0.0, 0.25))

    def test_srgb_function_channels_are_fractions_not_bytes(self) -> None:
        """`color(srgb .957 .969 .98)` is #F4F7FA. Read as 0-255 it would be near-black, and every
        contrast on a skin-authored surface would be wrong in the safe-looking direction."""
        parsed = legibility.parse_color("color(srgb 0.957 0.969 0.98)")
        self.assertIsNotNone(parsed)
        self.assertAlmostEqual(parsed[0], 244.0, delta=0.6)
        self.assertAlmostEqual(parsed[2], 250.0, delta=0.6)
        self.assertEqual(parsed[3], 1.0)
        alpha = legibility.parse_color("color(srgb 0.5 0.5 0.5 / 0.72)")
        self.assertAlmostEqual(alpha[3], 0.72)

    def test_unreadable_values_return_none_instead_of_a_guess(self) -> None:
        self.assertIsNone(legibility.parse_color("hsl(12, 50%, 50%)"))
        self.assertIsNone(legibility.parse_color(""))
        self.assertIsNone(legibility.parse_color("rgb(1 2)"))
        self.assertEqual(legibility.parse_color("transparent"), (0.0, 0.0, 0.0, 0.0))


class ContrastMathsTests(unittest.TestCase):
    def test_black_on_white_is_21_and_symmetric(self) -> None:
        self.assertEqual(legibility.contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0)
        self.assertEqual(legibility.contrast_ratio((255, 255, 255), (0, 0, 0)), 21.0)

    def test_documented_reference_pair_reproduces(self) -> None:
        """DESIGN.md quotes #EEF6FC on #050D16 = 17.87:1, computed here independently of the browser."""
        self.assertEqual(legibility.contrast_ratio((238, 246, 252), (5, 13, 22)), 17.87)

    def test_translucent_text_is_composited_not_assumed_opaque(self) -> None:
        """The planted fault. 50% black on white paints #7F7F7F: 3.98:1, which fails AA. Scored as
        opaque black it reads 21:1 and passes — a green gate over text a user cannot read."""
        bg = legibility.composite_backdrop([WHITE], WHITE)[0]
        painted = legibility.over((0.0, 0.0, 0.0, 0.5), bg)
        self.assertAlmostEqual(painted[0], 127.5, delta=0.01)
        self.assertEqual(legibility.contrast_ratio(painted, bg), 3.98)
        scored = legibility.node_contrast(node(color="rgba(0, 0, 0, 0.5)"), WHITE)
        self.assertFalse(scored["pass"])
        self.assertEqual(scored["renderedRatio"], 3.98)

    def test_backdrop_stack_composites_root_first(self) -> None:
        """Element layer over ancestor layer over page: 50% red on opaque blue, then that on white."""
        rgb, ok = legibility.composite_backdrop(["rgba(255, 0, 0, 0.5)", WHITE], WHITE)
        self.assertTrue(ok)
        self.assertAlmostEqual(rgb[0], 255.0, delta=0.01)
        self.assertAlmostEqual(rgb[1], 127.5, delta=0.01)
        self.assertAlmostEqual(rgb[2], 127.5, delta=0.01)

    def test_transparent_layers_are_skipped_not_counted_as_paint(self) -> None:
        rgb, ok = legibility.composite_backdrop(["transparent", "rgba(0,0,0,0)"], "rgb(5, 13, 22)")
        self.assertTrue(ok)
        self.assertEqual(rgb, (5.0, 13.0, 22.0))

    def test_an_unparsable_layer_is_unknown_not_a_silent_base_colour(self) -> None:
        rgb, ok = legibility.composite_backdrop(["hsl(0,0%,50%)"], WHITE)
        self.assertFalse(ok)
        self.assertIsNone(rgb)

    def test_ancestor_opacity_reaches_the_measured_ratio(self) -> None:
        opaque = legibility.node_contrast(node(), WHITE)["renderedRatio"]
        faded = legibility.node_contrast(node(opacity=0.5), WHITE)["renderedRatio"]
        self.assertEqual(opaque, 21.0)
        self.assertLess(faded, opaque)
        self.assertEqual(faded, 3.98)

    def test_invisible_foreground_is_a_failure_not_a_zero_contrast_pass(self) -> None:
        scored = legibility.node_contrast(node(color="rgba(0, 0, 0, 0)"), WHITE)
        self.assertEqual(scored["status"], "invisible-foreground")
        self.assertFalse(scored["pass"])


class LargeTextExemptionTests(unittest.TestCase):
    def test_thresholds_follow_the_written_rule(self) -> None:
        self.assertEqual(legibility.required_ratio(14.0, "400"), 4.5)
        self.assertEqual(legibility.required_ratio(18.66, "600"), 4.5)
        self.assertEqual(legibility.required_ratio(18.66, "700"), 3.0)
        # 14pt bold is the floor of "large", so anything at least that size and bold stays exempt.
        self.assertEqual(legibility.required_ratio(23.9, "800"), 3.0)
        self.assertEqual(legibility.required_ratio(23.9, "400"), 4.5)
        self.assertEqual(legibility.required_ratio(24.0, "400"), 3.0)

    def test_a_large_node_in_the_exemption_band_is_accepted_while_a_small_one_is_not(self) -> None:
        """#787878 on white measures 4.42:1: under the 4.5 rule for body text, over the 3.0 rule the
        same colour earns once it is large. A gate that ignores the exemption fails real headings."""
        big = legibility.node_contrast(node(size=26.0, color="rgb(120, 120, 120)"), WHITE)
        small = legibility.node_contrast(node(size=14.0, color="rgb(120, 120, 120)"), WHITE)
        self.assertEqual(big["renderedRatio"], small["renderedRatio"])
        self.assertEqual(small["renderedRatio"], 4.42)
        self.assertTrue(big["pass"])
        self.assertFalse(small["pass"])


class VerdictTests(unittest.TestCase):
    def setUp(self) -> None:
        self.v = legibility.verdict("dark", clean_harvest())
        self.checks = checks_of(self.v)

    def test_a_clean_harvest_passes_and_names_every_check(self) -> None:
        self.assertTrue(self.v["passed"], json.dumps(self.v["checks"], ensure_ascii=False))
        self.assertEqual(set(self.checks), {"harvest_is_dense_enough", "theme_actually_applied",
                                            "no_text_below_the_type_floor", "no_unparsable_colour",
                                            "every_text_node_meets_AA", "no_stale_floor_exception"})

    def test_a_sub_floor_paragraph_fails_the_floor_check_and_names_it(self) -> None:
        harvest = clean_harvest()
        harvest["nodes"][3] = node(path="p.token-panel", text="成本质量由后端投影", size=10.0)
        v = legibility.verdict("dark", harvest)
        failed = checks_of(v)["no_text_below_the_type_floor"]
        self.assertFalse(failed["pass"])
        self.assertIn("10.0px", failed["detail"])
        self.assertIn("成本质量", failed["detail"])

    def test_an_aa_failure_fails_with_the_measured_number(self) -> None:
        harvest = clean_harvest()
        harvest["nodes"][5] = node(path="span.brand-sub", text="WORK-LAB", color="rgb(120, 120, 120)")
        v = legibility.verdict("dark", harvest)
        failed = checks_of(v)["every_text_node_meets_AA"]
        self.assertFalse(failed["pass"])
        self.assertIn("4.42:1", failed["detail"])

    def test_a_thin_harvest_is_not_a_pass(self) -> None:
        v = legibility.verdict("dark", clean_harvest(count=4))
        self.assertFalse(checks_of(v)["harvest_is_dense_enough"]["pass"])

    def test_an_unapplied_theme_is_failing_not_green(self) -> None:
        """?theme=light that never reaches <html> would otherwise report a whole dark palette as light."""
        v = legibility.verdict("light", clean_harvest(theme="dark"))
        self.assertFalse(checks_of(v)["theme_actually_applied"]["pass"])

    def test_an_unparsable_computed_colour_is_unknown_and_red(self) -> None:
        harvest = clean_harvest()
        harvest["nodes"][7] = node(path="span.weird", text="x", color="hsl(0, 0%, 0%)")
        v = legibility.verdict("dark", harvest)
        self.assertFalse(checks_of(v)["no_unparsable_colour"]["pass"])

    def test_a_declared_role_is_permitted_below_the_floor_but_still_counted(self) -> None:
        harvest = clean_harvest()
        harvest["nodes"][2] = node(path="span.winctl-zoom", text="125%", size=10.0)
        with mock.patch.object(legibility, "FLOOR_EXCEPTIONS",
                               [(r"\.winctl-zoom\b", "zoom readout")]):
            v = legibility.verdict("dark", harvest)
        self.assertTrue(checks_of(v)["no_text_below_the_type_floor"]["pass"])
        # The exception lets the node pass the floor check; it never hides the node from the count
        # printed in the receipt, so a growing list of "decorative" roles stays visible in the diff.
        self.assertEqual(v["counts"]["belowFloor"], 1)
        self.assertEqual(v["counts"]["floorExceptions"], 1)
        self.assertEqual(v["counts"]["unexceptedBelowFloor"], 0)

    def test_an_exception_that_matches_nothing_is_reported_as_stale(self) -> None:
        """Without this, every entry ever added to the allowlist keeps working after the rule it
        excuses is fixed, and the next violation is waved through by a stranger's exception."""
        with mock.patch.object(legibility, "FLOOR_EXCEPTIONS",
                               [(r"\.gone-away\b", "nothing on screen matches this")]):
            v = legibility.verdict("dark", clean_harvest())
        self.assertFalse(checks_of(v)["no_stale_floor_exception"]["pass"])
        self.assertIn("gone-away", checks_of(v)["no_stale_floor_exception"]["detail"])

    def test_the_shipped_floor_allowlist_is_empty_and_stays_that_way_unless_challenged(self) -> None:
        """Every role that claimed a sub-12px exemption turned out to be text a user must read: the
        zoom readout is the only place the level appears, the strip is the only first-frame answer,
        the brand caption names the product. Adding an entry here is a deliberate act, so it is
        asserted rather than assumed — and any entry must carry a reason.
        """
        self.assertEqual(legibility.FLOOR_EXCEPTIONS, [],
                         "a floor exception now ships; it must name a decorative role that repeats "
                         "information available elsewhere, or come out")

    def test_a_stale_pattern_in_a_harvest_is_reported_even_when_the_floor_check_passes(self) -> None:
        """The two allowlist checks are different questions: this harvest breaks no rule, yet carries
        an excuse that no longer maps to anything — which is how an exception outlives its reason."""
        with mock.patch.object(legibility, "FLOOR_EXCEPTIONS",
                               [(r"\.gone-away\b", "nothing on screen matches this")]):
            v = legibility.verdict("dark", clean_harvest(count=31))
        self.assertTrue(checks_of(v)["no_text_below_the_type_floor"]["pass"])
        self.assertFalse(checks_of(v)["no_stale_floor_exception"]["pass"])


class ContractAgreementTests(unittest.TestCase):
    def test_the_gate_and_the_written_standard_share_one_number(self) -> None:
        """DESIGN.md declares the floor in its typography scale; the gate must enforce the same value.

        Two numbers for one rule is how a contract and its check drift apart while both stay green.
        """
        design = (ROOT / "apps" / "observer" / "frontend" / "DESIGN.md").read_text(encoding="utf-8")
        front = design.split("---")[1]
        sizes = [float(m) for m in re.findall(r"fontSize:\s*([\d.]+)px", front)]
        self.assertGreaterEqual(len(sizes), 5, f"no typography scale parsed out of DESIGN.md: {sizes}")
        self.assertGreaterEqual(min(sizes), legibility.FLOOR_PX,
                                f"DESIGN.md declares {min(sizes)}px while the gate floors at "
                                f"{legibility.FLOOR_PX}px")


class CrossfadeVerdictTests(unittest.TestCase):
    """The switch itself: a settled page that passes can still flash through an unreadable frame."""

    @staticmethod
    def sample(color: str = BLACK, instant: bool = True, duration: str = "0s") -> list:
        return [{"text": "label", "path": "button.nav", "size": 14.0, "weight": "400",
                 "color": color, "bg": [WHITE, WHITE], "opacity": 1, "gradient": False,
                 "instant": instant, "duration": duration}]

    @staticmethod
    def bundle(labels: list[tuple[str, str]]) -> dict:
        return {"pageBackground": WHITE, "themeAtStart": "dark",
                "samples": [[label, nodes] for label, nodes in labels]}

    def test_a_clean_switch_passes_and_reports_how_many_frames_it_saw(self) -> None:
        v = legibility.crossfade_verdict("dark->light", self.bundle([
            ("before", self.sample()), ("t+16ms", self.sample()),
            ("t+66ms", self.sample())]))
        self.assertTrue(v["passed"], json.dumps(v["checks"], ensure_ascii=False))
        self.assertEqual(v["counts"]["samples"], 3)

    def test_a_sub_aa_intermediate_frame_fails(self) -> None:
        """The planted fault this whole mode exists for: 1.22:1 for two frames reads as a finished,
        compliant page in a settled measurement taken a second later."""
        v = legibility.crossfade_verdict("dark->light", self.bundle([
            ("before", self.sample()),
            ("t+16ms", self.sample(color="rgb(180, 190, 200)")),
            ("t+66ms", self.sample())]))
        failed = checks_of(v)["theme_switch_has_no_sub_aa_frame"]
        self.assertFalse(failed["pass"])
        self.assertIn("t+16ms", failed["detail"])

    def test_a_leaking_transition_duration_fails_even_when_every_ratio_is_fine(self) -> None:
        """The mechanism and the effect are separate claims: b10's `transition:.2s ease` winning over
        `.theme-instant` would put the switch back on an eased path, and the next sample might happen
        to look fine. This check is what stops that from being reported as a pass."""
        v = legibility.crossfade_verdict("dark->light", self.bundle([
            ("before", self.sample()), ("t+16ms", self.sample(duration="0.2s"))]))
        self.assertFalse(checks_of(v)["transitions_are_held_off_while_switching"]["pass"])
        self.assertTrue(checks_of(v)["theme_switch_has_no_sub_aa_frame"]["pass"])

    def test_no_samples_is_not_a_pass(self) -> None:
        v = legibility.crossfade_verdict("dark->light", {"pageBackground": WHITE, "samples": []})
        self.assertFalse(v["passed"])
        self.assertFalse(checks_of(v)["switch_was_observed"]["pass"])


class HarvestShapeTests(unittest.TestCase):
    """The JS half is a dumb harvester, but its selection rules decide what is invisible to the gate."""

    def test_the_offscreen_measuring_sizer_cannot_be_counted_as_text(self) -> None:
        """`.action-sizer` lives at top:-9999px on purpose. It holds a copy of every control label, so
        harvesting it would double the census and invent failures at coordinates nobody renders."""
        self.assertIn("r.top >= innerHeight", legibility.HARVEST)
        self.assertIn("r.bottom <= 0 || r.top >= innerHeight", legibility.HARVEST)

    def test_only_leaf_text_is_judged(self) -> None:
        self.assertIn("n.nodeType === 3", legibility.HARVEST)

    def test_the_instrument_shares_the_geometry_probe_launcher(self) -> None:
        """Two browser bootstraps is two definitions of "the page was ready". One is kept."""
        self.assertIn("serve_and_eval", legibility.load_geometry().__dict__)


if __name__ == "__main__":
    unittest.main()
