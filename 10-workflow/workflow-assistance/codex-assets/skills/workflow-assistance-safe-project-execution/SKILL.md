---
name: workflow-assistance-safe-project-execution
description: "Use for any coding or project task that needs bounded scope, preserved user work, real execution, and honest completion evidence."
---

# Safe project execution

1. Resolve the Git root, branch, HEAD, applicable `AGENTS.md`, dirty paths, and owning module before edits.
2. Classify dirty paths as task-owned or unknown. Preserve unknown work and stop before overlapping writes.
3. Inspect relevant files, definitions, usages, manifests, and neighboring conventions before designing the change.
4. Keep one writer per checkout. Use an isolated worktree for a parallel writer.
5. Make the smallest coherent change. Do not refactor unrelated code or fabricate APIs and dependencies.
6. Run targeted checks, then the repository's canonical gate when available.
7. Inspect the final diff and status. Separate local verification from CI, publication, and live readback.
8. Do not commit, push, publish, or change global configuration without explicit authorization for that side effect.

If a prerequisite or required check cannot run, report `BLOCKED` or `NOT EXECUTED`; never substitute plausible output.
