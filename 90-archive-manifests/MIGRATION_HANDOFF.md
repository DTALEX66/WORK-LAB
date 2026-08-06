# Migration handoff

## Destination

- Repository: `DTALEX66/WORK-LAB`
- Local active target: `D:\All projects\WORK-LAB`
- Candidate used for this handoff: `D:\All projects\WORK-LAB-STAGING-20260805T091816Z`

## Imported module roots

| Module | Canonical path | Selected source tip |
|---|---|---|
| Workflow | `10-workflow/workflow-assistance` | `aee5d72c47d05eb88c77c41fdb69c485f6c192ee` |
| Open Design | `20-design/open-design` | `c8212401e891e7c3f0e4a6f36cdb11dbcca24e27` |
| MINIGAME | `30-products/minigame` | `d4bf0b3d33d0d97c469dbfedd969f4ec4801bfa2` |

Each imported tip is a merge parent of the candidate migration commit and its
module tree is parity-checked against the selected source tree. The MINIGAME local tip `ddd1ee18…` and all dirty/local-only state remain preserved outside this active Git root; the local committed tip is also published as `migration/minigame-local-head` and tag `minigame/local-head-20260805T091816Z`. Remote `main` keeps the user-selected freeze `d4bf0b3d…`.

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

The final active task graph is the attached
`WORK-LAB-HERMES-TASKPACK-v1.0.0.zip`; its reconciliation is recorded at
`50-taskpacks/WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md`. Historical `MIG-*`
and `GOV-*` claims are namespaced as `HIST-*` in that reconciliation.

Local active-path switching, legacy archive changes, product release, Hermes
live apply, and any force/destructive operation remain approval-gated. This
handoff does not claim current live platform builds, cloud CI, or production
release evidence.
