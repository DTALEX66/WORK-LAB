"""Gate: the HUD narrow-strip probe is a verdict, not a printout.

The strip's shape checks lived in `.project-local/runs/cl10/hud_narrow_probe.py`, the project's
designated evidence area: they found real defects, and nothing in CI re-ran them, so a later commit
could re-break a 150px label or eject the pinned footer silently. This file tests the tracked successor,
`scripts/audit/hud_strip_geometry_via_cdp.py`, on its PURE verdict function — every case below is a line
of measurement data, so the assertions are reviewable and run on any checkout without a browser.

The healthy fixture is the shipped shape, read from
`.project-local/runs/cl13/hud-strip-gate-pass-final.json` (generated from that receipt, not retyped).
Each planted fault is a defect this project actually measured or could plausibly re-create, and
each one names the check it is supposed to convict — a control that cannot fail guards nothing.
"""
from __future__ import annotations

import copy
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
SCRIPT = ROOT / "scripts" / "audit" / "hud_strip_geometry_via_cdp.py"

spec = importlib.util.spec_from_file_location("hud_strip_geometry_via_cdp", SCRIPT)
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def viewport(width=150, height=480, scroll=None):
    return {"clientW": width, "clientH": height, "scrollW": scroll if scroll is not None else width,
            "scrollH": height, "innerW": width, "innerH": height, "dpr": 1}


def box(left, top, width, height):
    return {"left": left, "right": round(left + width, 1), "top": top,
            "bottom": round(top + height, 1), "width": width, "height": height}


def control(name="详情", left=21.0, top=395.0, width=24.0, height=16.0,
            visibility="visible", display="block"):
    return {"name": name, "visibility": visibility, "display": display,
            **box(left, top, width, height)}


def ring(role="idle", stroke="rgb(48, 58, 70)", width="3", has_summary=False):
    """One H01 row as the browser reports it.

    `stroke` is the RESOLVED paint (the strip takes it from a --daily-* token now, so an attribute-level
    hex is no longer something a page can show); `role` is the element's own statement of which ring role
    it plays, which is how the hover check finds the lit row.
    """
    return {"hasRing": True, "ringRole": role, "stroke": stroke, "strokeWidth": width,
            "hasSummary": has_summary}


H01_TEXT = ("CO\n额度 UNKNOWN\nHE\n额度 UNKNOWN\nDE\n额度 UNKNOWN\nQO\n额度 UNKNOWN\n"
            "OP\n额度 UNKNOWN\n另有 1 个工具未在此列出（完整列表在主窗口）\n余额\nUNKNOWN\n"
            "项目 1 · 待审 1\n详情")
# The painted page text, verbatim from the receipt: the percentage rule and the UNKNOWN rule read what
# the user can see, not what the source says, so the fixture carries what the browser reported.
BODY_H01 = H01_TEXT + "\nLIVE\n已加载实时投影数据"
BODY_H02 = ("CO\n额度 UNKNOWN\nCodex：窗口 待确认 · 数值 UNKNOWN · 重置时间 待确认\nHE\n额度 UNKNOWN\n"
            "DE\n额度 UNKNOWN\nQO\n额度 UNKNOWN\nOP\n额度 UNKNOWN\n"
            "另有 1 个工具未在此列出（完整列表在主窗口）\n余额\nUNKNOWN\n项目 1 · 待审 1\n详情\n"
            "LIVE\n已加载实时投影数据")
BODY_H03 = ("CO\nCodex\n\n账户 UNKNOWN · 额度窗口 待确认\n\n当前会话\nUNKNOWN\n重置 待确认\n周额度\n"
            "UNKNOWN\n重置 待确认\n周上限 · Codex\nUNKNOWN\n重置 待确认\n\n"
            "以上三项是参考面板的额度维度；当前快照未提供任何额度字段，全部保持 UNKNOWN。\n\n更新时间\n"
            "2026/10/25 09:00:00\n相关会话\n2 条执行记录\n关联项目\nWORK-LAB、DESIGN-LAB 界面与资产\n"
            "Tokens\n24h · UNKNOWN\n\n无用量序列数据：不绘制柱状图，不虚构数值。\n\n返回面板\n提醒\n"
            "LIVE\n已加载实时投影数据")
BODY_H04 = ("外部回复提醒\n\n工具：Codex · 关联项目：WORK-LAB\n\n新回复\n✕\n\n启动与依赖排查脚本已就绪\n\n"
            "当前数据源未提供外部回复事件，摘要保持 待确认；外部回复不等于系统确认，审批回到原工具处理。\n\n"
            "时间：2026/10/25 09:00:00\n项目: work-lab\n查看相关用量\n返回外部工具查看 ↗\n"
            "LIVE\n已加载实时投影数据")
READY_WAIT = {"ms": 0, "mounted": True, "selector": "[data-hud-frame]", "budgetMs": 24000,
              "evaluateTimeoutS": 60.0}
QUOTA_ROWS = [
    {"text": "当前会话UNKNOWN重置 待确认", "boxes": [{"w": 6, "h": 6}, {"w": 48, "h": 4}]},
    {"text": "周额度UNKNOWN重置 待确认", "boxes": [{"w": 6, "h": 6}, {"w": 48, "h": 4}]},
    {"text": "周上限 · CodexUNKNOWN重置 待确认", "boxes": [{"w": 6, "h": 6}, {"w": 48, "h": 4}]},
]


