---
name: workflow-assistance-single-writer-delivery
description: "Use for Git changes, parallel agents, code review, commits, pull requests, CI, merge, release, or delivery closure."
---

# Single-writer delivery

- One writer owns a checkout. Parallel implementation requires separate branches and worktrees.
- Capture branch, HEAD, tree, status, staged paths, and unstaged paths before work and before a verdict.
- Read-only review binds to an exact candidate tree. Any edit, rebase, rebuild, amend, or conflict resolution invalidates that verdict.
- Verification is not authorization to commit or publish.
- Before a requested commit, stage only intended paths, run staged checks, and record `git write-tree`.
- Before a requested push, fetch, verify the target branch and remote, push without force, then read back the remote SHA.
- CI evidence must match the exact delivered SHA. A green run for another SHA is not evidence.
- Merge, tag, release, remote deletion, and history rewrite require explicit approval for that exact action.
