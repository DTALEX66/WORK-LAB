# WORK-LAB execution rules

> 全局执行标准（跨软件跨项目）：见 `00-governance/global-execution-standard.md`（执行生命周期：理解→扫技能→分片→执行→验证→落地）。
> 经验教训铁律（核实优先/治理最小化/官方优先）：见 `00-governance/LESSONS_LEARNED.md`。

## Scope

This is a single-root monorepo. Allowed active module roots are exactly:
`10-workflow/workflow-assistance` and `30-observer/work-lab-observer`. The
managed client workflow is Hermes · Codex · CC Switch · GitHub · Open Design ·
OpenHuman, plus any future AI software through the same Adapter contract.
DSH (DeepSeek Harness / DSH Desktop 2.0.4 community desktop) is a managed agent runtime client
through the same Adapter contract. CC Switch is LEGACY_OBSERVE (observe-only;
no active writes) unless evidence restores it to active status.
Open Design is an external *client* (`nexu-io/open-design`); the separate
`DTALEX66/DESIGN-LAB` project owns its own design domain (historical migration
alias: `DTALEX66/OPEN-DESIGN-Assistance`).

### Open Design client vs DESIGN-LAB project (two distinct identities)

WORK-LAB manages the Open Design **client** USER_GLOBAL desired state (rules,
skills, plugins, workflow policy, capability mapping) as `MANAGE` with
`apply_supported=false` until a reviewed adapter and stable official interface
exist. Since 2026-08-21 the user authorized WORK-LAB to manage Open Design
**plugins** (install/update/inventory of the client plugin layer); design
**capability** (models/tools/generation params/assets/specs/quality gates) stays
with `DTALEX66/DESIGN-LAB` and is not managed here. Design **capability** (models/tools, generation params, design assets,
specs, design systems, quality gates, editable handoff) belongs to the
`DTALEX66/DESIGN-LAB` project and is **neither collected nor managed here**
(`IGNORE`). Field-level ownership lives in
`10-workflow/workflow-assistance/config/config-ownership.json` (adapter
`open-design`, external project `design-lab-project`).

## Ownership

One writer owns a task. Read-only reviewers may inspect exact trees but may not
edit them. Cross-module changes require one explicit cross-module task card.
Module instructions can narrow these rules, never weaken them.

## Safety

Do not read, print, copy, commit, or upload credentials, `.env` files, auth
stores, private keys, browser data, tokens, prompt bodies, or response bodies.
Never access `E:\` — read or write — without explicit per-path,
per-operation user authorization. All content this project produces — builds,
caches, temp files, evidence, downloads, generated artifacts — stays locked
inside the project Git root: build/cache/temp roots live under
`.project-local/runs/` (TMP, npm/uv/pip caches, node_modules), evidence under
`.project-local/artifacts/` or ignored `80-evidence/`; nothing spills to user
directories, other projects, or the shared library unless explicitly
authorized. Any spill is traceable, locatable, cleanable and migratable
(`00-governance/project-data-boundary.json`). Never use destructive
reset/clean/force-push operations.

## Managed global configuration (Hermes)

WORK-LAB manages a declared Hermes user overlay on the official baseline:
the managed **assets** — 13 skills under `skills/`, `config/SOUL.md`, and
`bin/` launchers (`codex`, `codex.cmd`, `hermes-npx`, `hermes-npx.cmd`,
`hermes-project-data.py`, `hermes-project-terminal-guard.py`). The managed
**config fields** are only `display.language` and `display.busy_input_mode`;
every other Hermes field (`sessions.auto_prune`, `memory.*`,
`hooks.pre_tool_call`, `mcp_servers.*`, `hermes.model.*`, `plugins`) is
OBSERVE — never overwritten. `config-ownership.json` (WL3-200) is the single
authority for field layers and modes; `preserve_unknown: true` — never
override user provider/model/auth/desktop state. Deploy to Hermes Home only
through `sync_hermes_workflow_assets.py` (backup-before-publish staging,
updates `skill-provenance.yaml` live hashes in the same change); never
promote the mixed-ownership live `config.yaml` wholesale.

## Verification

Run checks from the exact module path. Report structural checks separately from
live execution checks. Any failed, cancelled, missing, or skipped required job
fails the aggregate gate.

## Workflow Assistance execution contract

`10-workflow/workflow-assistance` is the active owner of workflow configuration,
Task Ledger, Telemetry Ledger, sidecar, adapters, and delivery gates.
`30-observer/work-lab-observer` is a strict read-only projection: it may read
Workflow-owned projections but must not execute, approve, retry, apply, rollback,
change task state, or write the Telemetry Ledger.

When working through Codex, use the project-local workflow contract and exact
module paths. Bounded writers own one checkout; parallel writers require separate
worktrees. Prefer the canonical quality gate:
`python 10-workflow/workflow-assistance/scripts/workflow/run_quality_gate.py verify`.
Keep Task Ledger and runtime evidence under `.project-local/runs/` and
`.project-local/artifacts/`; do not treat local tests as exact-SHA CI or release
evidence. Codex may prepare changes and readback evidence, but must not commit,
push, publish, or modify global Codex/Hermes configuration without explicit
approval for that side effect.

## Five-dimension runtime baseline (mandatory, audited)

Every managed software surface must satisfy — and every audit must verify — the
following baseline, owned by the enhancement module:

1. **Unique entry per software.** One canonical launch path per tool — the
   OFFICIAL standard release format (whatever the vendor ships is the entry).
   Hermes: official desktop app (`apps/desktop/release/win-unpacked/Hermes.exe`,
   Electron) + `hermes` CLI; Codex: single wrapper (`bin/codex` bash +
   `bin/codex.cmd`, identical versioned-glob resolution to the official
   runtime); DSH: DSH Desktop 2.0.4 (community desktop, Electron, `D:\All projects\DSH\DSH Desktop.exe`);
   CC Switch / OpenHuman / Open Design: single desktop shortcut to
   their installed official executables. No duplicate or conflicting launchers;
   entries are the official standard formats — WORK-LAB never invents custom
   launcher formats (e.g. .vbs) that replace the vendor-shipped binary.
2. **Desktop entry.** Every GUI tool opens from its desktop shortcut; shortcut
   target chains must resolve (Test-Path true end-to-end).
3. **Official standard + user configuration.** Official baselines win; the
   enhancement module only manages declared overlay fields and never overrides
   user provider/model/auth/desktop state (`config-ownership.json`,
   `preserve_unknown: true`).
4. **No blocking overhead.** Global rules/skills/guidance must stay lean
   (skills ~<10KB each, guidance+rules <20KB total) and load on demand, never
   blocking startup or execution. Wrappers must not stall on missing candidates.
5. **Task-level model policy.** Each task declares its own quality/cost/privacy/
   latency constraints (four-dimensional strategy). Provider routing is official
   (cost_multiplier=1.0, no daily/monthly caps by default); reasoning_effort
   defaults to official baseline (empty = medium) or higher unless the task
   explicitly downgrades with justification. Pricing must include
   provider/model/currency/effective_at/source/version; missing fields display
   UNKNOWN. No global rate limits or cost caps — constraints are per-task and
   auditable.

When any dimension regresses (new entry point, config bloat, provider cap,
reasoning downgrade), fix at the root and record in the error ledger before
merging.
