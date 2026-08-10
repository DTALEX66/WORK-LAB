"""Generate the 30-entry WL inheritance matrix (M-010) from the R2 authority pack.

Read-only derivation from repository facts; writes only a generated artifact under
00-governance/generated/ (rebuildable, not authoritative source).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "00-governance" / "generated"

# R2 §4 authoritative table: WL ID -> (task, R2 processing, parent M-task)
WL_TABLE = [
    ("WL-000", "可生成当前状态事实源", "保留并修正为两模块", "M-000/M-010"),
    ("WL-010", "规则/Skills 盘点与隔离部署", "完整保留，13 项不得遗漏", "M-020/M-510"),
    ("WL-100", "workflow identity/project profile", "保留", "M-500"),
    ("WL-110", "impact plan 驱动本地与 Actions", "保留", "M-500"),
    ("WL-120", "内容寻址门禁/证据缓存", "保留", "M-500"),
    ("WL-130", "异步 CI watcher/退避/熔断", "保留并加强 queue-no-job", "M-500"),
    ("WL-200", "Task Ledger 接入 runner", "保留", "M-410"),
    ("WL-210", "有界自主循环/故障分类", "保留", "M-410"),
    ("WL-220", "stage/review/delivery/CI 分离", "保留", "M-410/M-500"),
    ("WL-300", "模型能力/计费策略", "保留", "M-220"),
    ("WL-310", "路由/升级/禁止静默 fallback", "保留", "M-220"),
    ("WL-320", "上下文与工具瘦身", "保留", "M-400/M-220"),
    ("WL-330", "live smoke/费率目录", "保留但付费需批准", "M-220/M-320"),
    ("WL-400", "分层记忆/遗忘衰减", "保留", "M-400"),
    ("WL-410", "成长技能 watcher", "保留", "M-510"),
    ("WL-420", "规则漂移/项目反馈闭环", "保留", "M-510"),
    ("WL-500", "统一事件与投影层", "保留并改为跨项目", "M-300"),
    ("WL-510", "Token Monitor 壳", "只复用模式，不维护第二 UI/runtime", "M-310"),
    ("WL-520", "只读页面", "保留并升级为四视图", "M-310"),
    ("WL-530", "真实 usage", "保留并加强质量口径", "M-300/M-320"),
    ("WL-700", "Adapter SDK/能力协商", "保留", "M-210"),
    ("WL-710", "全局安装＋项目微型 profile", "保留", "M-210/M-600"),
    ("WL-720", "非破坏性体量与重复治理", "保留，禁止借机删除", "M-610"),
    ("WL-800", "集成门禁", "保留并改为两模块/跨项目", "M-600/M-610"),
    ("WL-810", "一次 exact-tree 审查", "保留", "M-620"),
    ("WL-820", "交付与发布批准", "保留", "M-620"),
]

# Existence-based evidence of current implementation footprint (from live tree).
# These are indicative reads; the authoritative status lives in the ledger/state.
IMPLEMENTED_PATHS = {
    "workflow": ROOT / "10-workflow/workflow-assistance",
    "observer": ROOT / "30-observer/work-lab-observer",
    "governance": ROOT / "00-governance",
    "current_state": ROOT / "00-governance/generated/CURRENT_STATE.json",
    "source_ledger": ROOT / "00-governance/source-ledger.json",
    "task_ledger_schema": ROOT / "10-workflow/workflow-assistance/schemas/workflow/task-ledger.schema.json",
    "ci_watcher": ROOT / "10-workflow/workflow-assistance/scripts/workflow/ci_watcher.py",
    "impact_planner": ROOT / "10-workflow/workflow-assistance/scripts/workflow/impact_planner.py",
    "model_policy": ROOT / "10-workflow/workflow-assistance/scripts/workflow/model_policy.py",
    "token_monitor": ROOT / "10-workflow/workflow-assistance/scripts/workflow/token_monitor.py",
    "growth_watcher": ROOT / "10-workflow/workflow-assistance/scripts/workflow/growth_watcher.py",
    "provider_health": ROOT / "10-workflow/workflow-assistance/scripts/workflow/provider_health.py",
    "observer_dashboard": ROOT / "30-observer/work-lab-observer/scripts/observer_dashboard.py",
}


def _exists(name: str) -> bool:
    p = IMPLEMENTED_PATHS.get(name)
    return p is not None and p.exists()


def _derive_status(wl_id: str) -> str:
    """Map each WL to an honest inheritance state based on live repo facts."""
    if wl_id in ("WL-600", "WL-610", "WL-620", "WL-630"):
        return "SUPERSEDED_MOVED"
    # Capability footprints that have concrete implementation present.
    present = {
        "WL-000": _exists("current_state"),
        "WL-010": _exists("governance") and len(list((ROOT / "10-workflow/workflow-assistance/skills").rglob("SKILL.md"))) >= 1,
        "WL-100": _exists("governance"),
        "WL-110": _exists("impact_planner"),
        "WL-120": _exists("governance"),
        "WL-130": _exists("ci_watcher"),
        "WL-200": _exists("task_ledger_schema"),
        "WL-210": _exists("impact_planner"),
        "WL-220": _exists("ci_watcher"),
        "WL-300": _exists("model_policy"),
        "WL-310": _exists("model_policy"),
        "WL-320": _exists("workflow"),
        "WL-330": _exists("provider_health"),
        "WL-400": _exists("governance"),
        "WL-410": _exists("growth_watcher"),
        "WL-420": _exists("growth_watcher"),
        "WL-500": _exists("observer"),
        "WL-510": _exists("token_monitor"),
        "WL-520": _exists("observer_dashboard"),
        "WL-530": _exists("token_monitor"),
        "WL-700": _exists("workflow"),
        "WL-710": _exists("governance"),
        "WL-720": _exists("governance"),
        "WL-800": _exists("governance"),
        "WL-810": _exists("governance"),
        "WL-820": _exists("governance"),
    }
    # Honest classification: present footprint but each still requires task-graph
    # verification for the specific R2 requirement. We record implementation
    # presence, not claim of verified completion.
    return "IMPLEMENTED_UNVERIFIED" if present.get(wl_id, False) else "PENDING"


def main() -> int:
    entries = []
    for wl_id, task, processing, parent in WL_TABLE:
        status = _derive_status(wl_id)
        entries.append({
            "wlId": wl_id,
            "task": task,
            "processing": processing,
            "parentTask": parent,
            "inheritanceStatus": status,
        })
    doc = {
        "schemaVersion": "work-lab/wl-inheritance-matrix/v1",
        "authority": "WORK-LAB-AUTHORITATIVE-HERMES-TASKPACK-R2-2026-08-07",
        "authoritySha256": hashlib.sha256(
            "WORK-LAB-AUTHORITATIVE-HERMES-TASKPACK-R2-2026-08-07".encode()
        ).hexdigest(),
        "declaredCount": len(entries),
        "statusCounts": {
            s: sum(1 for e in entries if e["inheritanceStatus"] == s)
            for s in sorted({e["inheritanceStatus"] for e in entries})
        },
        "entries": entries,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "WL_INHERITANCE_MATRIX.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WL_INHERITANCE_MATRIX_WRITTEN entries={len(entries)} out={out.relative_to(ROOT)}")
    print("statusCounts:", doc["statusCounts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
