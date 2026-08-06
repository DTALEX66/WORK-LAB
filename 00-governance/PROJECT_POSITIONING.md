# WORK-LAB canonical project positioning

**Position:** current v2 monorepo control plane — not a product runtime and not a fourth product.

**Repository:** `DTALEX66/WORK-LAB`

## What this repository is

WORK-LAB is the auditable control plane for client-neutral AI workflow governance: task packs, ownership, single-writer boundaries, project data containment, contracts, evidence, recovery, cross-module integration and exact-SHA CI.

## Current canonical modules

These are the only active v2 module roots:

1. `10-workflow/workflow-assistance` — client-neutral workflow governance, execution control, portable contracts and delivery boundaries.
2. `20-design/open-design` — Open Design-first professional design knowledge, visual quality, production handoff and provenance evidence.
3. `30-observer/work-lab-observer` — strictly read-only derived observation, projections and evidence reports.

The root owns governance and integration. It does not duplicate module implementations.

## Explicit non-positioning

WORK-LAB is **not**:

- Hermes, Codex, CC Switch or another agent runtime;
- a model/provider gateway, credential store, chat UI or prompt/response archive;
- a platform deployment service, commercial marketplace or release host;
- an active MINIGAME product repository;
- permission to apply Hermes live configuration, modify external systems, or publish releases.

## MINIGAME boundary

`30-products/minigame` is retained as product history, fixture/reference material and migration/archive evidence. It is not one of the three active v2 canonical modules. No automatic merge, deletion, retirement, platform selection, real-device validation or commercial claim is implied.

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
