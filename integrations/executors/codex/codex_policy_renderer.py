#!/usr/bin/env python
"""U17.5 — Codex reference implementation of the Global Agent Policy projection.

Pipeline (taskpack section 8):

    config/global-agent-policy.yaml      (the neutral semantic core, the WHAT)
    + integrations/executors/codex/codex-policy-extension.yaml   (native knobs)
            ->
    CodexPolicyRenderer                  (this module, the HOW)
            ->
    integrations/executors/codex/global-guidance.md   (the new Golden Projection)
            ->
    integrations/executors/codex/sync_codex_global_assets.py   (the EXISTING syncer)
            ->
    native CODEX_HOME AGENTS.md managed block + config.toml

The renderer re-generates the golden ``global-guidance.md`` deterministically
from the policy + extension, and emits an honest ProjectionLossReport. It does
NOT rewrite the syncer: the syncer already owns the managed BEGIN/END block,
atomic writes, concurrent-modification detection, hash fencing, idempotent
NOOP, drift detection and rollback. The renderer only replaces the golden
CONTENT the syncer projects.

Section-10 drift cleanup is encoded here: the regenerated golden drops the
stale R4/R5 semantics (old ``.hermes/task-runtime`` paths, old
``scripts/workflow/...`` helpers, the "only one active item" global hard
limit, the over-absolute "session-never-read", and the long resident
Git/PowerShell tutorials). Those long-form techniques live in on-demand
skills, not in the global policy.

Usage:
    python integrations/executors/codex/codex_policy_renderer.py            # dry run, print golden + loss report
    python integrations/executors/codex/codex_policy_renderer.py --write   # rewrite the golden + persist the loss report
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "services" / "policy"))

import policy_projection as pp  # noqa: E402  (project-local module, see _REPO_ROOT insert)


def _section(title: str, bullets: list[str]) -> str:
    lines = [f"### {title}"]
    lines += [f"- {b}" for b in bullets]
    return "\n".join(lines)


class CodexPolicyRenderer(pp.SoftwarePolicyRenderer):
    """Project the neutral Global Agent Policy into the Codex native surface."""

    adapter = "codex"

    # Capability keys that become the Codex golden's prose sections, in order.
    _SECTION_ORDER = [
        "communication",
        "execution",
        "git_safety",
        "protected_storage",
        "credentials",
        "session_privacy",
        "network",
        "model_neutrality",
        "tool_truth",
        "evidence_semantics",
    ]

    # Render the neutral default_language code into a natural language name.
    # The existing syncer tests hard-code the phrase
    # "Communicate with the user in Chinese" for drift injection, so the
    # golden must carry that exact wording. This is a display mapping, not a
    # policy value.
    LANGUAGE_NAMES = {"zh": "Chinese", "en": "English"}

    def classify(self, policy: dict, extension: dict) -> dict[str, str]:
        """Codex capability states come from the extension's honest seed."""
        return dict(extension.get("capability_states", {}))

    def render(self, policy: dict, extension: dict) -> dict[str, str]:
        """Render the golden global-guidance.md from the policy + extension."""
        sections = extension.get("guidance_sections", {})
        lines = [
            "## WORK-LAB Workflow Assistance — Codex global execution overlay",
            "",
            "Generated from `config/global-agent-policy.yaml` (the single cross-software",
            "semantic source) plus the Codex native extension. Project instructions in a",
            "closer `AGENTS.md` may narrow these defaults for a project, but they can",
            "never weaken credential safety, the protected-storage boundary, or evidence",
            "honesty. Software-specific techniques that are not cross-software",
            "invariants live in on-demand skills, not in this global overlay.",
            "",
        ]

        # 1. communication / execution (from the neutral policy, not the extension)
        comm = policy.get("communication", {})
        execn = policy.get("execution", {})
        comm_bullets = [
            "Communicate with the user in "
            f"{self.LANGUAGE_NAMES.get(comm.get('default_language', 'zh'), comm.get('default_language'))}"
            " unless they request another language.",
        ]
        if comm.get("proceed_on_obvious_default") and comm.get("avoid_low_value_clarification"):
            comm_bullets.append(
                "Act on the obvious default instead of asking; ask only when ambiguity would change scope, risk, or the side effect."
            )
        lines += [_section("Communication and execution", comm_bullets + [
            "Keep work proportionate to task scale and risk; finish to closure with a concise plan for multi-step work.",
            "Inspect current repository state and real tool output before editing; never invent files, APIs, dependencies, or commands."
        ]), ""]

        # 2. git_safety / protected_storage / credentials / model_neutrality — from extension wording
        for cap in ("git_safety", "protected_storage", "credentials", "model_neutrality"):
            bullets = sections.get(cap, [])
            if bullets:
                title = {"git_safety": "Git safety", "protected_storage": "Protected storage and project data boundary",
                         "credentials": "Credentials and private state", "model_neutrality": "Model and provider neutrality"}[cap]
                lines += [_section(title, bullets), ""]

        # 3. session_privacy / network — neutral policy prose (honest, not over-absolute)
        sess = policy.get("session_privacy", {})
        net = policy.get("network", {})
        lines += [_section("Session privacy and network", [
            "Session and private state default to forbidden. Access follows the minimum-necessary ladder: metadata -> redacted summary -> raw body only when truly required.",
            "A permission denial on a private path is a correct boundary signal: stop and use repository evidence or a redacted user summary; never elevate to bypass it.",
            "Public read is scoped to the current sandbox/tool; authenticated write, upload, and paid calls require explicit authorization.",
        ]), ""]

        # 4. tool_truth / evidence_semantics — the hard invariants, prose-stated
        truth = policy.get("tool_truth", {})
        ev = policy.get("evidence_semantics", {})
        levels = ev.get("evidence_levels", [])
        lines += [_section("Evidence semantics and verification", [
            "Report real layers independently: PLANNED, BRANCH_PUBLISHED, IMPLEMENTED_LOCAL, TESTED_LOCAL, CI_VERIFIED_EXACT_SHA, MERGED_MAIN, and INSTALLED_RUNTIME_VERIFIED.",
            f"UNKNOWN is never 0 or SUCCESS; SIMULATED is never REAL; a local test is never CI; a build is never runtime; a merge is never installed.",
            f"Evidence level vocabulary: {' / '.join(levels)}." if levels else "Evidence must be real; a missing readback is UNVERIFIED, not PASS.",
            "Use real command output; keep working until verified, or report the exact blocker. Never fabricate state.",
        ]), ""]

        # 5. skills — on-demand, not resident
        skills = policy.get("skills", {})
        if skills.get("complex_techniques_are_on_demand_skills_not_global_policy"):
            lines += [_section("Skill use", [
                "Before executing, scan available skills (SKILL.md descriptions) and load the matching one; on a miss proceed directly — a skill is a manual, not authorization for side effects.",
                "Windows/Git/PowerShell and other long-form techniques are on-demand skills, not resident global policy.",
            ]), ""]

        return {
            "global-guidance.md": "\n".join(lines).rstrip() + "\n",
            "config.toml.managed_fields": json.dumps(
                extension.get("managed_config_values", {}), sort_keys=True
            ),
        }

    def golden_text(self, policy: dict, extension: dict) -> str:
        return self.render(policy, extension)["global-guidance.md"]


def build_renderer(root: Path) -> CodexPolicyRenderer:
    return CodexPolicyRenderer(root)


def write_golden(root: Path) -> dict:
    """Regenerate the golden global-guidance.md + persist the loss report."""
    renderer = build_renderer(root)
    result = renderer.project()
    extension = pp.load_extension(root, "codex")
    golden = result["assets"]["global-guidance.md"]
    golden_path = root / "integrations" / "executors" / "codex" / "global-guidance.md"
    golden_path.write_text(golden, encoding="utf-8")
    report_path = pp.write_loss_report(root, result["loss_report"])
    return {"golden": str(golden_path), "loss_report": str(report_path), "digest": pp.policy_digest(root)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write", action="store_true", help="regenerate the golden + persist the loss report")
    args = parser.parse_args()
    root = args.root

    renderer = build_renderer(root)
    result = renderer.project()  # fail-closed: validates the policy first

    if args.write:
        written = write_golden(root)
        print("CODEX_POLICY_WRITE golden=" + written["golden"])
        print("CODEX_POLICY_WRITE loss_report=" + written["loss_report"])
    else:
        print(result["assets"]["global-guidance.md"])
        print("--- loss report ---")
        print(json.dumps(result["loss_report"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
