"""C1 recovery tests: the Context Pack must recover machine-truth state, not
silently skip or reconstruct missing material, and must not promote an
unmerged PR / a historical path / a no-receipt task into "done".

Negative controls required by prompt C1:
  * an unmerged PR must not be presented as main;
  * a historical/archived path must not be presented as a current path;
  * a task without a receipt must not be presented as completed;
  * after a session/executor change the critical constraints must survive;
  * a successful generation is NOT proof of a complete recovery.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "packages/client-neutral-core" / "scripts" / "build_context_pack.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_context_pack", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=False, capture_output=True,
                   text=True, encoding="utf-8", errors="replace")


def _make_tmp_repo() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="wl-context-pack-"))
    _git(tmp, "init", "-q")
    _git(tmp, "config", "user.email", "test@local")
    _git(tmp, "config", "user.name", "test")
    # build_context_pack (not write_context_pack) is called directly, so no
    # git-ignored-output check runs on the temp repo.
    return tmp


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class AuthorityMaterialsFromIndexTests(unittest.TestCase):
    """C1: the material set is resolved from the authority index, not a second
    hand-written path list."""

    def test_index_declared_materials_are_resolved(self) -> None:
        module = load_module()
        tmp = _make_tmp_repo()
        try:
            index = {
                "topHumanAuthority": "WORK-LAB-AUTHORITY.md",
                "topMachineAuthority": ".project/governance/project-authority-index.json",
                "scopedAuthorities": {"taskpack": ".project/governance/taskpack-authority-index.json"},
                "currentTaskpack": "taskpacks/current/CURRENT-TASKPACK.md",
                "currentOpenTaskRegister": "taskpacks/current/OPEN-TASK-REGISTER.md",
            }
            _write(tmp / ".project/governance/project-authority-index.json", json.dumps(index))
            _git(tmp, "add", ".")
            _git(tmp, "commit", "-q", "-m", "seed")
            materials = module.authority_materials(tmp)
            for declared in (
                "WORK-LAB-AUTHORITY.md",
                ".project/governance/project-authority-index.json",
                ".project/governance/taskpack-authority-index.json",
                "taskpacks/current/CURRENT-TASKPACK.md",
                "taskpacks/current/OPEN-TASK-REGISTER.md",
            ):
                self.assertIn(declared, materials, f"index-declared material not resolved: {declared}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class MissingMaterialExplicitTests(unittest.TestCase):
    """A declared-but-missing material is marked MISSING, never silently
    dropped and never reconstructed from memory."""

    def test_missing_declared_material_is_marked_not_reconstructed(self) -> None:
        module = load_module()
        tmp = _make_tmp_repo()
        try:
            index = {
                "topHumanAuthority": "WORK-LAB-AUTHORITY.md",
                "topMachineAuthority": ".project/governance/project-authority-index.json",
                "currentTaskpack": "taskpacks/current/CURRENT-TASKPACK.md",
                "currentOpenTaskRegister": "taskpacks/current/OPEN-TASK-REGISTER.md",
            }
            _write(tmp / ".project/governance/project-authority-index.json", json.dumps(index))
            # Only TWO of the declared files actually exist:
            _write(tmp / "WORK-LAB-AUTHORITY.md", "# top authority\n")
            _write(tmp / "taskpacks/current/OPEN-TASK-REGISTER.md", "# register\n")
            # currentTaskpack is declared but absent.
            _git(tmp, "add", ".")
            _git(tmp, "commit", "-q", "-m", "seed")
            pack = module.build_context_pack(tmp, max_chars=module.HARD_MAX_CHARS)
            self.assertIn("## Missing Materials", pack, "missing materials must be explicitly surfaced")
            self.assertIn("MISSING `taskpacks/current/CURRENT-TASKPACK.md`", pack)
            # Present material is excerpted; missing material is NOT.
            self.assertIn("## Excerpt: `WORK-LAB-AUTHORITY.md`", pack)
            self.assertNotIn("## Excerpt: `taskpacks/current/CURRENT-TASKPACK.md`", pack)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class RecoveryChecklistSentinelTests(unittest.TestCase):
    """The pack must carry the recovery sentinels: generation success !=
    recovery complete; an unmerged PR is not main; a no-receipt task is not
    done; a historical path is not a current path."""

    def test_recovery_checklist_sentinels_present(self) -> None:
        module = load_module()
        tmp = _make_tmp_repo()
        try:
            _write(tmp / "README.md", "# x\n")
            _git(tmp, "add", ".")
            _git(tmp, "commit", "-q", "-m", "seed")
            pack = module.build_context_pack(tmp, max_chars=module.HARD_MAX_CHARS)
            self.assertIn("## Recovery Checklist", pack)
            self.assertIn("generation success != recovery complete", pack)
            self.assertIn("an unmerged PR is not main", pack)
            self.assertIn("A historical or archived path is not a current path", pack)
            self.assertIn("without a receipt is not complete", pack)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class CriticalConstraintSurvivalTests(unittest.TestCase):
    """After a session/executor change the critical constraints (owner,
    forbidden roots, single-writer) must re-derive from machine truth, not
    from prose memory."""

    def test_critical_constraints_rederive_from_machine_truth(self) -> None:
        module = load_module()
        tmp = _make_tmp_repo()
        try:
            ownership = {
                "singleWriter": True,
                "modules": {
                    "workflow-assistance": {"path": "packages/client-neutral-core", "owner": "workflow"},
                },
                "rootOwnedPaths": [".project/governance"],
            }
            boundary = {"forbiddenExternalRoots": ["E:", "F:"], "runtimeRoot": ".project-local"}
            _write(tmp / ".project/governance/module-ownership.json", json.dumps(ownership))
            _write(tmp / ".project/governance/project-data-boundary.json", json.dumps(boundary))
            _git(tmp, "add", ".")
            _git(tmp, "commit", "-q", "-m", "seed")
            pack = module.build_context_pack(tmp, max_chars=module.HARD_MAX_CHARS)
            self.assertIn("## Critical Constraints (must survive compression)", pack)
            self.assertIn("Single-writer checkout: yes", pack)
            self.assertIn("Module workflow-assistance: root `packages/client-neutral-core`", pack)
            self.assertIn("`E:`", pack)
            self.assertIn("`F:`", pack)
            self.assertIn("`.project-local`", pack)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class SkillCountLiveTests(unittest.TestCase):
    """Skill count is derived from the live inventory, never a fixed
    historical number."""

    def test_skill_inventory_reads_live_module_root(self) -> None:
        module = load_module()
        tmp = _make_tmp_repo()
        try:
            ownership = {"modules": {"workflow-assistance": {"path": "packages/client-neutral-core", "owner": "workflow"}}}
            _write(tmp / ".project/governance/module-ownership.json", json.dumps(ownership))
            # Two live skills on disk:
            _write(tmp / "packages/client-neutral-core/skills/a/SKILL.md", "# a\n")
            _write(tmp / "packages/client-neutral-core/skills/b/SKILL.md", "# b\n")
            _git(tmp, "add", ".")
            _git(tmp, "commit", "-q", "-m", "seed")
            skills = module.skill_inventory(tmp)
            self.assertEqual(len(skills), 2, f"live skill count expected 2, got {len(skills)}")
            # Add a third: the count must track it (not stay fixed).
            _write(tmp / "packages/client-neutral-core/skills/c/SKILL.md", "# c\n")
            self.assertEqual(len(module.skill_inventory(tmp)), 3)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
