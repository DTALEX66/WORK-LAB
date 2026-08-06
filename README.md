# WORK-LAB

`DTALEX66/WORK-LAB` is the canonical v2 monorepo control plane for the user's
**client-neutral AI project workflow**. It is not an agent runtime, product
platform or fourth product. The root controls task packs, governance, evidence,
ownership, data boundaries, recovery and cross-module delivery; module roots
contain the actual implementations.

> **Current positioning:** the only active v2 modules are Workflow-assistance,
> Open Design and the strictly read-only WORK-LAB Observer. `30-products/minigame`
> is retained as product history/fixture/archive material, not as a canonical
> active module. See [`00-governance/PROJECT_POSITIONING.md`](00-governance/PROJECT_POSITIONING.md).

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

## Canonical v2 modules

- `10-workflow/workflow-assistance` — global, client-neutral workflow governance,
  task execution control, observability and portable workflow assets
- `20-design/open-design` — design knowledge, visual quality and production handoff
- `30-observer/work-lab-observer` — strictly read-only derived observation,
  projections and evidence reports

`30-products/minigame` remains outside the active three-module registry as
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
- External mutation, active-path switching and release actions require explicit approval.
- Windows paths are checked case-insensitively before release.

See `00-governance/PROJECT_POSITIONING.md`, `00-governance/projects.json`,
module `AGENTS.md` files, and
`50-taskpacks/WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md` for the current
positioning and migration record.
