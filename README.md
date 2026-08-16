# WORK-LAB

`DTALEX66/WORK-LAB` is the canonical monorepo control plane for the user's
**client-neutral AI workflow global-configuration layer**. It manages the
highest user-level capability layer — Rules, Skills, plugins/MCP declarations,
portable Memory, Capabilities and workflow policy — as one canonical source,
then adapts it into native projections for each current client. It is not an
agent runtime, a product platform, or a fourth product.

> **Current positioning:** the only active modules are Workflow-assistance and
> **Hermes · Codex · CC Switch · GitHub · Open Design · OpenHuman · DeepSeek Harness (DSH)**, plus any
> future AI software through the same Adapter contract.
> `30-products/minigame` is retained as product history/fixture/archive
> material, not as a canonical active module. See
> [`00-governance/PROJECT_POSITIONING.md`](00-governance/PROJECT_POSITIONING.md).

## Neutrality (unbound, unlocked)

- **Client-neutral**: one canonical source → per-client native projection, not
  byte-identical copies.
- **Unbound**: the current clients (Hermes · Codex · CC Switch · GitHub · Open Design · OpenHuman ·
  DeepSeek Harness) are the *current* adapters, not permanent dependencies; future AI software plugs
  into the same contract. DSH is a replaceable Agent Runtime (temporary executor in the model
  control-plane taskpack), not a Hermes replacement; see
  [`00-governance/PROJECT_POSITIONING.md`](00-governance/PROJECT_POSITIONING.md).
  dependencies; future AI software plugs into the same contract.
- **Unlocked**: core schemas use stable IDs and capability discovery — never
  hard-coded programs, model IDs, versions, ports, or install paths.

## Workspace mission

WORK-LAB turns a request that spans planning, execution, review and delivery into
an auditable task-pack loop:

```text
request / task pack
  -> ownership + allowed paths + data boundary
  -> one writer with read-only parallel audits
  -> RED -> GREEN -> targeted/module/aggregate gates
  -> exact tree review + recovery evidence
  -> explicit commit/push/release approval
```

The global workflow surface is repository-controlled portable source under
`10-workflow/workflow-assistance`. Hermes Home, credentials, sessions, cron
metadata, provider routes and live caches remain **global platform state**; they
are never absorbed into this repository. Project task data and generated
evidence stay under the current Git root's ignored `.hermes/` boundary.

## Canonical active modules

- `10-workflow/workflow-assistance` — global, client-neutral workflow governance,
  task execution control, observability and portable workflow assets
- `30-observer/work-lab-observer` — strictly read-only derived observation,
  projections and evidence reports

`30-products/minigame` remains outside the active two-module registry as
product history, fixture/reference material and migration/archive evidence. It
does not imply a current platform release, commercial experiment or automatic
merge/deletion decision.

The repository preserves source history and keeps module implementations under
their canonical prefixes. Root governance owns stable contracts, task/evidence
formats, CI, release policy and cross-module ownership; it does not duplicate
module implementations.

## Task-pack responsibility

All substantial work is represented by a reviewed task pack under
`50-taskpacks/`. A task pack must identify the writer, read-only reviewers,
allowed/forbidden roots, input evidence, completion contract, verification
commands, rollback handle and external-mutation approval. Missing evidence,
dirty ownership, boundary violations or incomplete required jobs fail closed.

## Safety boundaries

- One Git root; module rules may narrow root rules but never weaken them.
- `80-evidence/` and `.hermes/` are generated/ignored project data; durable
  handoffs may be retained only when explicitly covered by a recovery contract.
- Secrets, credentials, prompt/response bodies and private browser data never enter evidence.
- Project artifacts never spill outside the project Git root; any spill is
  traceable, locatable, cleanable and migratable (see
  `00-governance/project-data-boundary.json`).
- The `E:` data volume is protected: any access requires explicit per-path,
  per-operation user authorization.
- External mutation, active-path switching and release actions require explicit approval.
- Windows paths are checked case-insensitively before release.

See `00-governance/PROJECT_POSITIONING.md`, `00-governance/projects.json`,
module `AGENTS.md` files, and
`50-taskpacks/TASKPACK_SUMMARY.md` for the current positioning and migration
record.
