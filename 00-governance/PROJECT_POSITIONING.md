# WORK-LAB canonical project positioning

**Position:** current v2 monorepo control plane — not a product runtime and not a fourth product.

**Repository:** `DTALEX66/WORK-LAB`

## What this repository is

WORK-LAB is the auditable control plane for client-neutral AI workflow governance: task packs, ownership, single-writer boundaries, project data containment, contracts, evidence, recovery, cross-module integration and exact-SHA CI.

## Current canonical modules

These are the only active module roots:

1. `10-workflow/workflow-assistance` — client-neutral workflow governance, execution control, portable contracts and delivery boundaries.
2. `30-observer/work-lab-observer` — strictly read-only derived observation, projections and evidence reports.

Open Design was transferred to `DTALEX66/OPEN-DESIGN-Assistance` on the
authorized migration branch. WORK-LAB retains only the one-time pointer under
`90-archive-manifests/`; it no longer owns or executes that module.

### Open Design configuration boundary (two-tier)

WORK-LAB is responsible for the Open Design **non-design global configuration**
— the migration pointer, registry, directory mapping, MCP declarations and
audit boundary. These are owned and `MANAGE`d by WORK-LAB. Any configuration
that would **enhance design capability** (models/tools, generation params,
design assets, design specs, design systems, quality gates, editable handoff)
belongs to the `OPEN-DESIGN-Assistance` project itself and is **neither
collected nor managed here** (`IGNORE`). Field-level ownership lives in
`10-workflow/workflow-assistance/config/config-ownership.json` (adapter
`open-design`).

The root owns governance and integration. It does not duplicate module implementations.

## Explicit non-positioning

WORK-LAB is **not**:

- Hermes, Codex, CC Switch or another agent runtime;
- a model/provider gateway, credential store, chat UI or prompt/response archive;
- a platform deployment service, commercial marketplace or release host;
- an active MINIGAME product repository;
- permission to apply Hermes live configuration, modify external systems, or publish releases.

## MINIGAME boundary

`30-products/minigame` is retained as product history, fixture/reference material and migration/archive evidence. It is not an active canonical module. No automatic merge, deletion, retirement, platform selection, real-device validation or commercial claim is implied.

## Evidence boundary

Local structural/module gates and exact-SHA GitHub Actions are separate from Hermes live state, real adapters, external platforms, devices, licenses, commercial experiments and release evidence. Unknown or unverified capabilities remain explicitly labeled as such.

## Authoritative source files

- `00-governance/projects.json` — canonical module registry;
- `00-governance/module-ownership.json` — ownership and writer boundary;
- `00-governance/contracts/contract-catalog.json` — canonical contract catalog;
- `50-taskpacks/TASKPACK_SUMMARY.md` — current task-pack summary;
- `50-taskpacks/WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md` — v2 reconciliation and historical mapping;
- `README.md` — public repository entrypoint.

If another README, historical handoff or external description conflicts with this file and the machine-readable registries, classify it as stale documentation and update it; do not infer a second architecture.
