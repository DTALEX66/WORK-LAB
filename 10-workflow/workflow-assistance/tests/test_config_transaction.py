import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'workflow'))
from config_control_plane import ConfigControlPlane, SoftwareRegistration

def test_unapproved_never_writes():
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    d = ccp.diff({'a': 1}, {'a': 2})
    r = ccp.transaction('hermes', d, approved=False)
    assert r['status'] == 'WAITING_APPROVAL'

def test_apply_readback_commit():
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm2'})
    r = ccp.transaction('hermes', d, approved=True,
        backup_dir=str(Path(__file__).resolve().parents[2] / 'config' / '.backups'),
        apply_fn=lambda before: {'model': 'm2'},
        readback_fn=lambda: {'model': 'm2'})
    assert r['status'] == 'COMMITTED', r

def test_drift_rolls_back():
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm2'})
    r = ccp.transaction('hermes', d, approved=True,
        backup_dir=str(Path(__file__).resolve().parents[2] / 'config' / '.backups'),
        apply_fn=lambda before: {'model': 'm2'},
        readback_fn=lambda: {'model': 'm1'})  # mismatch -> drift
    assert r['status'] == 'ROLLED_BACK', r

def test_no_apply_fn_unsupported():
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    d = ccp.diff({'a': 1}, {'a': 2})
    r = ccp.transaction('hermes', d, approved=True)
    assert r['status'] == 'UNSUPPORTED_APPLY'
