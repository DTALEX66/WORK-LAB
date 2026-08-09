from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/workflow'))
from sidecar_lock import SingleInstanceLock
class SidecarLockTests(unittest.TestCase):
 def test_second_instance_is_rejected_and_release_recovers(self):
  with tempfile.TemporaryDirectory() as raw:
   path=Path(raw)/'sidecar.lock'
   first=SingleInstanceLock(path); first.acquire()
   with self.assertRaises(RuntimeError): SingleInstanceLock(path).acquire()
   first.release()
   second=SingleInstanceLock(path); second.acquire(); second.release()
if __name__=='__main__': unittest.main()
