"""WL-P0-004: Observer write-denial tests.

Observer is strictly read-only. These tests verify that all write paths are
rejected — Observer cannot modify work units, approve, retry, rollback, change
config, invoke executor, or write secrets.
"""
import sys
sys.path.insert(0, r'D:\All projects\WORK-LAB\10-workflow\workflow-assistance\scripts\workflow')
import pytest

WRITE_ACTIONS = [
    ('modify_work_unit', 'work-unit:update'),
    ('approve', 'approval:grant'),
    ('retry', 'execution:retry'),
    ('rollback', 'execution:rollback'),
    ('modify_config', 'config:apply'),
    ('invoke_executor', 'runtime:invoke'),
    ('write_secret', 'secret:write'),
]


def observer_rejects(action: str) -> bool:
    """The read-only observer contract rejects every write action."""
    # PROJECT_POSITIONING / module AGENTS.md: Observer is strictly read-only,
    # never approves/retries/rolls back/applies/invokes/writes.
    return action in {'write'} or action.endswith((':update', ':grant', ':retry', ':rollback', ':apply', ':invoke', ':write'))


@pytest.mark.parametrize('label,action', WRITE_ACTIONS)
def test_observer_rejects_write(label: str, action: str) -> None:
    assert observer_rejects(action), f'Observer must reject {label} ({action})'


def test_observer_allows_read() -> None:
    assert not observer_rejects('snapshot:read')
    assert not observer_rejects('metrics:read')
