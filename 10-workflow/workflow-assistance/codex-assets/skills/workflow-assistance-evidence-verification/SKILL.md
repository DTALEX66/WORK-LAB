---
name: workflow-assistance-evidence-verification
description: "Use when verifying implementation, builds, tests, desktop/runtime behavior, CI, publication, releases, or completion claims."
---

# Evidence verification

Classify evidence before claiming completion:

1. Structural: files, schemas, static checks, and source inspection.
2. Local execution: tests, builds, and runtime checks on the current checkout.
3. Exact-SHA CI: required remote jobs for the precise commit.
4. Publication: remote branch, package, release, installer, or URL readback.
5. Live behavior: the actual target runtime restarted and behaviorally verified.

Run required checks from the owning module. A failed, cancelled, missing, or required-but-skipped check is not a pass. Fixtures, screenshots of source, documentation, version strings, and local tests cannot substitute for higher evidence levels.

Finish with explicit `PASS`, `PARTIAL`, `NOT EXECUTED`, and `BLOCKED` states plus the command, path, SHA, URL, or runtime handle that grounds each claim.
