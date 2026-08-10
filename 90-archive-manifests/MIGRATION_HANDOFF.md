# Migration handoff

> **Historical record only.** This handoff describes the earlier migration
> snapshot and is not the current project architecture. The current v2 active
> active canonical module. See `00-governance/PROJECT_POSITIONING.md`.

## Destination

- Repository: `DTALEX66/WORK-LAB`
- Local active target: `D:\All projects\WORK-LAB`
- Candidate used for this handoff: `D:\All projects\WORK-LAB-STAGING-20260805T091816Z`

## Imported module roots

| Module | Canonical path | Selected source tip |
|---|---|---|
| Workflow | `10-workflow/workflow-assistance` | `aee5d72c47d05eb88c77c41fdb69c485f6c192ee` |

Each imported tip is a merge parent of the candidate migration commit and its

## Evidence and recovery

Recoverable bundles and working-state preservation are outside the active root:
`D:\All projects\WORK-LAB-ARCHIVE\20260805T091816Z\`. Machine-readable maps
are in the local ignored task artifacts and the committed governance summary.
Do not delete the archive until an independent restore drill passes.

## Historical handoff boundary

This document records the historical migration handoff and must not be read as
current completion evidence for the attached task-pack. The current tree is
dirty and its migration status is explicitly marked
`HISTORICAL_SNAPSHOT_STALE_FOR_CURRENT_TREE`.

The final active task graph is the attached v2
`WORK-LAB-HERMES-TASKPACK-v2.0.0.zip`; its reconciliation is recorded at
`50-taskpacks/WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md`. Historical `MIG-*`
and `GOV-*` claims are namespaced as `HIST-*` in that reconciliation.

Local active-path switching, legacy archive changes, product release, Hermes
live apply, and any force/destructive operation remain approval-gated. This
handoff does not claim current live platform builds, cloud CI, or production
release evidence.
