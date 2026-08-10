---
name: workflow-assistance-github-delivery
description: "Use for GitHub repositories, issues, pull requests, checks, Actions, releases, remotes, or exact-SHA cloud readback."
---

# GitHub delivery

Use `git` for local identity and `gh` or the GitHub API for remote state. Never read or print authentication files or tokens.

1. Inspect remote, branch, status, HEAD/tree, current upstream, explicit
   `origin/main`, and divergence. Report each pair separately; do not say only
   "local equals remote".
2. Fetch before relying on remote state; preserve local WIP.
3. For PR or release work, inspect the exact diff and required checks.
4. Treat commit, push, PR creation/comment/merge, tag, release, and remote deletion as distinct side effects requiring the user's requested scope.
5. Never force-push or rewrite history.
6. After an authorized push, fetch and verify local HEAD equals the remote branch SHA.
7. Bind CI and release evidence to that exact SHA and include URLs or IDs in the result.

A squash merge creates a new main SHA, so the PR head need not be an ancestor of
main. Confirm `state=MERGED`, read the PR `mergeCommit`, find that commit on main,
and verify main CI against the merge SHA. Keep branch publication, PR merge, and
post-merge main CI as distinct states.

If remote access or auth is unavailable, report the blocker rather than inventing repository state.
