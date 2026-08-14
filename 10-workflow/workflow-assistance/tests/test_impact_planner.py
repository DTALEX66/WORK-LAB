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
        "observer": {"roots": ["30-observer/work-lab-observer"], "depends_on": ["workflow"]},
    },
    "risk_zones": {"critical": [".github/workflows/**", "00-governance/**"]},
    "gates": {
        "workflow": {"command": "python workflow.py", "tiers": ["module"], "platform": "any"},
        "observer": {"command": "python observer.py", "tiers": ["module"], "platform": "any"},
        "integration": {"command": "python integration.py", "tiers": ["full"], "platform": "any"},
    },
    "ci": {"stable_aggregate_check": "aggregate", "exact_sha_required_for": ["critical"], "outage_blocks": ["release"]},
}


class ImpactPlannerTests(unittest.TestCase):
    def test_canonical_project_profile_loads_with_contract_schema_version(self) -> None:
        module = load_module()
        profile = module.load_profile(Path(__file__).resolve().parents[3] / "00-governance" / "work-lab.project-profile.yaml")
        self.assertEqual(profile["schema_version"], "workflow/project-profile/v1")
        self.assertEqual(profile["ci"]["workflow_name"], "work-lab-gate")
        self.assertEqual(profile["ci"]["stable_aggregate_job"], "aggregate")
        self.assertEqual(
            profile["gates"]["token-monitor"]["paths"],
            ["10-workflow/workflow-assistance/apps/token-monitor-desktop/**"],
        )

    def test_token_monitor_path_selects_its_dedicated_gate(self) -> None:
        module = load_module()
        profile = module.load_profile(Path(__file__).resolve().parents[3] / "00-governance" / "work-lab.project-profile.yaml")
        plan = module.build_plan(
            profile,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["10-workflow/workflow-assistance/apps/token-monitor-desktop/src-tauri/src/lib.rs"],
        )
        self.assertIn("token-monitor", plan["required_gates"])

    def test_critical_ci_path_selects_supply_chain_security_gate(self) -> None:
        module = load_module()
        profile = module.load_profile(Path(__file__).resolve().parents[3] / "00-governance" / "work-lab.project-profile.yaml")
        plan = module.build_plan(
            profile,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=[".github/workflows/work-lab-gate.yml"],
        )
        self.assertEqual(
            plan["required_gates"],
            ["integration", "observer", "supply-chain-security", "token-monitor", "workflow"],
        )

    def test_workflow_change_expands_to_transitive_dependents(self) -> None:
        module = load_module()
        plan = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["10-workflow/workflow-assistance/scripts/workflow/task_ledger.py"],
        )
        self.assertEqual(plan["required_gates"], ["observer", "workflow"])
        self.assertEqual(plan["risk"], "medium")
        self.assertEqual(plan["delivery_effect"], "none")
        self.assertEqual(len(plan["plan_digest"]["value"]), 64)

    def test_external_design_path_fails_closed_to_all_active_gates(self) -> None:
        module = load_module()
        plan = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["external/handoff-pointer.txt"],
        )
        self.assertEqual(plan["required_gates"], ["integration", "observer", "workflow"])

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

    def test_unknown_path_fails_closed_to_all_configured_gates(self) -> None:
        module = load_module()
        plan = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["unclassified/new-boundary.txt"],
        )
        self.assertEqual(plan["risk"], "critical")
        self.assertEqual(plan["required_gates"], ["integration", "observer", "workflow"])

    def test_plan_digest_ignores_timestamp_and_display_id(self) -> None:
        module = load_module()
        first = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["external/handoff-pointer.txt"],
            plan_id="local",
            generated_at="2026-08-07T00:00:00Z",
        )
        second = module.build_plan(
            PROFILE,
            repository="DTALEX66/WORK-LAB",
            commit="commit",
            tree="tree",
            changed_paths=["external/handoff-pointer.txt"],
            plan_id="cloud",
            generated_at="2026-08-07T01:00:00Z",
        )
        self.assertEqual(first["plan_digest"], second["plan_digest"])


if __name__ == "__main__":
    unittest.main()
