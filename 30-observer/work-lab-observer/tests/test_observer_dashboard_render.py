"""Regression tests for the Observer dashboard canonical-schema rendering.

The Python server-rendered dashboard must render the canonical projection
(`to_dashboard()` shape) — summary/projects/usage/ci — not the retired
event-rebuild schema (overview/tasks). These tests lock the contract so the
dashboard never silently renders "暂无观测事件" again when canonical data exists.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from observer_canonical import open_canonical_reader

REPO = Path(__file__).resolve().parents[3]  # WORK-LAB root
OBS = Path(__file__).resolve().parents[1]  # 30-observer/work-lab-observer


def _canonical_projection() -> dict:
    store_path = (
        REPO / ".hermes" / "task-runtime" / "workflow" / "canonical.sqlite"
    )
    if not store_path.exists():
        raise unittest.SkipTest("canonical.sqlite not present in this checkout")
    reader = open_canonical_reader(store_path)
    try:
        return reader.to_dashboard()
    finally:
        reader.store.close()


class DashboardCanonicalRenderTests(unittest.TestCase):
    def test_full_render_contains_project_rows(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "observer_dashboard", OBS / "scripts" / "observer_dashboard.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("sys.argv", ["observer_dashboard.py"]):
            spec.loader.exec_module(mod)
        projection = _canonical_projection()
        html = mod._render_full(projection)
        self.assertIn("项目投影", html)
        self.assertIn("WORK-LAB", html)
        self.assertNotIn("暂无观测事件", html)
        self.assertNotIn("由事件重建", html)

    def test_full_render_contains_usage_tokens(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "observer_dashboard", OBS / "scripts" / "observer_dashboard.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("sys.argv", ["observer_dashboard.py"]):
            spec.loader.exec_module(mod)
        projection = _canonical_projection()
        html = mod._render_full(projection)
        self.assertIn("输入 Token", html)
        self.assertIn("总 Token", html)
        self.assertIn("趋势点", html)

    def test_compact_render_contains_project_and_tokens(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "observer_dashboard", OBS / "scripts" / "observer_dashboard.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("sys.argv", ["observer_dashboard.py"]):
            spec.loader.exec_module(mod)
        projection = _canonical_projection()
        html = mod._render_compact(projection)
        self.assertIn("项目投影", html)
        self.assertIn("总 Token", html)
        self.assertNotIn("暂无观测事件", html)

    def test_projection_state_field_maps_status_to_frontend_vocabulary(self) -> None:
        from observer_canonical import _dashboard_project_state

        self.assertEqual(_dashboard_project_state("ACTIVE"), "running")
        self.assertEqual(_dashboard_project_state("REGISTERED"), "idle")
        self.assertEqual(_dashboard_project_state("BLOCKED"), "blocked")
        self.assertEqual(_dashboard_project_state("bogus"), "unknown")

    def test_freshness_mode_vocabulary_maps_to_dashboard_vocabulary(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "observer_dashboard", OBS / "scripts" / "observer_dashboard.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("sys.argv", ["observer_dashboard.py"]):
            spec.loader.exec_module(mod)
        self.assertEqual(mod._freshness_state("LIVE"), "fresh")
        self.assertEqual(mod._freshness_state("STALE"), "stale")
        self.assertEqual(mod._freshness_state("SNAPSHOT"), "stale")
        self.assertEqual(mod._freshness_state("OFFLINE"), "offline")
        self.assertEqual(mod._freshness_state("UNKNOWN"), "unknown")
        self.assertEqual(mod._quality_cn("fresh"), "实时")
        self.assertEqual(mod._quality_cn("stale"), "滞后")
        self.assertEqual(mod._quality_cn("offline"), "离线")
        self.assertEqual(mod._quality_tone("fresh"), "#10b981")
        self.assertEqual(mod._quality_tone("stale"), "#f5b544")

    def test_full_render_maps_live_freshness_to_fresh(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "observer_dashboard", OBS / "scripts" / "observer_dashboard.py"
        )
        mod = importlib.util.module_from_spec(spec)
        with patch("sys.argv", ["observer_dashboard.py"]):
            spec.loader.exec_module(mod)
        projection = {
            "summary": {"tasks": {}},
            "quality": {"freshness": "LIVE", "integrity": "ok", "telemetryEvents": 0},
            "usage": {},
            "ci": {},
            "projects": [],
        }
        html = mod._render_full(projection)
        self.assertIn("实时", html)
        self.assertNotIn("STALE", html)


if __name__ == "__main__":
    unittest.main()
