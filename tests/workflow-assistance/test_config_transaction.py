import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'services' / 'policy'))
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
        backup_dir=str(Path(__file__).resolve().parents[2] / '.project-local' / 'runs' / 'config-transaction-tests'),
        apply_fn=lambda before: {'model': 'm2'},
        readback_fn=lambda: {'model': 'm2'})
    assert r['status'] == 'COMMITTED', r

def test_drift_rolls_back():
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm2'})
    r = ccp.transaction('hermes', d, approved=True,
        backup_dir=str(Path(__file__).resolve().parents[2] / '.project-local' / 'runs' / 'config-transaction-tests'),
        apply_fn=lambda before: {'model': 'm2'},
        readback_fn=lambda: {'model': 'm1'})  # mismatch -> drift
    assert r['status'] == 'ROLLBACK_REQUIRED', r

def test_no_apply_fn_unsupported():
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    d = ccp.diff({'a': 1}, {'a': 2})
    r = ccp.transaction('hermes', d, approved=True)
    assert r['status'] == 'UNSUPPORTED_APPLY'

def test_noop_on_empty_diff():
    # NF-04 acceptance: "no change" is a genuine no-op — an approved empty diff
    # never enters the backup/apply/readback cycle and never reports a write.
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm1'})   # changeCount == 0
    assert d['changeCount'] == 0
    def _boom(before):
        raise AssertionError("apply_fn must NOT be called for a no-op")
    r = ccp.transaction('hermes', d, approved=True, apply_fn=_boom,
                       readback_fn=lambda: {'model': 'm1'})
    assert r['status'] == 'NOOP', r
    assert r.get('changeCount') == 0

def test_apply_failure_is_honest_undetermined():
    # NF-04 acceptance: a raised write is UNDETERMINED, never faked as a
    # rollback or a success. errorType is surfaced but exception text is not
    # (an adapter may embed private config values in the message).
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm2'})
    def _fail(before):
        raise PermissionError("secret adapter detail must not leak")
    r = ccp.transaction('hermes', d, approved=True,
                       backup_dir=str(Path(__file__).resolve().parents[2] / '.project-local' / 'runs' / 'config-transaction-tests'),
                       apply_fn=_fail, readback_fn=lambda: {'model': 'm1'})
    assert r['status'] == 'APPLY_FAILED', r
    assert r['written'] == 'UNDETERMINED'
    assert r['restored'] is False
    assert r['errorType'] == 'PermissionError'
    assert 'secret adapter detail' not in r['errorType']

def test_rollback_failure_is_honest():
    # NF-04 acceptance: "recovery failure" must report ROLLBACK_FAILED with
    # restored=False — never a fake ROLLED_BACK / success.
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm2'})
    def _rb(before):
        raise RuntimeError("restore target missing")
    r = ccp.transaction('hermes', d, approved=True,
                       backup_dir=str(Path(__file__).resolve().parents[2] / '.project-local' / 'runs' / 'config-transaction-tests'),
                       apply_fn=lambda before: {'model': 'm2'},
                       readback_fn=lambda: {'model': 'm1'},   # drift -> rollback
                       rollback_fn=_rb)
    assert r['status'] == 'ROLLBACK_FAILED', r
    assert r['restored'] is False
    assert r['errorType'] == 'RuntimeError'

def test_simulated_success_is_tagged_and_not_real():
    # NF-04 acceptance: a simulated adapter's success must be distinguishable
    # from a real applied success so it can never enter the real success tally.
    ccp = ConfigControlPlane()
    ccp.register(SoftwareRegistration('hermes', 'Hermes', 'agent-harness', 'x'))
    ccp.set_layer('official_baseline', {'model': 'm1'})
    d = ccp.diff({'model': 'm1'}, {'model': 'm2'})
    sim = ccp.transaction('hermes', d, approved=True,
                         apply_fn=lambda before: {'model': 'm2'},
                         readback_fn=lambda: {'model': 'm2'}, simulated=True)
    real = ccp.transaction('hermes', d, approved=True,
                          apply_fn=lambda before: {'model': 'm2'},
                          readback_fn=lambda: {'model': 'm2'}, simulated=False)
    assert sim['status'] == 'COMMITTED_SIMULATED'
    assert sim['simulated'] is True
    assert real['status'] == 'COMMITTED'
    assert real['simulated'] is False
    # a real-success tally must only count the non-simulated outcome
    real_successes = [s for s in (sim, real) if s['status'] == 'COMMITTED']
    assert len(real_successes) == 1 and real_successes[0] is real
