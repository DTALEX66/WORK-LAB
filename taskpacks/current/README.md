# Task packs

`taskpacks/` is the root control surface for WORK-LAB's global project-task
workflow. It coordinates the canonical active modules without turning the root into
a fourth product. The authoritative public positioning is
`docs/decisions/PROJECT_POSITIONING.md`; the current authority is named by
`.project/governance/taskpack-authority-index.json` (`currentTaskpack`), whose
`staticHandoffViews` register static handoff archives by sha256.

Every non-trivial task pack records:

- one writer and any read-only reviewers;
- canonical module/root ownership and explicit cross-module permission;
- allowed and forbidden paths, including the `.project-local/` per-project data boundary;
- RED/GREEN, targeted, aggregate, exact-tree and recovery verification;
- external mutation, commit, push, merge and release approval gates;
- a completion contract and a durable recovery handle.

Parallel inspection is allowed; source modification remains single-writer and
fail-closed. Execution evidence belongs in the ignored per-project boundary —
`.project-local/artifacts/` (or `reports/`) — never in source control and never in the
global Hermes Home.

The task-pack directory stores reviewed manifests and stable summaries only; live
queues, logs, caches, sessions, credentials and scheduler state remain runtime
data outside the tracked tree.

The current v2 attachment reconciliation is recorded in
`WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md` and its machine-readable `.json`
counterpart. Historical task IDs are namespaced as `HIST-*` there so they do not
silently satisfy the final attachment task graph.

Maintenance rounds are recorded here as well when they change a managed software
surface; see `HERMES-UNIFIED-GOVERNANCE-20260915.md` and
`HERMES-UPDATE-AND-FIXES-20260917.md`.
