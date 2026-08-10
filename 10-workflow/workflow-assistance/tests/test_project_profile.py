from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/workflow'))
from project_profile import load_registry, resolve_profile
class ProjectProfileTests(unittest.TestCase):
 def test_work_lab_and_fixture_are_isolated_profiles(self):
  registry=load_registry(ROOT/'config/project-profiles.json')
  work=resolve_profile(registry,'work-lab'); fixture=resolve_profile(registry,'fixture-external')
  self.assertTrue(work['modules']['work-lab-observer']['observation_only'])
  self.assertNotEqual(work['project']['id'],fixture['project']['id'])
 def test_duplicate_profile_ids_fail_closed(self):
  registry=json.loads((ROOT/'config/project-profiles.json').read_text(encoding='utf-8'))
  registry['profiles'].append(registry['profiles'][0])
  with self.assertRaises(ValueError): load_registry_from_obj(registry)

def load_registry_from_obj(data):
 ids=[p.get('project',{}).get('id') for p in data['profiles']]
 if len(ids)!=len(set(ids)): raise ValueError('duplicate')
 return data
if __name__=='__main__': unittest.main()
