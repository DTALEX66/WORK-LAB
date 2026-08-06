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
    def test_v2_observer_job_is_required(self):
        payload = json.dumps({"jobs": {name: "success" for name in load_gate().REQUIRED}})
        self.assertEqual(load_gate().main(payload), 0)

    def test_retired_minigame_job_does_not_satisfy_v2_gate(self):
        gate = load_gate()
        payload = json.dumps({"jobs": {"workflow": "success", "open-design": "success", "minigame": "success", "integration": "success"}})
        self.assertEqual(gate.main(payload), 1)


if __name__ == "__main__":
    unittest.main()