# The rows the fixture's declared roles put in the strip, in card order. Six of the nine fixture
# adapters declare `agent_runtime`; the strip shows five and says the sixth is capped, so the panel
# (which is not capped) reports all six.
STRIP_AGENT_ROWS = ["codex", "hermes", "deepseek-harness", "qoder", "fixture-agent-a"]
PANEL_AGENT_ROWS = STRIP_AGENT_ROWS + ["fixture-agent-b"]


def strip_h01() -> dict:
    return {
        "viewport": viewport(), "hudFrame": "native-strip", "hudState": "h01", "shell": None,
        "h01": {"rect": box(8, 22, 134, 402), "text": H01_TEXT},
        "rows": [ring() for _ in range(5)] + [
            {"hasRing": False, "ringRole": None, "stroke": None, "strokeWidth": None, "hasSummary": False},
            {"hasRing": False, "ringRole": None, "stroke": None, "strokeWidth": None, "hasSummary": False}],
        "agentMarks": STRIP_AGENT_ROWS,
        "summary": None, "switcherButtons": 0, "switcherRect": None, "dragRegions": 1,
        "footer": box(8, 447, 134, 25), "quotaRows": None, "nav": [], "labelLines": [],
        "hoverDispatch": "not-requested", "bodyText": BODY_H01, "readyWait": READY_WAIT,
        "ready": True, "readyWaitMs": 2, "readyProbe": "an adapter ring row is painted",
        "readyBudgetMs": gate.READY_BUDGET_MS,
        "controls": [control(), control("HUD 设置", 128, 457, 14, 14)],
    }


def strip_h02() -> dict:
    surface = strip_h01()
    surface["h01"] = {"rect": box(8, 22, 119, 496),
                      "text": H01_TEXT.replace("HE\n额度 UNKNOWN",
                                               "Codex：窗口 待确认 · 数值 UNKNOWN · 重置时间 待确认\nHE\n额度 UNKNOWN")}
    surface["bodyText"] = BODY_H02
    surface["rows"] = [ring("active", "rgb(251, 191, 36)", "3.5", True)] + [ring() for _ in range(4)] + surface["rows"][5:]
    surface["summary"] = {**box(21, 75, 93, 90), "insideLi": True, "insideH01Row": True,
                          "scrollerOverflow": 94}
    surface["hoverDispatch"] = "dispatched"
    surface["controls"] = [control(left=21, top=489), control("HUD 设置", 128, 457, 14, 14)]
    return surface


def strip_h03() -> dict:
    surface = strip_h01()
    surface.update({"hudState": "h03", "h01": None, "rows": [], "quotaRows": copy.deepcopy(QUOTA_ROWS),
                    "bodyText": BODY_H03,
                    "controls": [control("返回面板", 25, 859, 48, 16),
                                 control("HUD 设置", 128, 457, 14, 14)]})
    return surface


def strip_h04() -> dict:
    surface = strip_h03()
    surface.update({"hudState": "h04", "quotaRows": None, "bodyText": BODY_H04,
                    "labelLines": [{"text": "外部回复提醒", "fontSize": 14,
                                    "lines": [{"text": "外部回复", "width": 56},
                                              {"text": "提醒", "width": 28}]}],
                    "controls": [control("关闭提醒", 87, 133, 13.1, 24),
                                 control("HUD 设置", 128, 457, 14, 14)]})
    return surface


def panel_h01() -> dict:
    return {
        "viewport": viewport(440, 680), "hudFrame": "panel", "hudState": "h01", "shell": None,
        "h01": {"rect": box(137.5, 217, 150, 368), "text": H01_TEXT},
        "rows": [ring() for _ in range(6)], "agentMarks": PANEL_AGENT_ROWS,
        "summary": None, "switcherButtons": 4,
        "switcherRect": box(131.6, 597, 161.9, 24), "dragRegions": 1, "footer": None,
        "quotaRows": None, "nav": [], "labelLines": [], "hoverDispatch": "not-requested",
        "readyWait": READY_WAIT, "ready": True, "readyWaitMs": 1,
        "readyProbe": "an adapter ring row is painted", "readyBudgetMs": gate.READY_BUDGET_MS,
        "controls": [control("通知", 134, 16, 38, 30), control("关闭窗口", 391, 21, 32, 32)],
    }


def daily_home() -> dict:
    return {
        "viewport": viewport(1280, 820), "hudFrame": None, "hudState": None, "shell": "daily",
        "h01": None, "rows": [], "summary": None, "switcherButtons": 0, "switcherRect": None,
        "dragRegions": 1, "footer": None, "quotaRows": None, "labelLines": [],
        "hoverDispatch": "not-requested", "readyWait": READY_WAIT,
        "ready": True, "readyWaitMs": 0, "readyProbe": None, "readyBudgetMs": None,
        "nav": [{"label": label, "rect": box(12, top, 151, 36)}
                for label, top in (("项目", 96), ("问题与经验", 136), ("我的工具", 176), ("设置", 726))],
        "controls": [control("全局搜索", 230.6, 9.5, 560, 32), control("关闭窗口", 1231, 21, 32, 32)],
    }


def strip_settings() -> dict:
    """H01 with the footer gear pressed: the same strip, plus the block the click opens."""
    surface = strip_h01()
    surface["settingsDispatch"] = "clicked"
    surface["settings"] = {
        **box(8, 380, 134, 62),
        "text": "数据源：LIVE；修订 1。主题与更多设置在主窗口设置页。\n收起",
        "expanded": "true", "insideFrame": True, "closeText": "收起",
        "closeRect": box(21, 420, 28, 16), "fontSizes": [12.0, 12.0, 12.0], "controlCount": 1,
    }
    surface["controls"] = surface["controls"] + [control("收起", 21, 420, 28, 16)]
    return surface


