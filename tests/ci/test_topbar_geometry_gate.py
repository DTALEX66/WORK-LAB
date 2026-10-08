"""Gate: the CDP geometry probe is a verdict, not a printout (UI prompt pack G3).

The probe shipped for a week as an instrument that could only produce numbers: `main()` returned
None, so it always exited 0, and no workflow step or test referenced it. Every check here is on the
PURE verdict function, so the assertions are reviewable and run on any checkout — the browser is
only needed to produce the measurement it judges.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "topbar_geometry_via_cdp.py"

spec = importlib.util.spec_from_file_location("topbar_geometry", SCRIPT)
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)  # type: ignore[attr-defined]


def element(left=0.0, width=280.0, height=40.0, gap=10.0, display="flex") -> dict:
    return {"left": left, "right": left + width, "top": 0.0, "bottom": height,
            "width": width, "height": height, "gapToViewportRight": gap, "display": display}


def good_measured(view="full") -> dict:
    data = {
        "__viewport": "1280x820", "__innerWidth": 1280, "__docScrollWidth": 1280,
        ".app": [element(0, 1280, 820, 0)],
        ".topbar": [element(280, 1000, 78, 280)],
        ".search": [element(300, 600, 40, 400)],
        ".top-actions": [element(950, 300, 40, 30)],
        ".topbar-brand": [element(290, 120, 22, 990)],
        ".winctl": [element(1150, 120, 32, 10)],
        ".winctl-btn": [element(1160, 32, 32, 88), element(1196, 32, 32, 52),
                        element(1232, 32, 32, 16)],
        ".main": [element(280, 1000, 742, 0)],
        ".kpi-grid": [element(300, 960, 120, 20)],
        "__elementsOverlappingRightEdge": [],
    }
    if view == "full":
        data[".sidebar"] = [element(0, 280, 820, 1000)]
        # The healthy shape: everything fits at the top, so no scrolling is required at all. The
        # scrollable-and-last-hit-testable branch is exercised separately below.
        data["__navReach"] = {"total": 9, "atTop": 9, "afterScroll": 9, "overflow": False,
                              "lastHitInside": True, "clientH": 620, "scrollH": 620}
    return data


class VerdictTests(unittest.TestCase):
    def setUp(self) -> None:
        self.v = geometry.verdict(good_measured("full"), "full")

    def test_a_clean_desktop_measurement_passes_and_names_every_check(self) -> None:
        self.assertTrue(self.v["passed"], json.dumps(self.v["checks"], indent=1))
        self.assertEqual({c["check"] for c in self.v["checks"]},
                         {"no_horizontal_overflow", "topbar_measured", "topbar_not_stacked",
                          "brand_mark_present", "actions_visible", "window_controls_reachable",
                          "action_row_inside_viewport", "rail_always_present",
                          "rail_at_left_edge", "nav_items_reachable"})

    def test_the_rail_must_survive_every_width_the_main_window_can_take(self) -> None:
        # the desktop-only contract in geometry form: b10 used to hide `.sidebar` below 840px.
        measured = good_measured("full")
        del measured[".sidebar"]
        v = geometry.verdict(measured, "full")
        self.assertFalse(v["passed"])
        self.assertFalse([c for c in v["checks"] if c["check"] == "rail_always_present"][0]["pass"])

        measured = good_measured("full")
        measured[".sidebar"] = [element(0, 120, 820, 1160)]
        self.assertFalse([c for c in geometry.verdict(measured, "full")["checks"]
                          if c["check"] == "rail_always_present"][0]["pass"])

    def test_content_pushed_past_the_right_edge_fails(self) -> None:
        measured = good_measured("full")
        measured[".winctl-btn"][-1]["gapToViewportRight"] = -40.0
        v = geometry.verdict(measured, "full")
        self.assertFalse(v["passed"])
        self.assertIn("clipped", [c for c in v["checks"]
                                  if c["check"] == "window_controls_reachable"][0]["detail"])

    def test_a_hidden_action_row_is_a_failure_not_an_absence_of_problem(self) -> None:
        measured = good_measured("full")
        measured[".top-actions"] = [element(950, 300, 40, 30, display="none")]
        self.assertFalse([c for c in geometry.verdict(measured, "full")["checks"]
                          if c["check"] == "actions_visible"][0]["pass"])

    def test_a_stacked_topbar_fails_the_height_bound(self) -> None:
        # the measured phone-shape defect: four action buttons stacked one per row at 320px CSS.
        measured = good_measured("full")
        measured[".topbar"] = [element(280, 1000, 263, 280)]
        self.assertFalse([c for c in geometry.verdict(measured, "full")["checks"]
                          if c["check"] == "topbar_not_stacked"][0]["pass"])

    def test_a_passing_detail_says_what_was_measured(self) -> None:
        # On the runner the gate logged `topbar_measured PASS no .topbar element`, which reads as a missing
        # element while the next line reports a height. A PASS detail must name the quantity it passed on.
        detail = [c for c in self.v["checks"] if c["check"] == "topbar_measured"][0]["detail"]
        self.assertIn("height=", detail)
        self.assertIn("found", detail)
        self.assertNotIn("no .topbar element", detail)

        measured = good_measured("full")
        del measured[".topbar"]
        absent = [c for c in geometry.verdict(measured, "full")["checks"]
                  if c["check"] == "topbar_measured"][0]
        self.assertFalse(absent["pass"])
        self.assertIn("MISSING", absent["detail"])

    def test_horizontal_overflow_fails(self) -> None:
        measured = good_measured("full")
        measured["__docScrollWidth"] = 1400
        self.assertFalse(geometry.verdict(measured, "full")["passed"])

    def test_a_missing_brand_mark_fails(self) -> None:
        measured = good_measured("full")
        del measured[".topbar-brand"]
        self.assertFalse([c for c in geometry.verdict(measured, "full")["checks"]
                          if c["check"] == "brand_mark_present"][0]["pass"])

    def test_the_compact_view_asserts_the_opposite_rail_contract(self) -> None:
        measured = good_measured("compact")
        self.assertTrue(geometry.verdict(measured, "compact")["passed"])
        measured[".sidebar"] = [element(0, 280, 820, 1000)]
        self.assertFalse([c for c in geometry.verdict(measured, "compact")["checks"]
                          if c["check"] == "compact_has_no_rail"][0]["pass"])


class InstrumentTests(unittest.TestCase):
    def test_the_probe_is_not_bound_to_the_authors_machine(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(r"D:\All projects", text)
        self.assertIn('Path(__file__).resolve().parents[2]', text)

    def test_browser_is_discovered_and_reported_as_a_named_category(self) -> None:
        real = Path(sys.executable)
        with mock.patch.dict(os.environ, {"WL_CHROME": str(real)}):
            self.assertEqual(geometry.find_browser(), str(real))
        # PATH discovery, with no env override and no vendor install dir on disk.
        with mock.patch.dict(os.environ, {"PROGRAMFILES": str(ROOT / "nope"),
                                          "PROGRAMFILES(X86)": str(ROOT / "nope")}), \
                mock.patch.object(geometry.shutil, "which", return_value=str(real)):
            self.assertEqual(geometry.find_browser(), str(real))
        env = {"PATH": str(ROOT / "definitely-not-a-bin")}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(geometry.shutil, "which", return_value=None):
            self.assertIsNone(geometry.find_browser())

    def test_a_tree_without_the_built_bundle_refuses_instead_of_passing(self) -> None:
        scratch = Path(tempfile.mkdtemp(prefix="geometry-gate-selftest-",
                                        dir=ROOT / ".project-local" / "runs"))
        try:
            proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(scratch)],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace")
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertIn("GEOMETRY_GATE_NOT_RUN DIST_ABSENT", proc.stdout)
        finally:
            shutil.rmtree(scratch, ignore_errors=False)

    def test_the_page_session_url_carries_the_port_that_was_asked_for(self) -> None:
        # Chrome builds webSocketDebuggerUrl from the request's Host header, so a portless Host —
        # the shape that gets a 200 from its HTTP endpoint at all — makes it echo a portless URL,
        # and connecting to that refuses. The gate must rebuild the URL from the port it was given.
        target = [{"type": "page",
                   "webSocketDebuggerUrl": "ws://127.0.0.1/devtools/page/ABC123",
                   "url": "http://x/index.html"}]
        with mock.patch.object(geometry, "cdp_list", return_value=target):
            self.assertEqual(geometry.discover_page_ws(59123, tries=1),
                             "ws://127.0.0.1:59123/devtools/page/ABC123")

    def test_each_surface_is_measured_at_its_own_declared_shape(self) -> None:
        # Measuring the compact layout at desktop width proved nothing about the panel.
        self.assertEqual(geometry.WIN_SIZE["full"], "1280,820")
        self.assertEqual(geometry.WIN_SIZE["compact"], "440,780")
        self.assertGreater(geometry.MAX_HEIGHT["compact"], geometry.MAX_HEIGHT["full"],
                           "the 440px panel wraps its bar into more rows than the desktop shell")

    def test_a_missing_evaluate_value_is_reported_not_crashed_on(self) -> None:
        client = geometry.ChromeCDP.__new__(geometry.ChromeCDP)
        with mock.patch.object(client, "send", return_value={"type": "string"}):
            with self.assertRaises(RuntimeError) as caught:
                client.evaluate("1+1")
        self.assertIn("produced no value", str(caught.exception))

    def test_the_chrome_port_is_read_from_the_browser_instead_of_assumed(self) -> None:
        # The gate asks Chrome for port 0 and parses the announced one; a socket reserved first is
        # free again by the time Chrome binds, and Chrome then picks a different port silently.
        line = ("DevTools listening on ws://127.0.0.1:54796/devtools/browser/"
                "5888c269-2647-43f4-9318-4b349e7a1bc8\n")
        self.assertEqual(geometry.LISTEN_RE.search(line).group(1), "54796")
        self.assertIsNone(geometry.LISTEN_RE.search("nothing here yet"))

    def test_refusal_to_run_is_not_reported_as_a_pass(self) -> None:
        # A gate that exits 0 while refusing to measure is the defect G3 records; exit 3 is the
        # only honest answer. The browser is absent by patch, not by launching one.
        scratch = ROOT / ".project-local" / "runs" / "geometry-gate-nobrowser"
        dist = scratch / "apps/observer/frontend/dist"
        dist.mkdir(parents=True, exist_ok=True)
        (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        try:
            with mock.patch.object(geometry, "find_browser", return_value=None), \
                    mock.patch.object(sys, "argv", ["x", "--root", str(scratch)]), \
                    mock.patch("builtins.print") as printed:
                self.assertEqual(geometry.main(), 3)
            self.assertTrue(any("GEOMETRY_GATE_NOT_RUN" in str(c.args[0])
                                for c in printed.call_args_list), printed.call_args_list)
        finally:
            # The fixture is derived test data with no unique bytes; deleting it here is the
            # ERR-140 rule (never swallow the failure) applied to my own scratch root.
            shutil.rmtree(scratch)
            self.assertFalse(scratch.exists())


class NavReachabilityTests(unittest.TestCase):
    """The check that was missing while the rail was silently clipped 14 of its 23 items.

    Each case is a shape the shipped skin actually produced, so the guard cannot be satisfied by a
    fixture nobody ever renders: `overflow-y:auto` on a box as tall as its content is the dead
    container, and it is the only failure mode a "is the nav in the DOM" test would have passed.
    """

    def verdict_for(self, reach: dict) -> dict:
        measured = good_measured("full")
        measured["__navReach"] = reach
        return geometry.verdict(measured, "full")

    def check(self, verdict: dict) -> dict:
        return next(c for c in verdict["checks"] if c["check"] == "nav_items_reachable")

    def test_the_dead_container_that_shipped_fails_the_check(self) -> None:
        # Measured 2026-10-08 at 1386x807: clientH == scrollH == 1496 with 23 buttons and 9 visible.
        dead = self.check(self.verdict_for({"total": 23, "atTop": 9, "afterScroll": 9, "overflow": False,
                                            "lastHitInside": False, "clientH": 1496, "scrollH": 1496}))
        self.assertFalse(dead["pass"], dead)
        self.assertIn("overflow=False", dead["detail"])

    def test_a_live_scroll_container_that_reveals_the_last_item_passes(self) -> None:
        # The shape after the fix: clientH 595 < scrollH 1505, and the last item is hit-testable once
        # the rail is scrolled to its end.
        live = self.check(self.verdict_for({"total": 23, "atTop": 9, "afterScroll": 11, "overflow": True,
                                            "lastHitInside": True, "clientH": 595, "scrollH": 1505}))
        self.assertTrue(live["pass"], live)

    def test_scrolling_that_still_never_reveals_the_last_item_fails(self) -> None:
        # A box that reports overflow but whose last row cannot be brought under the pointer -- clipped
        # by an ancestor, or covered by the top bar -- is the failure the hit-test exists to catch.
        covered = self.check(self.verdict_for({"total": 23, "atTop": 9, "afterScroll": 11, "overflow": True,
                                              "lastHitInside": False, "clientH": 595, "scrollH": 1505}))
        self.assertFalse(covered["pass"], covered)

    def test_a_rail_that_renders_nothing_cannot_claim_reachability(self) -> None:
        empty = self.check(self.verdict_for({"total": 0, "atTop": 0, "afterScroll": 0, "overflow": False,
                                             "lastHitInside": False, "clientH": 0, "scrollH": 0}))
        self.assertFalse(empty["pass"], empty)
        self.assertIn("rendered nothing", empty["detail"])

    def test_a_short_rail_passes_without_needing_to_scroll(self) -> None:
        fits = self.check(self.verdict_for({"total": 4, "atTop": 4, "afterScroll": 4, "overflow": False,
                                            "lastHitInside": True, "clientH": 300, "scrollH": 300}))
        self.assertTrue(fits["pass"], fits)


if __name__ == "__main__":
    unittest.main(verbosity=2)
