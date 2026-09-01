# DeepSeek Harness (DSH) — agent-runtime adapter

DSH is an **agent runtime** adapted into WORK-LAB as a replaceable,
approval-gated executor. It runs bounded agent tasks in an isolated, task-scoped
Git worktree. It is **not** a WORK-LAB core module, not a model gateway, not a
Hermes replacement, and it never writes client config or completes a Task Ledger
task.

- Adapter id: `deepseek-harness` · kind: `agent_runtime`
- Upstream: `deepseek-ai/deepseek-harness` pinned at `47f943859bef60e4160492346772ded9b24f765a`
- Upstream version `0.1.0-rc.5` (developer preview), license `MIT`
- `packageManager: pnpm@11.7.0`, `engines.node: ^22.19.0 || >=24.0.0`

## Contract invariants (taskpack §4.1)

| Field | Value |
|---|---|
| `install_mode` | `isolated_source_checkout` |
| `entrypoints` | `web`, `headless` (single launcher, no dual entry) |
| `network` | `loopback_only` — `127.0.0.1` (localhost / ::1), port `3080` default, dynamic conflict detection |
| `workspace_scope` | `task_scoped_git_worktree_only` |
| `secrets` | `runtime_secret_only` — never in repo/receipt/Observer |
| `execution_authority` | `execute_only_no_task_completion_authority` |
| `external_mutation` | `approval_required` |
| `plugin_policy` | `builtins_only` |
| `upgrade_policy` | `pinned_commit + explicit_upgrade_task + compatibility_evidence` |
| `rollback` | stop recorded PID → preserve read-only evidence → quarantine runtime → restore previous verified commit |

## Runtime directory (git-ignored, never committed)

```
.project-local/runs/deepseek-harness/
├─ source/    # pinned checkout @ 47f94385 (never committed)
├─ dsh-home/  # DSH_HOME: profiles, credentials, settings, sessions (never committed)
├─ launch/    # local start/stop scripts + pid/port state
├─ logs/      # local, redacted logs
└─ receipts/  # minimal execution receipts
```

## Start / stop / health (WL-DSH-030/040 — approval-gated)

These are **not** performed by the adapter by default; each is an approval item.

- **Install**: clone + checkout the pinned SHA, then
  `corepack pnpm@11.7.0 install --frozen-lockfile` (per-invocation, no global
  toolchain mutation), `corepack pnpm@11.7.0 run typecheck`, `… run build`.
- **Start web**: bind `127.0.0.1` only, with `DSH_HOME=<project>/.project-local/runs/deepseek-harness/dsh-home`.
  On port conflict, fail closed — do not kill an unknown PID; record an idle
  loopback port or stop and report.
- **Health**: `--dump-config` redacted + a loopback socket readback; never a
  screenshot as proof of binding.

## Configuration location (no values)

DSH config and credentials live under `DSH_HOME` (the `dsh-home/` dir above).
The model key is entered by the user in the DSH Web UI; Hermes never reads,
displays, or writes it, and only verifies a redacted credential descriptor.

## Permissions

- Workspace must be a Git worktree under the project — never `D:\All projects`
  itself, never the user home, never a drive root.
- Default: no file-write / command / network permission outside the approved
  task; every external mutation is approval-required.

## Evidence (receipt)

A receivable receipt may only contain: `task_id`, `adapter_id`, `upstream_commit`,
start/end time, repo-relative workspace id, command kind, approval result, exit
code, test summary, file-change summary (path+hash), error kind, evidence hash.

Forbidden in any receipt: API keys, full prompts, full responses, source text,
raw session ids, private paths, provider-private headers, unredacted logs.

## Failure classes and rollback

- **Commit drift** → re-pin to `47f94385`, re-review before any run.
- **Non-loopback listener** → stop and report immediately.
- **Unknown PID** → never kill; quarantine the runtime and stop for manual handling.
- **Secret in dump/receipt** → fail closed, redact, do not serialize.

Rollback: stop only the recorded PID, close the loopback listener, mark the
runtime `QUARANTINED`, keep source commit + lockfile fingerprint; handle the
versioned adapter change via non-destructive Git revert (never reset/clean).

## Upgrade

Any upstream upgrade is a separate `WL-DSH-UPGRADE-*`: change audit → new commit
pin → clean runtime canary → schema/adapter compatibility → rollback rehearsal →
approval. Never `git pull` to follow master.
