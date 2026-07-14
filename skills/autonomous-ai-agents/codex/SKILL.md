---
name: codex
description: "Delegate bounded coding or read-only review tasks to the OpenAI Codex CLI; use isolated worktrees for writers."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [agent-workflow-fortress, hermes-agent]
---

# Codex CLI

Use Codex for a clearly bounded coding task, refactor, or independent review. This skill owns CLI invocation only. `agent-workflow-fortress` owns writer isolation, frozen-tree review, commit/push authorization, and CI closure.

## Live CLI semantics

Current verified CLI: `codex-cli 0.144.2`.

- `codex` without a subcommand is an interactive TUI: use `pty=true`.
- `codex exec`, `codex review`, and `codex exec review` are non-interactive: use `pty=false` (default).
- Current CLI does not expose `--full-auto` or `--yolo`; never invent or reuse removed flags.
- A normal task should run in a Git repository. For an intentional read-only/scratch non-repo task, use the documented `--skip-git-repo-check` option if `codex exec --help` still lists it.
- Re-check `codex --version` and relevant `--help` when commands fail; flags are not stable contracts.

On this Windows machine, prefer the desktop plugin binary when it is newer than PATH:

```text
C:/Users/ALEX/.codex/plugins/.plugin-appserver/codex.exe
```

Do not read or copy Codex/Hermes auth files. Use each product's supported login flow.

## One-shot execution

```python
terminal(
    command='codex exec --sandbox workspace-write "Implement the bounded task. Do not commit or push."',
    workdir='D:/All projects/repo-worktree',
    timeout=600,
)
```

`exec` does not need a PTY. If it is a long bounded run:

```python
terminal(
    command='codex exec --sandbox workspace-write "<bounded task>"',
    workdir='<isolated-worktree>',
    background=True,
    notify_on_complete=True,
)
```

Monitor with `process(log/poll)`; do not edit the same checkout while Codex owns it.

## Read-only review

```python
terminal(
    command='codex exec --sandbox read-only "Review only the staged Git index. Do not modify files."',
    workdir='<repo>',
    timeout=600,
)
```

Bind a release verdict to an exact staged tree. If read-only sandbox prevents `git write-tree` because Git wants an index lock, compute/verify the tree outside Codex first and pass the expected hash; Codex may inspect with `git diff --cached` and `git show :path`.

## Interactive TUI

Only the interactive TUI requires PTY:

```python
terminal(command='codex', workdir='<repo>', pty=True)
```

## Parallel writers

Parallel Codex writers are allowed only in separate Git worktrees/branches. The orchestrator serially integrates shared files. Read-only reviewers may share an already frozen candidate tree.

Codex must not commit, push, merge, create PRs, or post comments unless the user explicitly authorized that side effect. Review is not authorization to publish.

## Sandbox escalation

Use the narrowest working sandbox (`read-only` for review, `workspace-write` for a bounded writer). Never automatically bypass approvals/sandbox because of a gateway, Windows helper, bubblewrap, or permission failure.

The current CLI may expose a prominently dangerous bypass flag. Use it only when:

1. the user explicitly authorizes that exact run;
2. the task is in an isolated disposable worktree/environment;
3. allowed and forbidden paths are stated;
4. a clean baseline and rollback exist;
5. the final diff and tests are reviewed before any publication.

Otherwise stop and report the sandbox blocker.

## Rules

1. One writer per checkout; separate worktrees for parallel writers.
2. `exec/review`: non-PTY; interactive TUI: PTY.
3. Explicit `workdir`, scope, allowed/forbidden paths, and completion evidence.
4. No credentials in prompts, command arguments, logs, or copied auth files.
5. No automatic commit/push or sandbox bypass.
6. Any edit after a frozen review invalidates the verdict.
