from __future__ import annotations
import importlib.util
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('config_coordinator',ROOT/'scripts/workflow/config_coordinator.py'); assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
class ConfigCoordinatorTests(unittest.TestCase):
 def test_unique_managed_field_is_dry_run_patch(self):
  plan=mod.plan_changes({'apply_allowed':True},{'fields':[{'path':'display.language','owner':'USER_OVERLAY','mode':'MANAGE'}]},{'display.language':'zh'},{'display.language':'en'})
  self.assertEqual(plan['status'],'DRY_RUN'); self.assertTrue(plan['apply_allowed']); self.assertEqual(plan['fields'][0]['action'],'PATCH')
 def test_ambiguous_or_unknown_field_is_quarantined(self):
  plan=mod.plan_changes({'apply_allowed':False},{'fields':[]},{'credentials':'x'},{'credentials':'y'})
  self.assertFalse(plan['apply_allowed']); self.assertEqual(plan['fields'][0]['action'],'QUARANTINE')
if __name__=='__main__': unittest.main()
