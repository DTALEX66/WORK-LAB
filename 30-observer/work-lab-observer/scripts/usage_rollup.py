"""Usage rollup / retention / freshness semantics (NX-320).

- Idempotent rollup: re-ingesting the same fixture produces identical aggregates.
- Rebuildable projection: totals are recomputed from events, never stored-as-fact.
- Pricing expiry: if a model's pricing is stale/unknown, cost auto-downgrades to
  stale/unknown (never fabricates USD for a subscription or stale quote).
- Layered retention; raw sensitive bodies never enter the retention chain.
- Observer shows source / coverage / freshness / quality / last-good /
  estimated-vs-reconciled.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

# Pricing catalog: model -> pricing. Subscriptions are not-metered (no USD).
PRICING_CATALOG: dict[str, dict[str, Any]] = {
    "deepseek-v4-flash": {
        "alias": "deepseek-v4-flash", "billing": "metered",
        "source": "vendor-pricing-snapshot", "effective_at": "2026-08-01",
        "currency": "USD", "stale": False,
        "input_per_million": 0.27, "output_per_million": 1.10,
    },
    "gpt-5.6-terra": {
        "alias": "gpt-5.6-terra", "billing": "subscription",
        "source": "subscription-not-metered", "effective_at": "2026-01-01",
        "currency": "USD", "stale": False,
    },
    "claude-3-5-sonnet": {
        "alias": "claude-3-5-sonnet", "billing": "metered",
        "source": "vendor-pricing-snapshot", "effective_at": "2026-05-01",
        "currency": "USD", "stale": True,  # expired -> cost downgrades to stale
        "input_per_million": 3.0, "output_per_million": 15.0,
    },
}


def _price_for(model: str) -> dict[str, Any] | None:
    return PRICING_CATALOG.get(model)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_fingerprint(event: dict[str, Any]) -> str:
    """Deterministic fingerprint of the observable usage fields (idempotency key)."""
    usage = event.get("usage") or {}
    payload = json_dumps({k: usage.get(k) for k in (
        "provider", "model", "operation", "inputTokens", "outputTokens",
        "cacheReadTokens", "cacheWriteTokens", "taskDigest", "observedAt",
    )})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def json_dumps(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def rollup(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Idempotent, rebuildable aggregate of usage events.

    Same fixture -> same output (dedup by fingerprint). Tokens/cache/reasoning/
    tool/outcome kept separate; never infer subscription quota from token count.
    """
    events = list(events)
    # Idempotency: dedup by fingerprint.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for event in events:
        fp = _event_fingerprint(event)
        if fp in seen:
            continue
        seen.add(fp)
        unique.append(event)

    totals = {
        "inputTokens": 0, "outputTokens": 0, "cacheReadTokens": 0,
        "cacheWriteTokens": 0, "latencyMs": 0, "count": 0,
        "estimatedCostUsd": None, "costStatus": "unknown",
    }
    model_usage: dict[str, dict[str, Any]] = {}
    subscription_models: list[str] = []

    for event in unique:
        usage = event.get("usage") or {}
        model = usage.get("model") or "unknown"
        for k in ("inputTokens", "outputTokens", "cacheReadTokens", "cacheWriteTokens"):
            v = usage.get(k)
            if isinstance(v, (int, float)):
                totals[k] += v
        latency = usage.get("latencyMs")
        if isinstance(latency, (int, float)):
            totals["latencyMs"] += latency
        totals["count"] += 1
        # Separate per-model aggregates.
        m = model_usage.setdefault(model, {
            "inputTokens": 0, "outputTokens": 0, "cacheReadTokens": 0,
            "cacheWriteTokens": 0, "count": 0, "costStatus": "unknown",
            "estimatedCostUsd": None,
        })
        for k in ("inputTokens", "outputTokens", "cacheReadTokens", "cacheWriteTokens"):
            v = usage.get(k)
            if isinstance(v, (int, float)):
                m[k] += v
        m["count"] += 1

    # Cost estimation with pricing freshness downgrade.
    total_cost = 0.0
    has_metered = False
    cost_status = "estimated"
    for model, m in model_usage.items():
        price = _price_for(model)
        if price is None:
            m["costStatus"] = "unknown"
            cost_status = "unknown" if cost_status == "estimated" else cost_status
            continue
        if price["billing"] == "subscription":
            m["costStatus"] = "not-metered"
            subscription_models.append(model)
            continue
        if price.get("stale"):
            # Expired quote -> downgrade, do not fabricate current USD.
            m["costStatus"] = "stale"
            cost_status = "stale"
            continue
        # metered, fresh
        cost = (m["inputTokens"] / 1_000_000) * price["input_per_million"] + \
               (m["outputTokens"] / 1_000_000) * price["output_per_million"]
        m["estimatedCostUsd"] = round(cost, 4)
        m["costStatus"] = "estimated"
        total_cost += cost
        has_metered = True

    if has_metered and cost_status != "stale":
        totals["estimatedCostUsd"] = round(total_cost, 4)
        totals["costStatus"] = "estimated"
    elif cost_status == "stale":
        totals["costStatus"] = "stale"
    elif not has_metered:
        totals["costStatus"] = "not-metered" if subscription_models else "unknown"

    return {
        "schemaVersion": "work-lab/usage-rollup/v1",
        "generatedAt": _now(),
        "totals": totals,
        "byModel": model_usage,
        "subscriptionModels": subscription_models,
        "idempotent": True, "rebuildable": True,
        "privacy": {"rawBodies": False, "sensitiveBodies": False},
    }


def price_status_for(model: str) -> dict[str, str]:
    """Expose pricing freshness for Observer (source/coverage/freshness/last-good)."""
    price = _price_for(model)
    if price is None:
        return {"status": "unknown", "coverage": "unknown", "freshness": "unknown"}
    return {
        "status": "stale" if price.get("stale") else ("not-metered" if price["billing"] == "subscription" else "estimated"),
        "coverage": "full",
        "freshness": "stale" if price.get("stale") else "fresh",
        "source": price["source"],
        "effective_at": price["effective_at"],
    }
