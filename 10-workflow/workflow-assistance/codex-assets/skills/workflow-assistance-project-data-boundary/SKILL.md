---
name: workflow-assistance-project-data-boundary
description: "Use when a task creates caches, logs, evidence, temporary environments, generated artifacts, downloads, or agent runtime state."
---

# Project data boundary

Keep task-generated state inside the current Git project. Prefer:

- `.hermes/task-runtime/` for caches, logs, temporary files, virtual environments, and transient state.
- `.hermes/task-artifacts/` for user-deliverable evidence and bounded handoff artifacts.

Before writing, verify the destination is inside the intended repository and ignored by Git when it is runtime-only. Do not place project state in the user profile, another repository, a browser profile, an auth store, or an external drive without explicit path-level authorization.

Never read or copy `.env`, credentials, private keys, cookies, tokens, prompt/response bodies, or session databases. Avoid broad cleanup. Remove only exact, verified, regenerable paths authorized by the user.
