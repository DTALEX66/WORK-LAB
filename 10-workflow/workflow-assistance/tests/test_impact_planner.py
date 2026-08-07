from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/workflow/impact_planner.py"


def load_module():
    spec = importlib.util.spec_from_file_location("impact_planner", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROFILE = {
    "schema": "work-lab-project-profile/v1",
    "project": {"id": "work-lab", "root_policy": "discover_git_root", "windows_native_first": True},
    "modules": {
        "workflow": {"roots": ["10-workflow/workflow-assistance"]},
        "open_design": {"roots": ["20-design/open-design"], "depends_on": ["workflow"]},
        "observer": {"roots": ["30-observer/work-lab-observer"], "depends_on": ["workflow"]},
    },
    "risk_zones": {"critical": [".github/workflows/**", "00-governance/**"]},
    "gates": {
        "workflow": {"command": "python workflow.py", "tiers": ["module"], "platform": "any"},
        "open_design": {"command": "python design.py", "tiers": ["module"], "platform": "any"},
        "observer": {"command": "python observer.py", "tiers": ["module"], "platform": "any"},
        "integration": {"command": "python integration.py", "tiers": ["full"], "platform": "any"},
    },
    "ci": {"stable_aggregate_check": "aggregate", "exact_sha_required_for": ["critical"], "outage_blocks": ["release"]},
}


class ImpactPlannerTests(unittest.TestCase):
    def test_workflow_change_expands_to_transitive_dependents(self) -> None:
        module = load_module()
        plan = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["10-workflow/workflow-assistance/scripts/workflow/task_ledger.py"],
        )
        self.assertEqual(plan["required_gates"], ["observer", "open_design", "workflow"])
        self.assertEqual(plan["risk"], "medium")
        self.assertEqual(plan["delivery_effect"], "none")
        self.assertEqual(len(plan["plan_digest"]["value"]), 64)

    def test_unrelated_design_change_does_not_select_workflow_or_observer(self) -> None:
        module = load_module()
        plan = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["20-design/open-design/README.md"],
        )
        self.assertEqual(plan["required_gates"], ["open_design"])
        skipped = {item["gate_id"] for item in plan["skipped_gates"]}
        self.assertEqual(skipped, {"integration", "observer", "workflow"})

    def test_governance_change_is_critical_and_requires_integration(self) -> None:
        module = load_module()
        plan = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["00-governance/contracts/contract-catalog.json"],
            delivery_effect="push",
            platform_scope=["linux", "windows"],
        )
        self.assertEqual(plan["risk"], "critical")
        self.assertIn("integration", plan["required_gates"])
        self.assertEqual(plan["platform_scope"], ["linux", "windows"])


if __name__ == "__main__":
    unittest.main()