def good_measurement() -> dict:
    """Every surface the gate declares, at the shape the shipped bundle renders."""
    return {"strip-h01": strip_h01(), "strip-h02": strip_h02(), "strip-h03": strip_h03(),
            "strip-h04": strip_h04(), "strip-settings": strip_settings(),
            "panel-h01": panel_h01(), "daily-home": daily_home()}


def expected_check_names() -> set:
    names = set()
    for spec_row in gate.SURFACES:
        slug = spec_row["name"].replace("-", "_")
        names |= {f"{slug}_measured", f"{slug}_no_horizontal_overflow",
                  f"{slug}_no_unreachable_control", f"{slug}_no_label_shatters_to_one_character",
                  f"{slug}_no_label_leaves_a_single_glyph_alone",
                  }
        if spec_row.get("readyProbe"):
            names.add(f"{slug}_fixture_snapshot_reached_the_surface")
        if spec_row["kind"] == "strip":
            names |= {f"{slug}_footer_pinned_in_viewport", f"{slug}_state_renders_as_declared",
                      f"{slug}_state_switcher_is_not_painted"}
        if spec_row.get("openSettings"):
            names |= {f"{slug}_gear_opens_the_settings_block",
                      f"{slug}_settings_block_is_readable_and_dismissible"}
    return names | {
        "strip_frame_is_the_native_strip_not_the_panel", "strip_has_a_drag_surface",
        "h01_card_stays_inside_the_declared_strip_width",
        "hud_monitors_only_declared_agent_runtimes",
        "hover_reveals_the_summary_inside_the_row", "hover_summary_is_readable_without_scrolling",
        "hover_row_is_the_one_highlighted_amberly", "hover_keeps_h01_mounted",
        "h03_quota_rows_are_three_slots_and_honest", "strip_never_fabricates_a_percentage",
        "strip_keeps_quota_unknown_instead_of_zero", "panel_keeps_the_four_state_switcher",
        "daily_renders_the_four_entries", "daily_settings_sits_below_the_four_entries"}


