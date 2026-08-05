# WORK-LAB

`DTALEX66/WORK-LAB` is the canonical workspace for the user's **global project
workflow task system** and its three independently owned delivery modules. It is
not a fourth product. The root is the control plane for task packs, governance,
evidence, ownership, data boundaries and recoverable cross-module delivery;
module roots contain the actual product/knowledge implementations.

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

## Delivery modules

- `10-workflow/workflow-assistance` — global, client-neutral workflow governance,
  task execution control, observability and portable workflow assets
- `20-design/open-design` — design knowledge, visual quality and production handoff
- `30-products/minigame` — independent game product and revenue proof

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

See `00-governance/`, module `AGENTS.md` files, and `MIGRATION_LEDGER.json` for the current migration record.
