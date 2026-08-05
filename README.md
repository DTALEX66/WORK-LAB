# WORK-LAB

`DTALEX66/WORK-LAB` is the canonical monorepo for three independently owned modules:

- `10-workflow/workflow-assistance` — client-neutral workflow governance and execution control
- `20-design/open-design` — design knowledge, visual quality and production handoff
- `30-products/minigame` — independent game product and revenue proof

The repository preserves each source history through merge commits and keeps module implementations under their canonical prefixes. Root governance owns only stable contracts, task/evidence formats, CI and release policy; it does not duplicate module implementations.

## Safety boundaries

- One Git root; module rules may narrow root rules but never weaken them.
- `80-evidence/` and `.hermes/task-runtime/` are generated/ignored data.
- Secrets, credentials, prompt/response bodies and private browser data never enter evidence.
- External mutation, active-path switching and release actions require explicit approval.
- Windows paths are checked case-insensitively before release.

See `00-governance/`, module `AGENTS.md` files, and `MIGRATION_LEDGER.json` for the current migration record.