class VerdictTests(unittest.TestCase):
    def setUp(self) -> None:
        self.v = gate.verdict(good_measurement())

    def test_a_clean_strip_measurement_passes_and_names_every_check(self) -> None:
        self.assertTrue(self.v["passed"], json.dumps([c for c in self.v["checks"] if not c["pass"]],
                                                    indent=1, ensure_ascii=False))
        self.assertEqual({c["check"] for c in self.v["checks"]}, expected_check_names())

    def test_the_expected_names_cover_every_declared_surface(self) -> None:
        # Guard the guard: a surface added to SURFACES without extending the expectation above would
        # otherwise make the set-equality test pass by forgetting a whole column of claims.
        for spec_row in gate.SURFACES:
            slug = spec_row["name"].replace("-", "_")
            self.assertIn(f"{slug}_measured", expected_check_names())

    def test_a_passing_detail_says_what_was_measured(self) -> None:
        detail = self.check("strip_h01_footer_pinned_in_viewport")["detail"]
        self.assertIn("bottom=472", detail)
        self.assertIn("viewportHeight=480", detail)

    def check(self, name: str, measured=None) -> dict:
        verdict = gate.verdict(measured if measured is not None else good_measurement())
        return next(c for c in verdict["checks"] if c["check"] == name)

    def test_a_surface_harvested_before_the_snapshot_lands_is_not_a_pass(self) -> None:
        # The runner-side race this gate would otherwise have: the frame mounts on the first render, the
        # fixture snapshot arrives after it, and a harvest taken in between sees no rows — so the hover
        # and quota claims would be about a shape the product does not ship.
        measured = good_measurement()
        measured["strip-h01"]["ready"] = False
        measured["strip-h01"]["readyWaitMs"] = gate.READY_BUDGET_MS
        bad = self.check("strip_h01_fixture_snapshot_reached_the_surface", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("condition='an adapter ring row is painted'", bad["detail"])
        self.assertIn(f"waitedMs={gate.READY_BUDGET_MS}", bad["detail"])
        self.assertFalse(gate.verdict(measured)["passed"])

        measured = good_measurement()
        del measured["panel-h01"]["ready"]
        self.assertFalse(self.check("panel_h01_fixture_snapshot_reached_the_surface", measured)["pass"])

    def test_readiness_is_only_claimed_where_the_surface_needs_data(self) -> None:
        # The daily entry's four claims are about the nav, which renders without a snapshot; inventing a
        # data-readiness check for it would fail the surface for a reason that has no bearing on it.
        names = {c["check"] for c in self.v["checks"]}
        self.assertIn("strip_h01_fixture_snapshot_reached_the_surface", names)
        self.assertNotIn("daily_home_fixture_snapshot_reached_the_surface", names)

    # --- the label family, which is the reason this gate exists -------------------------------

    def test_a_label_broken_one_character_per_line_is_convicted(self) -> None:
        measured = good_measurement()
        measured["strip-h03"]["labelLines"] = [{
            "text": "返回面板", "fontSize": 12,
            "lines": [{"text": ch, "width": 12} for ch in "返回面板"]}]
        bad = self.check("strip_h03_no_label_shatters_to_one_character", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("返回面板", bad["detail"])
        self.assertFalse(gate.verdict(measured)["passed"])

    def test_one_ideograph_left_alone_on_a_line_fails_without_looking_shattered(self) -> None:
        # The measured pre-fix H03 reset row: 「重置时间 待确」 at 75.3px is a wide line, so the
        # shatter rule stayed green while the second line held nothing but 「认」. The two rules catch
        # different defects, and this case is the proof that they are not the same assertion twice.
        measured = good_measurement()
        measured["strip-h03"]["labelLines"] = [{
            "text": "重置时间 待确认", "fontSize": 12,
            "lines": [{"text": "重置时间 待确", "width": 75.3}, {"text": "认", "width": 12}]}]
        self.assertTrue(self.check("strip_h03_no_label_shatters_to_one_character", measured)["pass"],
                        "the widest line is 75.3px: this is a wrap, not a shatter")
        lonely = self.check("strip_h03_no_label_leaves_a_single_glyph_alone", measured)
        self.assertFalse(lonely["pass"], lonely)
        self.assertIn("认", lonely["detail"])

    def test_a_number_left_alone_on_a_line_is_not_a_shattered_label(self) -> None:
        # 「2 个已注册项目」 breaks after the count. Failing that would push the product toward
        # widening boxes for the wrong reason, so the exception is asserted, not just intended.
        measured = good_measurement()
        measured["daily-home"]["labelLines"] = [{
            "text": "2 个已注册项目", "fontSize": 12,
            "lines": [{"text": "2", "width": 6.5}, {"text": "个已注册项目", "width": 75.3}]}]
        self.assertTrue(self.check("daily_home_no_label_leaves_a_single_glyph_alone", measured)["pass"])
        self.assertTrue(self.check("daily_home_no_label_shatters_to_one_character", measured)["pass"])

    def test_a_label_harvest_that_is_not_a_list_fails_instead_of_passing(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["labelLines"] = None
        self.assertFalse(self.check("strip_h01_no_label_shatters_to_one_character", measured)["pass"])
        self.assertFalse(self.check("strip_h01_no_label_leaves_a_single_glyph_alone", measured)["pass"])

    def test_the_type_floor_is_not_owned_here_anymore(self) -> None:
        # Two gates reading one standard means two thresholds and two exception lists to keep in step.
        # `scripts/audit/text_legibility_via_cdp.py --shell-surfaces` judges the 12px floor and the AA
        # ratio on these same surfaces, so this gate harvests geometry only.
        names = {c["check"] for c in self.v["checks"]}
        self.assertFalse([n for n in names if "text_meets_the_12px_floor" in n], sorted(names))
        self.assertNotIn("smallText", gate.MEASURE_JS)
        self.assertFalse(hasattr(gate, "TEXT_FLOOR_EXCEPTIONS"))

    def test_a_control_pushed_past_the_strip_edge_is_named(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["controls"].append(control("详情", 128, 395, 44, 16))
        bad = self.check("strip_h01_no_unreachable_control", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("详情", bad["detail"])

    def test_the_off_screen_measuring_sizer_is_not_convicted_as_an_unreachable_control(self) -> None:
        # Measured 2026-10-25 on the first run of this gate: the compact shell's `.action-sizer` lives
        # at top/left -9999 with `visibility:hidden`, and a rect-only rule reported five perfectly
        # reachable panel controls as pushed outside the window. Presence of a box is not paint.
        measured = good_measurement()
        measured["panel-h01"]["controls"] += [control("通知", -9999, -9999, 38, 30, visibility="hidden"),
                                              control("检测环境工具", -9953, -9999, 50, 30,
                                                      visibility="hidden")]
        self.assertTrue(self.check("panel_h01_no_unreachable_control", measured)["pass"])

    def test_a_surface_that_paints_no_control_does_not_pass_reachability(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["controls"] = []
        bad = self.check("strip_h01_no_unreachable_control", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("nothing painted", bad["detail"])

    def test_horizontal_overflow_fails_and_a_wrong_viewport_refuses_to_judge(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["viewport"]["scrollW"] = 172
        self.assertFalse(self.check("strip_h01_no_horizontal_overflow", measured)["pass"])

        measured = good_measurement()
        measured["strip-h01"]["viewport"] = viewport(482, 480)  # Chrome clamps a too-narrow window
        self.assertFalse(self.check("strip_h01_measured", measured)["pass"])
        self.assertIn("not judged",
                      self.check("strip_h01_no_horizontal_overflow", measured)["detail"])

    def test_a_missing_surface_is_a_failure_not_an_absence_of_problem(self) -> None:
        measured = good_measurement()
        del measured["strip-h04"]
        bad = self.check("strip_h04_measured", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("no entry for it", bad["detail"])
        self.assertFalse(self.check("strip_h04_footer_pinned_in_viewport", measured)["pass"])
        self.assertFalse(gate.verdict(measured)["passed"])

    # --- H01: the strip is its own surface, not the panel squeezed ------------------------------

    def test_a_strip_that_renders_the_panel_frame_fails(self) -> None:
        measured = good_measurement()
        measured["strip-h03"]["hudFrame"] = "panel"
        self.assertFalse(self.check("strip_frame_is_the_native_strip_not_the_panel", measured)["pass"])

    def test_a_strip_that_paints_the_four_state_switcher_fails(self) -> None:
        # The switcher is the 440px panel's affordance; the strip reaches the other states by deep link.
        measured = good_measurement()
        measured["strip-h03"]["switcherButtons"] = 4
        self.assertFalse(self.check("strip_h03_state_switcher_is_not_painted", measured)["pass"])

    def test_a_state_the_url_declared_but_the_render_ignored_is_caught(self) -> None:
        # `?hs=h03` is the only way H03 is reached in the native strip; a render that ignored it would
        # otherwise be judged against the wrong content and could still look tidy.
        measured = good_measurement()
        measured["strip-h03"]["hudState"] = "h01"
        self.assertFalse(self.check("strip_h03_state_renders_as_declared", measured)["pass"])

    def test_the_h01_card_may_not_outgrow_the_declared_strip_width(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["h01"]["rect"] = box(8, 22, 168, 402)
        self.assertFalse(self.check("h01_card_stays_inside_the_declared_strip_width", measured)["pass"])

    def test_a_strip_without_a_drag_surface_is_unmovable_and_fails(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["dragRegions"] = 0
        self.assertFalse(self.check("strip_has_a_drag_surface", measured)["pass"])

    # --- who the monitor is allowed to draw -----------------------------------------------------

    def test_the_clean_hud_draws_only_clients_that_declare_an_agent_role(self) -> None:
        # Non-vacuity: the check is not satisfied by an empty row list, and the fixture's own excluded
        # names really are absent from the recorded text.
        self.assertTrue(self.check("hud_monitors_only_declared_agent_runtimes")["pass"])
        self.assertTrue(gate.AGENT_FIXTURE_IDS)
        self.assertIn("github", {str(c["clientId"]).lower() for c in gate.FIXTURE_SNAPSHOT["adapterCapabilities"]
                                 if c.get("role") != gate.AGENT_ROLE})

    def test_a_strip_row_for_a_client_that_declares_no_agent_role_fails(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["agentMarks"] = ["codex", "github", "hermes", "qoder", "fixture-agent-a"]
        self.assertFalse(self.check("hud_monitors_only_declared_agent_runtimes", measured)["pass"])

    def test_an_excluded_client_painted_in_the_panel_fails_even_with_no_stray_row(self) -> None:
        measured = good_measurement()
        measured["panel-h01"]["agentMarks"] = PANEL_AGENT_ROWS
        measured["panel-h01"]["bodyText"] = H01_TEXT + "\nGitHub\n"
        self.assertFalse(self.check("hud_monitors_only_declared_agent_runtimes", measured)["pass"])

    def test_a_hud_surface_that_reported_no_rows_is_not_a_pass_by_omission(self) -> None:
        measured = good_measurement()
        for name in ("strip-h01", "strip-h02", "strip-h03", "strip-h04", "panel-h01"):
            measured[name]["agentMarks"] = []
        self.assertFalse(self.check("hud_monitors_only_declared_agent_runtimes", measured)["pass"])

    # --- the mini settings block, which only the gear can open ------------------------------------

    def test_a_gear_that_opens_nothing_is_convicted(self) -> None:
        measured = good_measurement()
        measured["strip-settings"]["settings"] = None
        self.assertFalse(self.check("strip_settings_gear_opens_the_settings_block", measured)["pass"])
        self.assertFalse(
            self.check("strip_settings_settings_block_is_readable_and_dismissible", measured)["pass"])

    def test_a_block_the_gear_does_not_report_as_open_is_convicted(self) -> None:
        measured = good_measurement()
        measured["strip-settings"]["settings"]["expanded"] = "false"
        self.assertFalse(self.check("strip_settings_gear_opens_the_settings_block", measured)["pass"])

    def test_a_settings_block_pushed_below_the_window_fails(self) -> None:
        measured = good_measurement()
        measured["strip-settings"]["settings"].update({"top": 470.0, "bottom": 532.0, "height": 62.0})
        self.assertFalse(
            self.check("strip_settings_settings_block_is_readable_and_dismissible", measured)["pass"])

    def test_a_settings_block_with_no_way_to_close_fails(self) -> None:
        measured = good_measurement()
        measured["strip-settings"]["settings"]["closeText"] = ""
        self.assertFalse(
            self.check("strip_settings_settings_block_is_readable_and_dismissible", measured)["pass"])

    def test_the_settings_block_is_not_measured_on_surfaces_that_never_open_it(self) -> None:
        names = {c["check"] for c in self.v["checks"]}
        self.assertIn("strip_settings_gear_opens_the_settings_block", names)
        self.assertFalse([n for n in names if n.endswith("_gear_opens_the_settings_block")
                          and not n.startswith("strip_settings_")], sorted(names))

    # --- the pinned footer, the defect class that started this gate ----------------------------

    def test_a_footer_pushed_below_the_window_fails_by_its_measured_bottom(self) -> None:
        # Measured 2026-10-25 before the structural fix: hovering H02 inside a frame that scrolled
        # itself put the footer at top=874 / bottom=899 of a 480px window — entirely off-screen.
        measured = good_measurement()
        measured["strip-h02"]["footer"] = box(8, 874, 134, 25)
        bad = self.check("strip_h02_footer_pinned_in_viewport", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("bottom=899", bad["detail"])

    def test_a_missing_footer_is_a_failure_not_an_absence_of_problem(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["footer"] = None
        bad = self.check("strip_h01_footer_pinned_in_viewport", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("absence", bad["detail"])

    def test_the_panel_keeps_the_four_state_switcher_the_strip_deliberately_drops(self) -> None:
        measured = good_measurement()
        measured["panel-h01"]["switcherButtons"] = 0
        self.assertFalse(self.check("panel_keeps_the_four_state_switcher", measured)["pass"])

    # --- H02: the hover contract ----------------------------------------------------------------

    def test_a_summary_appended_after_the_list_is_not_the_reference_capsule(self) -> None:
        measured = good_measurement()
        measured["strip-h02"]["summary"]["insideLi"] = False
        bad = self.check("hover_reveals_the_summary_inside_the_row", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn('"insideLi": false', bad["detail"])

    def test_a_summary_below_the_fold_is_convicted_even_when_it_is_inline(self) -> None:
        measured = good_measurement()
        measured["strip-h02"]["summary"].update({"top": 400, "bottom": 620})
        bad = self.check("hover_summary_is_readable_without_scrolling", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("bottom=620", bad["detail"])

    def test_the_hovered_row_must_be_the_only_one_lit_amber(self) -> None:
        # three separate faults, each convicted: a second row lit, the hovered row not lit, and — the
        # new one since the strip took its colour from tokens — a lit row whose RESOLVED stroke is the
        # same paint as the idle rows. The last one is what proves the colour is still measured and not
        # merely declared: warn-mark and line collapsing to one value keeps the roles intact and makes
        # the ring invisible to a user.
        measured = good_measurement()
        measured["strip-h02"]["rows"][2]["ringRole"] = gate.ACTIVE_RING
        bad = self.check("hover_row_is_the_one_highlighted_amberly", measured)
        self.assertFalse(bad["pass"], bad)

        measured = good_measurement()
        measured["strip-h02"]["rows"][0]["ringRole"] = gate.IDLE_RING
        self.assertFalse(self.check("hover_row_is_the_one_highlighted_amberly", measured)["pass"])

        measured = good_measurement()
        measured["strip-h02"]["rows"][0]["stroke"] = measured["strip-h02"]["rows"][1]["stroke"]
        faded = self.check("hover_row_is_the_one_highlighted_amberly", measured)
        self.assertFalse(faded["pass"], faded)
        self.assertIn("colourDiffersFromIdle=False", faded["detail"])

        # and the detector is not blind the other way: a ring that states no role at all is a fault too
        measured = good_measurement()
        measured["strip-h02"]["rows"][1]["ringRole"] = None
        self.assertFalse(self.check("hover_row_is_the_one_highlighted_amberly", measured)["pass"])

    def test_a_hover_that_revealed_nothing_fails_rather_than_reporting_no_problems(self) -> None:
        # This is also the shape of a rejected fixture snapshot: no adapter rows, so no row to hover.
        measured = good_measurement()
        measured["strip-h02"]["summary"] = None
        measured["strip-h02"]["rows"] = []
        self.assertFalse(self.check("hover_reveals_the_summary_inside_the_row", measured)["pass"])
        self.assertFalse(self.check("hover_row_is_the_one_highlighted_amberly", measured)["pass"])

    # --- H03 and the truth rule ----------------------------------------------------------------

    def test_a_percentage_in_the_quota_rows_is_a_fabricated_value(self) -> None:
        measured = good_measurement()
        measured["strip-h03"]["quotaRows"][1]["text"] = "周额度62%重置 3h 后"
        bad = self.check("h03_quota_rows_are_three_slots_and_honest", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("percentage", bad["detail"])
        # The same fabrication painted anywhere else on the strip is caught by the other rule, which
        # reads the page text rather than the quota block.
        measured = good_measurement()
        measured["strip-h03"]["bodyText"] = BODY_H03 + "\n周额度 62%"
        self.assertFalse(self.check("strip_never_fabricates_a_percentage", measured)["pass"])

    def test_a_quota_row_that_states_a_number_instead_of_unknown_fails(self) -> None:
        measured = good_measurement()
        measured["strip-h03"]["quotaRows"][0]["text"] = "当前会话0重置 待确认"
        bad = self.check("h03_quota_rows_are_three_slots_and_honest", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("instead of UNKNOWN", bad["detail"])

    def test_quota_slots_that_were_deleted_to_avoid_lying_fail_too(self) -> None:
        # Dropping the track is how a panel quietly becomes "everything normal": the row would no
        # longer say "there is a dimension here whose value we do not have".
        measured = good_measurement()
        measured["strip-h03"]["quotaRows"][2]["boxes"] = [{"w": 6, "h": 6}]
        self.assertFalse(self.check("h03_quota_rows_are_three_slots_and_honest", measured)["pass"])

        measured = good_measurement()
        measured["strip-h03"]["quotaRows"] = measured["strip-h03"]["quotaRows"][:2]
        self.assertIn("rows=2", self.check("h03_quota_rows_are_three_slots_and_honest",
                                           measured)["detail"])

    def test_the_quota_block_rendering_nothing_is_reported_as_unmeasurable(self) -> None:
        measured = good_measurement()
        measured["strip-h03"]["quotaRows"] = None
        bad = self.check("h03_quota_rows_are_three_slots_and_honest", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("NoneType", bad["detail"])

    def test_the_strip_must_keep_quota_unknown_and_must_not_paint_a_percent_anywhere(self) -> None:
        measured = good_measurement()
        measured["strip-h01"]["h01"]["text"] = H01_TEXT.replace("额度 UNKNOWN", "额度 0")
        self.assertFalse(self.check("strip_keeps_quota_unknown_instead_of_zero", measured)["pass"])

        measured = good_measurement()
        measured["strip-h04"]["bodyText"] = "周额度 45% 已用"
        self.assertFalse(self.check("strip_never_fabricates_a_percentage", measured)["pass"])

    def test_a_surface_that_harvested_no_painted_text_is_not_an_absence_of_percent(self) -> None:
        measured = good_measurement()
        measured["strip-h03"]["bodyText"] = ""
        bad = self.check("strip_never_fabricates_a_percentage", measured)
        self.assertFalse(bad["pass"], bad)
        self.assertIn("strip-h03", bad["detail"])


class InstrumentTests(unittest.TestCase):
    def test_the_probe_is_not_bound_to_the_authors_machine(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(r"D:\All projects", text)
        self.assertIn("Path(__file__).resolve().parents[2]", text)

    def test_the_measured_sizes_are_the_windows_the_desktop_declares(self) -> None:
        # Bound to the machine authority, not restated: if tauri.conf.json re-sizes a window, this fails
        # and the strip contract gets re-opened on purpose instead of drifting with the gate.
        conf = json.loads((ROOT / "apps" / "observer" / "src-tauri" / "tauri.conf.json")
                          .read_text(encoding="utf-8"))
        windows = {w["label"]: w for w in conf["app"]["windows"]}
        self.assertEqual(gate.STRIP, (windows["hud"]["width"], windows["hud"]["height"]))
        self.assertEqual(gate.PANEL, (windows["panel"]["width"], windows["panel"]["height"]))
        self.assertEqual(gate.DAILY, (windows["main"]["width"], windows["main"]["height"]))

    def test_the_strip_surfaces_come_from_the_urls_the_windows_open(self) -> None:
        conf = json.loads((ROOT / "apps" / "observer" / "src-tauri" / "tauri.conf.json")
                          .read_text(encoding="utf-8"))
        hud = {w["label"]: w for w in conf["app"]["windows"]}["hud"]["url"]
        self.assertIn("surface=hud", hud)
        self.assertTrue(any(s["query"].startswith("surface=hud") for s in gate.SURFACES))

    def test_the_hover_event_is_dispatched_on_the_row_not_the_section(self) -> None:
        # React 18 derives onMouseEnter from a bubbling mouseover whose TARGET is the element under the
        # pointer; the first version of the evidence probe dispatched on the section and every row
        # handler stayed un-triggered, which read as "the summary never appears".
        js = gate.MEASURE_JS
        self.assertIn("document.querySelector(H01 + ' li')", js)
        self.assertNotIn("document.querySelector(H01)).dispatchEvent", js)

    def test_line_boxes_come_from_the_platform_not_from_glyph_tops(self) -> None:
        # Instrument defect found while writing this gate: grouping characters by their own rect.top
        # splits one visual line, because a digit's glyph box sits higher than the CJK next to it.
        js = gate.MEASURE_JS
        self.assertIn("whole.selectNodeContents(el)", js)
        self.assertIn("const lineOf = (r) =>", js)

    def test_the_fixture_snapshot_satisfies_the_producer_contract(self) -> None:
        schema = json.loads((ROOT / "packages" / "contracts" / "schemas" / "workflow"
                             / "snapshot-v3.schema.json").read_text(encoding="utf-8"))
        for field in schema["required"]:
            self.assertIn(field, gate.FIXTURE_SNAPSHOT, f"the fixture would be rejected: {field}")
        if schema.get("additionalProperties") is False:
            declared = set(schema["properties"])
            self.assertEqual(sorted(set(gate.FIXTURE_SNAPSHOT) - declared), [])
        # The strip renders rows from `adapterCapabilities`; a fixture the front rejects would silently
        # turn every hover claim into "nothing to hover".
        self.assertGreaterEqual(len(gate.FIXTURE_SNAPSHOT["adapterCapabilities"]), 2)
        for card in gate.FIXTURE_SNAPSHOT["adapterCapabilities"]:
            self.assertTrue(card["clientId"])
            self.assertIsInstance(card["layers"], list)

    def test_the_verdict_is_pure(self) -> None:
        # No filesystem, no browser, and the same bytes in produce the same verdict out — otherwise the
        # CI cases above would be describing a machine rather than a rule.
        first = gate.verdict(good_measurement())
        self.assertEqual(first, gate.verdict(good_measurement()))
        self.assertTrue(gate.verdict(good_measurement())["passed"])
        text = SCRIPT.read_text(encoding="utf-8")
        start = text.index("def verdict(measured: dict)")
        end = text.index("def measure_all(")
        body = text[start:end]
        for call in ("open(", "Path(", "subprocess", "serve_and_eval"):
            self.assertNotIn(call, body, f"the pure section reaches for {call}")

    def test_refusal_to_run_is_not_reported_as_a_pass(self) -> None:
        scratch = Path(tempfile.mkdtemp(prefix="hud-strip-gate-selftest-",
                                        dir=ROOT / ".project-local" / "runs"))
        try:
            proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(scratch)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            self.assertIn("HUD_STRIP_GATE_NOT_RUN DIST_ABSENT", proc.stdout)
        finally:
            shutil.rmtree(scratch, ignore_errors=False)

    def _scratch_tree(self, prefix: str, with_dist: bool) -> Path:
        scratch = Path(tempfile.mkdtemp(prefix=prefix, dir=ROOT / ".project-local" / "runs"))
        if with_dist:
            dist = scratch / "apps" / "observer" / "frontend" / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            (dist / "index.html").write_text("<html></html>", encoding="utf-8")
        return scratch

    def test_a_tree_without_a_browser_refuses_by_name(self) -> None:
        # The refusal has to be reachable on any checkout. Measured on the runner: the
        # workflow-assistance job builds nothing under `apps/observer/frontend/dist`, so pointing at the
        # real tree returned `DIST_ABSENT` where the assertion demanded `BROWSER_NOT_FOUND`. A test whose
        # answer depends on whether somebody ran `npm run build` here is not a gate.
        class NoBrowser:
            @staticmethod
            def find_browser():
                return None

        scratch = self._scratch_tree("hud-strip-nobrowser-", with_dist=True)
        try:
            with mock.patch.object(gate, "load_geometry", return_value=NoBrowser), \
                    mock.patch.object(sys, "argv", ["x", "--root", str(scratch)]), \
                    mock.patch("builtins.print") as printed:
                self.assertEqual(gate.main(), 3)
            self.assertTrue(any("BROWSER_NOT_FOUND" in str(c.args[0]) for c in printed.call_args_list),
                            printed.call_args_list)
        finally:
            shutil.rmtree(scratch)

    def test_bad_input_is_bad_input_whatever_the_machine_has_built(self) -> None:
        # A misspelled `--surface` must come back as exit 2 with the name listed, on a tree that has no
        # dist at all — otherwise the runner reports a typo as DIST_ABSENT and the reader loses the only
        # signal that says what they typed wrong.
        scratch = self._scratch_tree("hud-strip-badname-", with_dist=False)
        try:
            with mock.patch.object(sys, "argv",
                                   ["x", "--root", str(scratch), "--surface", "strip-h9"]), \
                    mock.patch("builtins.print") as printed:
                self.assertEqual(gate.main(), 2)
            self.assertTrue(any("UNKNOWN_SURFACE" in str(c.args[0]) for c in printed.call_args_list),
                            printed.call_args_list)
            self.assertFalse(any("DIST_ABSENT" in str(c.args[0]) for c in printed.call_args_list))
        finally:
            shutil.rmtree(scratch)

    def test_the_receipt_reports_what_the_browser_bootstrap_could_not_clean_up(self) -> None:
        # The gate reuses the geometry probe's Chrome launcher, and that launcher keeps a profile dir it
        # could not delete rather than raising. Reporting nothing would hide a leftover on purpose.
        class Clean:
            RESIDUE: list = []
            ANNOUNCED_MISMATCH: list = []

        class Leaking:
            RESIDUE = ["udf-1792341448-10404 WinError 32"]
            ANNOUNCED_MISMATCH = ["requested 59123, announced 59124"]

        self.assertEqual(gate.browser_leftovers(Clean),
                         {"residue": [], "portAnnouncedMismatch": []})
        reported = gate.browser_leftovers(Leaking)
        self.assertEqual(reported["residue"], ["udf-1792341448-10404 WinError 32"])
        self.assertEqual(reported["portAnnouncedMismatch"], ["requested 59123, announced 59124"])

    def test_an_unknown_surface_name_is_bad_input_not_a_silent_subset(self) -> None:
        with mock.patch.object(sys, "argv", ["x", "--surface", "strip-h9"]), \
                mock.patch("builtins.print") as printed:
            self.assertEqual(gate.main(), 2)
        self.assertTrue(any("UNKNOWN_SURFACE" in str(c.args[0]) for c in printed.call_args_list))

    def test_the_readiness_probes_match_what_each_state_actually_paints(self) -> None:
        # The marker has to be a separate constant so SURFACES can carry it before the fixture literal
        # exists; if the two drift the gate waits for a string the snapshot never paints.
        self.assertEqual(gate.FIXTURE_MARKER,
                         gate.FIXTURE_SNAPSHOT["adapterCapabilities"][0]["displayName"])
        self.assertIn(gate.FIXTURE_MARKER, gate.MARKER_PROBE)
        # And the lesson this gate re-learned while being written: H01 paints initials (`CO`, `HE`) and
        # 额度 UNKNOWN, never the tool name. Waiting for the name on those surfaces times out on a
        # healthy render, so they wait for a ring row instead.
        by_name = {s["name"]: s for s in gate.SURFACES}
        for name in ("strip-h01", "strip-h02", "panel-h01"):
            self.assertEqual(by_name[name]["readyProbe"], gate.RING_ROW_PROBE, name)
        for name in ("strip-h03", "strip-h04"):
            self.assertEqual(by_name[name]["readyProbe"], gate.MARKER_PROBE, name)
        self.assertIsNone(by_name["daily-home"]["readyProbe"])

    def test_the_expression_substitutes_the_selectors_it_declares(self) -> None:
        expr = gate.expression_for({"name": "strip-h02", "hover": True,
                                    "readyProbe": gate.RING_ROW_PROBE,
                                    "readyWhy": "an adapter ring row is painted"})
        self.assertIn("const HOVER = true;", expr)
        self.assertIn("const READY = () => (%s);" % gate.RING_ROW_PROBE, expr)
        self.assertIn("const BUDGET_MS = %d;" % gate.READY_BUDGET_MS, expr)
        self.assertIn("工具额度窄面板", expr)
        for placeholder in ("__HOVER__", "__READY_PROBE__", "__READY_WHY__", "__BUDGET_MS__",
                            "__POLL_MS__", "__H01__", "__SUMMARY__"):
            self.assertNotIn(placeholder, expr)
        # A surface whose claims do not need snapshot data must not wait for one.
        plain = gate.expression_for({"name": "daily-home"})
        self.assertIn("const READY = () => (true);", plain)
        self.assertIn("const ready = READY();", plain)


if __name__ == "__main__":
    unittest.main(verbosity=2)
