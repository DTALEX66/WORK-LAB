# Task packs

`50-taskpacks/` is the root control surface for WORK-LAB's global project-task
workflow. It coordinates work across the three canonical modules without turning
the root into a fourth product.

Every non-trivial task pack records:

- one writer and any read-only reviewers;
- canonical module/root ownership and explicit cross-module permission;
- allowed and forbidden paths, including the project-local `.hermes/` data boundary;
- RED/GREEN, targeted, aggregate, exact-tree and recovery verification;
- external mutation, commit, push, merge and release approval gates;
- a completion contract and a durable recovery handle.

Parallel inspection is allowed; source modification remains single-writer and
fail-closed. Execution evidence belongs in ignored `.hermes/task-artifacts/` or
`80-evidence/`, never in source control and never in the global Hermes Home.

The task-pack directory stores reviewed manifests and stable summaries only; live
queues, logs, caches, sessions, credentials and scheduler state remain runtime
data outside the tracked tree.
