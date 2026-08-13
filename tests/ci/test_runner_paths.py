"""WLG-050: runner path hardcoding regression tests.

Active docs/skills must reference the runner by repository-relative path or a
stable CLI, never by a machine-specific absolute path. Historical archive
records may keep legacy paths for migration traceability.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_HINTS = (
    "10-workflow/workflow-assistance/skills/model-switch/SKILL.md",
    "10-workflow/workflow-assistance/skills/model-switch/references/current-model-lanes.md",
)
ARCHIVE_HINTS = (
    "90-archive-manifests/",
    "00-governance/migration-status.json",
    "50-taskpacks/WORK-LAB-HERMES-TASKPACK-RECONCILIATION.json",
)


class RunnerPathHardcodingTests(unittest.TestCase):
    def test_active_skill_docs_have_no_machine_absolute_paths(self):
        for rel in ACTIVE_HINTS:
            path = ROOT / rel
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("D:/All projects", text, f"{rel} must not hardcode a machine path")
            self.assertNotIn("C:\\Users", text, f"{rel} must not hardcode a user path")

    def test_active_skill_docs_use_repository_relative_runner_path(self):
        skill = (ROOT / "10-workflow/workflow-assistance/skills/model-switch/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "10-workflow/workflow-assistance/scripts/workflow/switch_model.py",
            skill,
            "SKILL.md must invoke the runner via repository-relative path",
        )
        self.assertNotIn("python scripts/workflow/", skill)

    def test_runner_entrypoint_is_discoverable_from_repo_root(self):
        runner = ROOT / "10-workflow/workflow-assistance/scripts/workflow/switch_model.py"
        self.assertTrue(runner.exists(), "runner must exist at documented relative path")

    def test_archive_records_may_keep_legacy_paths(self):
        # migration-status.json documents legacy local paths for migration
        # traceability; that is historical record, not active usage.
        migration = (ROOT / "00-governance/migration-status.json").read_text(encoding="utf-8")
        self.assertIn("legacyLocalPaths", migration)


if __name__ == "__main__":
    unittest.main()
