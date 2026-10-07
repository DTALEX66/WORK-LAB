"""Throwaway fixture roots that cannot land outside the project Git root.

ERR-140 was a bare ``tempfile.mkdtemp()`` in a governance test: its ``tearDown`` did
``shutil.rmtree(..., ignore_errors=True)``, so a failing run left complete mirrors of the authority
package in the system temp directory — outside the boundary
``.project/governance/project-data-boundary.json`` declares ("all content this project produces —
builds, caches, temp files, evidence … stays locked inside the project Git root").

The canonical gate runner binds ``TMP``/``TEMP``/``TMPDIR`` to ``.project-local/runs/tmp`` for its
children, so a fixture created *inside a gate run* is already contained. This module removes the
dependence on that environment for paths production code creates when it is invoked directly, and it
deliberately exposes one entry point named ``fixture_dir`` rather than ``mkdtemp``: the debt gate
``tests/workflow-assistance/test_temp_fixture_stays_inside_the_boundary.py`` fails on any call whose
name is ``mkdtemp`` without ``dir=``, so a bounded helper must not be able to masquerade as the leak it
replaces.
"""
from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TMP = REPO_ROOT / ".project-local" / "runs" / "tmp"


def temp_root() -> Path:
    """A writable in-boundary directory for throwaway fixtures.

    An inherited ``TMPDIR``/``TEMP``/``TMP`` is honoured only when it resolves inside the repository;
    anything else (system temp, a path that cannot be resolved) is refused and the project-local root
    is used instead. A boundary gate fails closed — it does not take the environment's word for it.
    """
    for variable in ("TMPDIR", "TEMP", "TMP"):
        raw = os.environ.get(variable)
        if not raw:
            continue
        candidate = Path(raw)
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_relative_to(REPO_ROOT):
            resolved.mkdir(parents=True, exist_ok=True)
            return resolved
    DEFAULT_TMP.mkdir(parents=True, exist_ok=True)
    return DEFAULT_TMP


_TRACKED: list[Path] = []
_SWEEP_REGISTERED = False


def _release_tracked() -> None:
    for leftover in list(_TRACKED):
        if not leftover.exists():
            _TRACKED.remove(leftover)
            continue
        try:
            shutil.rmtree(leftover)
        except OSError as error:  # reported, never ignored — residue must be visible
            print(f"TEMP_RESIDUE_NOT_REMOVED {leftover} {type(error).__name__}: {error}")
            continue
        _TRACKED.remove(leftover)


def fixture_dir(prefix: str = "work-lab-") -> Path:
    """Create a throwaway directory inside the boundary and guarantee its release is attempted.

    A self-check script that makes five fixture roots and forgets five ``rmtree`` calls is the ERR-140
    spill. Registration here is part of creation, so cleanup cannot be forgotten, and a removal that
    fails is reported rather than swallowed. On Windows a fixture whose store is still open cannot be
    removed, so a caller that opens a database must close it — the report names the directory instead
    of hiding it.
    """
    global _SWEEP_REGISTERED
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(temp_root())))
    if not path.is_relative_to(REPO_ROOT):
        raise RuntimeError(f"fixture root escaped the project boundary: {path}")
    _TRACKED.append(path)
    if not _SWEEP_REGISTERED:
        atexit.register(_release_tracked)
        _SWEEP_REGISTERED = True
    return path


def pending_fixtures() -> tuple[Path, ...]:
    return tuple(_TRACKED)


def inside_project(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(REPO_ROOT)
    except OSError:
        return False
