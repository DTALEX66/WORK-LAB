from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_gate():
    path = ROOT / "scripts" / "ci" / "aggregate_gate.py"
    spec = importlib.util.spec_from_file_location("aggregate_gate", path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load aggregate gate")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AggregateGateTests(unittest.TestCase):
    def test_observer_job_is_required(self):
        payload = json.dumps({"jobs": {name: "success" for name in load_gate().REQUIRED}})
        self.assertEqual(load_gate().main(payload), 0)

    def test_retired_open_design_job_does_not_satisfy_gate(self):
        gate = load_gate()
        payload = json.dumps({"jobs": {"workflow": "success", "open-design": "success", "integration": "success"}})
        self.assertEqual(gate.main(payload), 1)

    def test_selected_token_monitor_job_is_required(self):
        gate = load_gate()
        plan = {
            "schema_version": "workflow/gate-plan/v1",
            "plan_id": "work-lab-gate",
            "source_identity": {
                "repository": "DTALEX66/WORK-LAB",
                "commit": {"algorithm": "repository-default", "object_type": "commit", "oid": "sha"},
                "tree": {"algorithm": "repository-default", "object_type": "tree", "oid": "tree"},
            },
            "changed_paths": ["10-workflow/workflow-assistance/apps/token-monitor-desktop/src/main.js"],
            "required_gates": ["token-monitor"],
            "skipped_gates": [{"gate_id": "workflow", "reason": "not selected"}],
            "risk": "medium",
            "delivery_effect": "none",
            "platform_scope": ["windows"],
            "generated_at": "2026-08-13T00:00:00Z",
        }
        plan["plan_digest"] = {"algorithm": "sha256", "value": gate._plan_digest(plan)}
        payload = json.dumps({
            "gate_plan": plan,
            "expected_plan_digest": plan["plan_digest"]["value"],
            "expected_head_sha": "sha",
            "jobs": {"token-monitor": "skipped"},
        })
        self.assertEqual(gate.main(payload), 1)

    def test_selected_supply_chain_security_job_is_required(self):
        gate = load_gate()
        plan = {
            "schema_version": "workflow/gate-plan/v1",
            "plan_id": "work-lab-gate",
            "source_identity": {
                "repository": "DTALEX66/WORK-LAB",
                "commit": {"algorithm": "repository-default", "object_type": "commit", "oid": "sha"},
                "tree": {"algorithm": "repository-default", "object_type": "tree", "oid": "tree"},
            },
            "changed_paths": [".github/workflows/work-lab-gate.yml"],
            "required_gates": ["supply-chain-security"],
            "skipped_gates": [{"gate_id": "workflow", "reason": "not selected"}],
            "risk": "critical",
            "delivery_effect": "none",
            "platform_scope": ["discovered"],
            "generated_at": "2026-08-15T00:00:00Z",
        }
        plan["plan_digest"] = {"algorithm": "sha256", "value": gate._plan_digest(plan)}
        payload = {
            "gate_plan": plan,
            "expected_plan_digest": plan["plan_digest"]["value"],
            "expected_head_sha": "sha",
            "jobs": {"supply-chain-security": "failure"},
        }
        self.assertEqual(gate.main(json.dumps(payload)), 1)
        payload["jobs"]["supply-chain-security"] = "success"
        self.assertEqual(gate.main(json.dumps(payload)), 0)

    def test_plan_digest_and_head_sha_are_verified(self):
        gate = load_gate()
        plan = {
            "schema_version": "workflow/gate-plan/v1",
            "plan_id": "work-lab-gate",
            "source_identity": {
                "repository": "DTALEX66/WORK-LAB",
                "commit": {"algorithm": "repository-default", "object_type": "commit", "oid": "sha"},
                "tree": {"algorithm": "repository-default", "object_type": "tree", "oid": "tree"},
            },
            "changed_paths": ["README.md"],
            "required_gates": ["workflow"],
            "skipped_gates": [{"gate_id": "workflow", "reason": "not selected"}],
            "risk": "medium",
            "delivery_effect": "none",
            "platform_scope": ["discovered"],
            "generated_at": "2026-08-07T00:00:00Z",
        }
        plan["plan_digest"] = {"algorithm": "sha256", "value": gate._plan_digest(plan)}
        payload = json.dumps({
            "gate_plan": plan,
            "expected_plan_digest": plan["plan_digest"]["value"],
            "expected_head_sha": "sha",
            "jobs": {"workflow": "success", "observer": "skipped", "integration": "skipped"},
        })
        self.assertEqual(gate.main(payload), 0)

    def test_plan_digest_mismatch_fails_closed(self):
        gate = load_gate()
        plan = {
            "schema_version": "workflow/gate-plan/v1",
            "plan_id": "work-lab-gate",
            "source_identity": {"commit": {"oid": "sha"}},
            "required_gates": ["workflow"],
            "plan_digest": {"algorithm": "sha256", "value": "wrong"},
        }
        self.assertEqual(gate.main(json.dumps({"gate_plan": plan, "expected_plan_digest": "wrong", "expected_head_sha": "sha", "jobs": {"workflow": "success"}})), 1)


if __name__ == "__main__":
    unittest.main()
