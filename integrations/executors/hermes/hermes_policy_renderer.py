#!/usr/bin/env python
"""U17.6 — Hermes reference implementation of the Global Agent Policy projection.

Pipeline (taskpack section 12/13, mirroring the Codex reference implementation):

    config/global-agent-policy.yaml        (neutral semantic core, the WHAT)
    + integrations/executors/hermes/hermes-policy-extension.yaml   (native knobs)
            ->
    HermesPolicyRenderer                   (this module, the HOW)
            ->
    config/SOUL.md                         (the repo-managed Hermes SOUL source)
            ->
    integrations/executors/hermes/sync_hermes_workflow_assets.py    (the EXISTING syncer)
            ->
    live Hermes home SOUL.md (via the three-way managed_asset_baseline)

The renderer regenerates the managed ``config/SOUL.md`` deterministically from
the neutral policy + the Hermes native extension, and emits an honest
ProjectionLossReport. It does NOT rewrite the syncer, the three-way baseline,
or the curator foldback: those already own ownership diffing, backup-before-
publish, readback, and append-only foldback. The renderer only refreshes the
SOUL content the syncer projects.

Section-12/13 rules honored here:
- SOUL stays short: only the high-frequency, stable body + the machine-enforced
  boundary sections. Long-form technique stays in on-demand skills.
- provider / model / reasoning / auth / unknown live config are NEVER written.
- The existing three-way baseline (repo vs live vs candidate) and the curator
  foldback (append-only auto-fold; deletion/rewrite -> NEEDS_REVIEW) are
  untouched.

Usage:
    python integrations/executors/hermes/hermes_policy_renderer.py            # dry run, print SOUL + loss report
    python integrations/executors/hermes/hermes_policy_renderer.py --write    # rewrite config/SOUL.md + persist loss report
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "services" / "policy"))

import policy_projection as pp  # noqa: E402  (project-local module)


class HermesPolicyRenderer(pp.SoftwarePolicyRenderer):
    """Project the neutral Global Agent Policy into the Hermes managed SOUL."""

    adapter = "hermes"

    def classify(self, policy: dict, extension: dict) -> dict[str, str]:
        """Hermes capability states come from the extension's honest seed."""
        return dict(extension.get("capability_states", {}))

    def render(self, policy: dict, extension: dict) -> dict[str, str]:
        """Render the managed config/SOUL.md from the policy + extension."""
        header = (extension.get("soul_header") or "").strip()
        sections = extension.get("soul_sections", {})
        lines = [header] if header else []

        # Each extension section becomes a short markdown heading + bullets.
        section_titles = {
            "proactive_completion": "主动完成",
            "project_rules_first": "项目规则优先",
            "no_fabrication": "不伪造、证据分层",
            "protected_drive_boundary": "E/F 盘边界",
            "credential_boundary": "凭据与私有状态边界",
            "minimum_privilege": "最小权限与项目数据边界",
            "model_neutral": "模型与 provider 中立",
            "authorization_semantics": "授权语义",
        }
        for key, bullets in sections.items():
            if not bullets:
                continue
            title = section_titles.get(key, key)
            lines += [f"## {title}"]
            lines += [f"- {b}" for b in bullets]
            lines += [""]

        # Neutral-policy cross-check: the rendered SOUL must still carry the two
        # hard invariants that the loss report marks as guard/enforced, so a
        # policy flip that weakens them is visible in the artifact too.
        ev = policy.get("evidence_semantics", {})
        if ev.get("unknown_is_success") is False or ev.get("unknown_is_zero") is False:
            lines += [
                "## 铁律",
                "- UNKNOWN 不等于 0 也不等于 SUCCESS；SIMULATED 不等于 REAL；本地测试不等于 CI；merge 不等于 installed。",
                "- 缺 native readback 时状态只能是 APPLIED_UNVERIFIED，不得写成 VERIFIED。",
                "",
            ]

        body = "\n".join(lines).rstrip() + "\n"
        return {"config/SOUL.md": body}

    def golden_text(self, policy: dict, extension: dict) -> str:
        return self.render(policy, extension)["config/SOUL.md"]


def build_renderer(root: Path) -> HermesPolicyRenderer:
    return HermesPolicyRenderer(root)


def write_soul(root: Path) -> dict:
    """Regenerate the managed config/SOUL.md + persist the Hermes loss report."""
    renderer = build_renderer(root)
    result = renderer.project()  # fail-closed: validates the policy first
    body = result["assets"]["config/SOUL.md"]
    soul_path = root / "config" / "SOUL.md"
    soul_path.write_text(body, encoding="utf-8")
    report_path = pp.write_loss_report(root, result["loss_report"])
    return {"soul": str(soul_path), "loss_report": str(report_path), "digest": pp.policy_digest(root)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write", action="store_true", help="regenerate config/SOUL.md + persist the loss report")
    args = parser.parse_args()

    renderer = build_renderer(args.root)
    result = renderer.project()

    if args.write:
        written = write_soul(args.root)
        print("HERMES_POLICY_WRITE soul=" + written["soul"])
        print("HERMES_POLICY_WRITE loss_report=" + written["loss_report"])
    else:
        print(result["assets"]["config/SOUL.md"])
        print("--- loss report ---")
        print(json.dumps(result["loss_report"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
