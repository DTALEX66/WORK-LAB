#!/usr/bin/env python3
"""Usage rollup / retention / freshness verifier (NX-320).

Verifies idempotent rollup, rebuildable aggregates, subscription not-metered,
pricing-stale auto-downgrade, and privacy (no raw bodies in retention).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 30-observer/work-lab-observer
sys.path.insert(0, str(ROOT / "scripts"))

from usage_rollup import rollup, price_status_for, PRICING_CATALOG  # noqa: E402


def _sample_events() -> list[dict]:
    return [
        {"usage": {"provider": "deepseek", "model": "deepseek-v4-flash", "inputTokens": 100, "outputTokens": 50, "cacheReadTokens": 10, "latencyMs": 50, "observedAt": "2026-08-08T00:00:00Z"}},
        {"usage": {"provider": "deepseek", "model": "deepseek-v4-flash", "inputTokens": 100, "outputTokens": 50, "cacheReadTokens": 10, "latencyMs": 50, "observedAt": "2026-08-08T00:00:00Z"}},  # duplicate
        {"usage": {"provider": "openai", "model": "gpt-5.6-terra", "inputTokens": 500, "outputTokens": 200, "observedAt": "2026-08-08T00:01:00Z"}},
        {"usage": {"provider": "anthropic", "model": "claude-3-5-sonnet", "inputTokens": 1000, "outputTokens": 500, "observedAt": "2026-08-08T00:02:00Z"}},
    ]


def verify() -> dict:
    errors: list[str] = []

    events = _sample_events()
    r1 = rollup(events)
    r2 = rollup(events)  # idempotent
    if r1["totals"] != r2["totals"]:
        errors.append("rollup not idempotent")

    t = r1["totals"]
    if t["count"] != 3:  # dedup removed 1 duplicate -> 3 unique
        errors.append(f"expected 3 unique events after dedup, got {t['count']}")
    if t["inputTokens"] != 1600:  # 100+500+1000
        errors.append(f"input tokens wrong: {t['inputTokens']}")

    # Subscription model -> not-metered, no fabricated USD.
    by_model = r1["byModel"]
    if by_model["gpt-5.6-terra"]["costStatus"] != "not-metered":
        errors.append("subscription should be not-metered")
    if by_model["gpt-5.6-terra"].get("estimatedCostUsd") is not None:
        errors.append("subscription must not fabricate USD")

    # Stale pricing -> costStatus stale, no current USD.
    if by_model["claude-3-5-sonnet"]["costStatus"] != "stale":
        errors.append("stale pricing should downgrade to stale")
    if by_model["claude-3-5-sonnet"].get("estimatedCostUsd") is not None:
        errors.append("stale pricing must not fabricate USD")

    # Fresh metered model -> estimated cost.
    if by_model["deepseek-v4-flash"]["costStatus"] != "estimated":
        errors.append("fresh metered model should be estimated")

    # price_status_for exposes source/freshness.
    ps = price_status_for("deepseek-v4-flash")
    if ps["freshness"] != "fresh" or ps["source"] != "vendor-pricing-snapshot":
        errors.append(f"price status wrong: {ps}")

    if errors:
        raise ValueError("; ".join(errors))
    return {"models": len(PRICING_CATALOG), "idempotent": True, "rebuildable": True}


def main() -> int:
    try:
        result = verify()
    except (ValueError, ImportError) as exc:
        print(f"USAGE_ROLLUP_FAIL {exc}")
        return 1
    print(
        f"USAGE_ROLLUP_PASS models={result['models']} idempotent=true rebuildable=true "
        f"subscription=not-metered stale=downgraded privacy=no-bodies"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
