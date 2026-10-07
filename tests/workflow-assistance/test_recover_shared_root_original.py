"""AG-19/spill gate: the shared-root recovery tool must only ever mirror in what it can prove safe.

`scripts/maintenance/recover_shared_root_original.py` pulls one WORK-LAB-authored original out of a
DECLARED shared root and back inside the Git root — the `migrate` property of
`.project/governance/project-data-boundary.json` exercised for real. Because the tool writes, its
screens are what matters, so they are falsified here against fixtures instead of trusted from the
happy path.

Fixtures live under the git-ignored `.project-local` run root, and the CLI is driven through a shim
that points the module's `EXTERNAL_INDEX` and `SPILL_LEDGER` globals at fixture files. That way the
declared-root screen and the per-write ledger append are exercised without writing outside the
repository and without touching the real spill ledger.

Discovered dynamically by `run_quality_gate.py governance`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / ".project-local" / "runs" / "recover-shared-root-original-tests"
SHARED = RUN / "fake-shared-root"
TOOL = ROOT / "scripts" / "maintenance" / "recover_shared_root_original.py"

MIRRORED_REL = "docs/history/archive/recovered-originals/WORK-LAB-SHARED-DEPENDENCIES-2026-08-15.md"
MIRRORED_SHA = "3a71b7bedd042d7c9e936a01ab08c2625ca4356a880cd2a3f899a950eeee5972"
MIRRORED_BYTES = 3763
OUTSIDE_ORIGINAL = Path(r"D:/All projects/OS External Configuration/docs"
                        "/WORK-LAB-SHARED-DEPENDENCIES-2026-08-15.md")

DOC = "# register\n\nNode 24.18.0 shared, git 2.54.0 shared, nothing moved.\n"
SECRET_DOC = DOC + "\napi token line:\nsk-abcdefghijklmnopqrstuvwx1234567890\n"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


class RecoveryScreensTests(unittest.TestCase):
    """Every refusal path and the one allowed path, against fixtures only."""

    def setUp(self) -> None:
        self.shared = SHARED / "docs"
        self.shared.mkdir(parents=True, exist_ok=True)
        self.source = write(self.shared / "doc.md", DOC)
        self.index = write(RUN / "external-libraries-index.json", json.dumps(
            {"sharedRoots": {"fake-shared": str(SHARED)}, "libraries": []}, ensure_ascii=False))
        self.ledger = RUN / "spill-ledger.jsonl"
        self.ledger.unlink(missing_ok=True)

    def cli(self, dest: str, kind: str = "user_published_audit",
            source: str | None = None, stage: bool = False) -> subprocess.CompletedProcess:
        argv = ["--source", source if source is not None else str(self.source),
                "--dest", dest, "--actor", "gate-fixture", "--kind", kind,
                "--evidence", f"{RUN / 'evidence.json'}"]
        if stage:
            argv.append("--stage")
        shim = write(RUN / "shim.py",
                     "import sys, pathlib\n"
                     f"sys.path.insert(0, {str(TOOL.parent)!r})\n"
                     "import recover_shared_root_original as m\n"
                     f"m.EXTERNAL_INDEX = pathlib.Path({str(self.index)!r})\n"
                     f"m.SPILL_LEDGER = pathlib.Path({str(self.ledger)!r})\n"
                     f"sys.argv = [str(m.__file__)] + {argv!r}\n"
                     "raise SystemExit(m.main())\n")
        return subprocess.run([sys.executable, str(shim)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def dest(self, name: str) -> str:
        path = RUN / name
        path.unlink(missing_ok=True)
        return str(path.relative_to(ROOT)).replace("\\", "/")

    def test_declared_root_screen_accepts_only_index_declared_locations(self) -> None:
        sys.path.insert(0, str(TOOL.parent))
        try:
            import recover_shared_root_original as mod
            original = mod.EXTERNAL_INDEX
            mod.EXTERNAL_INDEX = self.index
            try:
                self.assertIsNone(mod.declared_root_of(ROOT / "AGENTS.md")[0],
                                  "a repository file was accepted as shared-root material")
                self.assertEqual(mod.declared_root_of(self.source)[0], "fake-shared")
            finally:
                mod.EXTERNAL_INDEX = original
        finally:
            sys.path.remove(str(TOOL.parent))

    def test_forbidden_volume_is_refused_before_any_read(self) -> None:
        proc = self.cli(self.dest("nope.md"), source="E:/private/WORK-LAB.md")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("SOURCE_IN_FORBIDDEN_VOLUME", proc.stdout)
        self.assertFalse((ROOT / self.dest("nope.md")).exists())

    def test_source_outside_every_declared_root_is_refused(self) -> None:
        proc = self.cli(self.dest("nope2.md"), source=str(ROOT / "README.md"))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("SOURCE_NOT_UNDER_DECLARED_SHARED_ROOT", proc.stdout)

    def test_existing_or_tracked_destination_is_never_overwritten(self) -> None:
        proc = self.cli("AGENTS.md")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("DEST_ALREADY_EXISTS", proc.stdout)
        self.assertIn("DEST_ALREADY_TRACKED", proc.stdout)

    def test_unresolved_destination_outside_the_root_is_refused(self) -> None:
        proc = self.cli("../escaped-by-dest.md")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("DEST_OUTSIDE_GIT_ROOT", proc.stdout)
        self.assertFalse((ROOT.parent / "escaped-by-dest.md").exists())

    def test_forbidden_artifact_class_is_rejected_even_with_authorization(self) -> None:
        target = self.dest("rejected.md")
        proc = self.cli(target, kind="conversation_log")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("ARTIFACT_FLOW_NOT_ALLOWED:REJECT", proc.stdout)
        self.assertFalse((ROOT / target).exists(),
                         "a forbidden-class document was written into the root")
        self.assertEqual(self.ledger.read_text(encoding="utf-8") if self.ledger.exists() else "", "",
                         "a refused recovery still appended a ledger line")

    def test_unclassified_artifact_kind_fails_closed(self) -> None:
        target = self.dest("pending.md")
        proc = self.cli(target, kind="something-unknown")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("ARTIFACT_FLOW_NOT_ALLOWED:PENDING_AUTHORIZATION", proc.stdout)
        self.assertFalse((ROOT / target).exists())

    def test_secret_shaped_line_stops_the_mirror(self) -> None:
        write(self.shared / "doc.md", SECRET_DOC)
        target = self.dest("secret.md")
        proc = self.cli(target)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("SECRET_SHAPED_LINES", proc.stdout)
        self.assertNotIn("sk-", proc.stdout, "the refusal echoed the secret value")
        self.assertFalse((ROOT / target).exists())

    def test_allowed_mirror_is_byte_identical_and_recorded_once(self) -> None:
        target = self.dest("mirror.md")
        proc = self.cli(target)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("RECOVERED", proc.stdout)
        self.assertIn("blobIdentical=None", proc.stdout)  # --stage was not passed
        self.assertIn("untouched=True identical=True", proc.stdout)
        out = ROOT / target
        self.assertEqual(out.read_bytes(), DOC.encode("utf-8"))
        lines = [json.loads(l) for l in self.ledger.read_text(encoding="utf-8").splitlines() if l]
        self.assertEqual(len(lines), 1, "the mirror was not recorded as exactly one write")
        for field in ("at", "actor", "action", "outOfRoot", "target", "source", "trace", "locate",
                      "clean", "migrate", "reversible"):
            self.assertIn(field, lines[0], f"ledger line lacks the declared field {field}")
        self.assertIs(lines[0]["outOfRoot"], False)
        self.assertIn(str(self.source), lines[0]["locate"])
        evidence = json.loads((RUN / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["flowDecision"]["decision"], "ALLOW")
        self.assertEqual(evidence["originalMeasure"]["sha256"], hashlib.sha256(DOC.encode()).hexdigest())


class UpstreamScannerGapTests(unittest.TestCase):
    """ERR-139: the shared secret scanner does not see a bare string inside a list.

    Pinned here so the recovery tool's keyed-lines workaround is not later "simplified" back into a
    silent blind spot, and so the defect in
    `packages/client-neutral-core/scripts/artifact_flow_policy.py::_walk_keys` carries a runnable
    reproduction instead of a prose claim.
    """

    def setUp(self) -> None:
        sys.path.insert(0, str(ROOT / "packages" / "client-neutral-core" / "scripts"))
        import artifact_flow_policy as afp  # noqa: E402
        self.afp = afp

    def tearDown(self) -> None:
        sys.path.remove(str(ROOT / "packages" / "client-neutral-core" / "scripts"))

    def test_list_of_strings_is_invisible_but_keyed_lines_are_not(self) -> None:
        token = "sk-" + "a" * 30
        self.assertTrue(self.afp._SECRET_VALUE_RE.match(token), "the fixture token is not token-shaped")
        self.assertEqual(self.afp.find_nested_secrets({"content": {"lines": [token]}}), [],
                         "the upstream scanner caught a list element; update this test and the "
                         "workaround in scripts/maintenance/recover_shared_root_original.py")
        self.assertEqual(self.afp.find_nested_secrets({"content": {"L1": token}}), ["content.L1"],
                         "the keyed workaround the recovery tool relies on does not actually work")


class MirroredOriginalTests(unittest.TestCase):
    """The one original this recovery actually moved in stays verifiable."""

    def test_repo_copy_hashes_to_the_recorded_digest(self) -> None:
        tracked = subprocess.run(["git", "show", f"HEAD:{MIRRORED_REL}"], cwd=ROOT, capture_output=True)
        if tracked.returncode != 0:
            self.skipTest("the mirrored original is not in HEAD yet (commit still pending)")
        data = tracked.stdout
        self.assertEqual(hashlib.sha256(data).hexdigest(), MIRRORED_SHA)
        self.assertEqual(len(data), MIRRORED_BYTES)
        self.assertNotIn(b"\r", data, "the blob is not LF-only, so the byte-identity claim would "
                                      "break between checkout and commit")

    def test_outside_original_is_untouched_when_this_machine_has_it(self) -> None:
        if not OUTSIDE_ORIGINAL.is_file():
            self.skipTest(f"{OUTSIDE_ORIGINAL} is not on this machine")
        data = OUTSIDE_ORIGINAL.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), MIRRORED_SHA,
                         "the outside original changed after the mirror, so the recovery point is "
                         "no longer reproducible")


if __name__ == "__main__":
    unittest.main()
