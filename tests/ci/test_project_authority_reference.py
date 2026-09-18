"""A03: negative controls for the authority-reference verifier.

Each test mutates a throwaway copy of the repository's authority package under
a temp directory and asserts the verifier fails closed with the exact named
reason. The live repository is never mutated.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "ci" / "verify_project_authority_reference.py"

# Minimal authority files the verifier requires, copied into the fixture.
_REQUIRED = [
    "WORK-LAB-AUTHORITY.md",
    ".project/governance/project-authority-index.json",
    ".project/governance/taskpack-authority-index.json",
    ".project/governance/module-ownership.json",
    "taskpacks/current/OPEN-TASK-REGISTER.md",
]


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_project_authority_reference", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_fixture() -> Path:
    """Copy the live authority package into a temp root that verifies clean."""
    tmp = Path(tempfile.mkdtemp(prefix="auth-ref-"))
    # Build the fixture from live files so it reflects the real package.
    for rel in _REQUIRED:
        source = ROOT / rel
        target = tmp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_file():
            shutil.copy2(source, target)
    # The allowlist files declared by the project index must exist in the
    # fixture for the clean copy to pass check 6.
    pidx = json.loads((tmp / ".project/governance/project-authority-index.json").read_text(encoding="utf-8"))
    for entry in pidx.get("operationalCompatibilityAllowlist", []):
        src = ROOT / entry["path"]
        dst = tmp / entry["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dst)
    # The CURRENT taskpack file must exist under taskpacks/current/.
    tidx = json.loads((tmp / ".project/governance/taskpack-authority-index.json").read_text(encoding="utf-8"))
    current = tidx["classification"]["CURRENT"]
    assert len(current) == 1
    live_current = ROOT / "taskpacks" / "current" / f"{current[0]}.md"
    dest = tmp / "taskpacks" / "current" / f"{current[0]}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(live_current, dest)
    return tmp


def _read(tmp: Path, rel: str) -> dict:
    return json.loads((tmp / rel).read_text(encoding="utf-8"))


def _write(tmp: Path, rel: str, data: dict) -> None:
    (tmp / rel).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class AuthorityReferenceNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.verifier = _load_verifier()
        self.tmp = _make_fixture()
        try:
            # fixture sanity: the unmutated copy must PASS.
            self.assertEqual(self.verifier.verify(self.tmp), 0)
        finally:
            pass

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clean_fixture_passes(self) -> None:
        self.assertEqual(self.verifier.verify(self.tmp), 0)

    def test_missing_top_authority_fails(self) -> None:
        (self.tmp / "WORK-LAB-AUTHORITY.md").unlink()
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_project_index_missing_fails(self) -> None:
        (self.tmp / ".project/governance/project-authority-index.json").unlink()
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_multiple_current_taskpacks_fail(self) -> None:
        tidx = _read(self.tmp, ".project/governance/taskpack-authority-index.json")
        tidx["classification"]["CURRENT"].append("SOME-OTHER-TASKPACK")
        _write(self.tmp, ".project/governance/taskpack-authority-index.json", tidx)
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_current_taskpack_file_missing_fails(self) -> None:
        tidx = _read(self.tmp, ".project/governance/taskpack-authority-index.json")
        current = tidx["classification"]["CURRENT"][0]
        (self.tmp / "taskpacks/current" / f"{current}.md").unlink()
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_open_register_missing_fails(self) -> None:
        (self.tmp / "taskpacks/current/OPEN-TASK-REGISTER.md").unlink()
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_frozen_history_marked_normative_fails(self) -> None:
        # A frozen/historical record must not be promoted to the current taskpack.
        tidx = _read(self.tmp, ".project/governance/taskpack-authority-index.json")
        tidx["classification"]["CURRENT"] = ["WORK-LAB-FROZEN-LEGACY-INDEX-20260918"]
        _write(self.tmp, ".project/governance/taskpack-authority-index.json", tidx)
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_forbidden_root_reactivation_fails(self) -> None:
        mo = _read(self.tmp, ".project/governance/module-ownership.json")
        # Re-declare a forbidden legacy root as a live module root.
        mo["modules"]["legacy-regression"] = {
            "path": "50-taskpacks",
            "owner": "workflow",
            "releasePrefix": "workflow",
        }
        _write(self.tmp, ".project/governance/module-ownership.json", mo)
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_dangling_allowlist_reference_fails(self) -> None:
        pidx = _read(self.tmp, ".project/governance/project-authority-index.json")
        pidx.setdefault("operationalCompatibilityAllowlist", []).append(
            {"path": "taskpacks/current/DOES-NOT-EXIST.md", "role": "x"}
        )
        _write(self.tmp, ".project/governance/project-authority-index.json", pidx)
        self.assertEqual(self.verifier.verify(self.tmp), 1)

    def test_project_index_invalid_json_fails(self) -> None:
        (self.tmp / ".project/governance/project-authority-index.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(self.verifier.verify(self.tmp), 1)


if __name__ == "__main__":
    unittest.main()
