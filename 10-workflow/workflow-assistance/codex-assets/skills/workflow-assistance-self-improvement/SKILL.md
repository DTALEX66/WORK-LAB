---
name: workflow-assistance-self-improvement
description: "Use when maintaining or growing the skill collection."
---

# Self-improvement (skill lifecycle)

## What this is

A client-neutral skill lifecycle: skills are usage-tracked, reviewed, and
archived-with-recovery instead of accumulating forever or being deleted. It
mirrors the auto-growth pattern personal agents use (usage sidecar,
active/stale/archived states, pin opt-out, archive-not-delete, backup before
transitions, provenance filter) without depending on any agent runtime.

## When to use

- A skill has not been used in a long time and the collection is growing.
- You created a skill during work and want it to persist across machines.
- You are reviewing which skills to keep, archive, pin, or fold into the module.

## Managed set (provenance filter)

Only skills with `created_by: agent` in SKILL.md frontmatter are managed.
Repository-owned, bundled, and manually authored skills are off-limits. The
module's own `workflow-assistance-*` skills are repository-owned: they are
never auto-archived.

## Lifecycle

- `active` → `stale`: no activity for `stale_after_days` (30);
- `stale` → `archived`: no activity for `archive_after_days` (90); moved to
  `.archive/` (recoverable) after a backup to `.backups/`;
- `pinned`: opt-out from all auto-transitions;
- archive is never delete.

## Running it (deterministic part)

```bash
python scripts/workflow/skill_lifecycle.py --root <skills-root> status
python scripts/workflow/skill_lifecycle.py --root <root> record <name> use
python scripts/workflow/skill_lifecycle.py --root <root> run --dry-run
python scripts/workflow/skill_lifecycle.py --root <root> archive <name>
python scripts/workflow/skill_lifecycle.py --root <root> restore <name>
python scripts/workflow/skill_lifecycle.py --root <root> pin <name>
python scripts/workflow/skill_lifecycle.py --root <root> backup <name>
```

## Review procedure (the judgment step)

1. Every cycle (e.g. weekly), list candidates from `status`: stale / archived.
2. For each candidate decide: **patch** (fold in new lessons), **pin**
   (still load-bearing), **consolidate** (merge into an umbrella skill), or
   leave archived (recoverable).
3. Patch with the module's skill-authoring standards: `description` ≤ 60
   chars, modern section order, scripts under `scripts/`, tests under
   `tests/`.
4. Fold durable lessons back into repository-owned module skills so they
   survive machine changes — the repo is the cross-machine persistent store.

## Cross-machine persistence

- The module repo carries the skills and this lifecycle tool; `sync` deploys
  them to any machine.
- Auto-grown knowledge persists by promoting it into the module's
  `codex-assets` skills (via PR) — never only in a machine-local sidecar.

## User environment preservation

Beyond skills, preserve the user's Hermes/Codex configuration and skill lists
in neutral, secret-free form so a machine change does not start from zero:

- Export: `python scripts/workflow/user_profile_export.py` — read-only against
  user homes; writes `config/user-environment-profile.json` (tracked) with
  non-secret config values, `.env` key names only, and skill inventories
  (Hermes skills, Codex `~/.agents/skills`).
- Redaction is fail-closed: any value matching a secret pattern is
  `[REDACTED]`; an unredacted value makes the export refuse to write.
- Restore: see `docs/workflow/user-environment-profile.md` — `sync` deploys
  the module skills; the profile tells you which config keys exist and which
  secrets must be re-entered on the new machine.
- The profile is a snapshot: re-run the exporter after meaningful config or
  skill changes and commit the refresh.

## Pitfalls

- Archiving a repository-owned skill (the provenance filter blocks it —
  `created_by: agent` only).
- Deleting instead of archiving (archiving keeps recovery).
- Trusting a machine-local sidecar as durable storage (promote to the repo).
- Skipping the backup step before a transition.

## Verification

- `status` shows the expected state/pinned flags and the managed/repo-owned
  split.
- `run --dry-run` reports what would transition without moving anything.
- An archived skill restores byte-identical via `restore`.
