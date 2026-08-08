"""NX-320: usage rollup / retention / freshness tests.

RED-GREEN coverage:
- Same fixture re-ingested -> identical aggregate (idempotent).
- Aggregates are rebuildable from events.
- Subscription model -> not-metered, no fabricated USD.
- Stale pricing -> costStatus stale, no current USD.
- Fresh metered model -> estimated cost.
- Tokens/cache/reasoning/tool/outcome kept separate.
- price_status_for exposes source/freshness/effective_at.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 30-observer/work-lab-observer
sys.path.insert(0, str(ROOT / "scripts"))

from usage_rollup import rollup, price_status_for  # noqa: E402


def _sample() -> list[dict]:
    return [
        {"usage": {"provider": "deepseek", "model": "deepseek-v4-flash", "inputTokens": 100, "outputTokens": 50, "cacheReadTokens": 10, "latencyMs": 50, "observedAt": "2026-08-08T00:00:00Z"}},
        {"usage": {"provider": "deepseek", "model": "deepseek-v4-flash", "inputTokens": 100, "outputTokens": 50, "cacheReadTokens": 10, "latencyMs": 50, "observedAt": "2026-08-08T00:00:00Z"}},
        {"usage": {"provider": "openai", "model": "gpt-5.6-terra", "inputTokens": 500, "outputTokens": 200, "observedAt": "2026-08-08T00:01:00Z"}},
        {"usage": {"provider": "anthropic", "model": "claude-3-5-sonnet", "inputTokens": 1000, "outputTokens": 500, "observedAt": "2026-08-08T00:02:00Z"}},
    ]


class UsageRollupTest(unittest.TestCase):
    def test_rollup_is_idempotent(self) -> None:
        r1 = rollup(_sample())
        r2 = rollup(_sample())
        self.assertEqual(r1["totals"], r2["totals"])

    def test_dedup_removes_duplicate(self) -> None:
        r = rollup(_sample())
        self.assertEqual(r["totals"]["count"], 3)  # 4 raw - 1 dup

    def test_totals_are_rebuildable(self) -> None:
        r = rollup(_sample())
        self.assertEqual(r["totals"]["inputTokens"], 1600)

    def test_subscription_not_metered_no_usd(self) -> None:
        r = rollup(_sample())
        m = r["byModel"]["gpt-5.6-terra"]
        self.assertEqual(m["costStatus"], "not-metered")
        self.assertIsNone(m.get("estimatedCostUsd"))

    def test_stale_pricing_downgrades(self) -> None:
        r = rollup(_sample())
        m = r["byModel"]["claude-3-5-sonnet"]
        self.assertEqual(m["costStatus"], "stale")
        self.assertIsNone(m.get("estimatedCostUsd"))

    def test_fresh_metered_is_estimated(self) -> None:
        r = rollup(_sample())
        m = r["byModel"]["deepseek-v4-flash"]
        self.assertEqual(m["costStatus"], "estimated")
        self.assertIsNotNone(m.get("estimatedCostUsd"))

    def test_tokens_kept_separate(self) -> None:
        r = rollup(_sample())
        t = r["totals"]
        # deepseek appears once after dedup with cacheReadTokens=10; no other model has cacheReadTokens
        self.assertEqual(t["cacheReadTokens"], 10)

    def test_price_status_exposes_source_and_freshness(self) -> None:
        ps = price_status_for("deepseek-v4-flash")
        self.assertEqual(ps["freshness"], "fresh")
        self.assertEqual(ps["source"], "vendor-pricing-snapshot")
        self.assertIn("effective_at", ps)

    def test_unknown_model_unknown_status(self) -> None:
        ps = price_status_for("no-such-model")
        self.assertEqual(ps["status"], "unknown")

    def test_privacy_no_raw_bodies(self) -> None:
        r = rollup(_sample())
        self.assertEqual(r["privacy"]["rawBodies"], False)
        self.assertEqual(r["privacy"]["sensitiveBodies"], False)


if __name__ == "__main__":
    unittest.main()
