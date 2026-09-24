# WORK-LAB

`DTALEX66/WORK-LAB` is the canonical monorepo control plane for the user's
**client-neutral AI workflow global-configuration layer**. It manages the
highest user-level capability layer — Rules, Skills, plugins/MCP declarations,
portable Memory, Capabilities and workflow policy — as one canonical source,
then adapts it into native projections for each current client. It is not an
agent runtime, a product platform, or a fourth product.

> **Current positioning (V2 converged):** the active module roots are
> `packages/client-neutral-core` (task/telemetry ledger, sidecar, adapters,
> delivery gates), `services/` (orchestration, policy, receipts) and
> `apps/observer` (strictly read-only projection). Managed clients:
> **Hermes · Codex · DSH · GitHub · Open Design · OpenHuman**, plus any future
> AI software through the same Adapter contract; CC Switch is LEGACY_OBSERVE
> (observe-only, no active writes). Frozen history lives under `docs/history/`
> (single retrieval anchor; see `WL_INHERITANCE_MATRIX.json`, MiniGame =
> `FOREIGN_HISTORICAL`). See
> [`docs/decisions/PROJECT_POSITIONING.md`](docs/decisions/PROJECT_POSITIONING.md).

## Neutrality (unbound, unlocked)

- **Client-neutral**: one canonical source → per-client native projection, not
  byte-identical copies.
- **Unbound**: the current clients (Hermes · Codex · DSH · GitHub · Open Design ·
  OpenHuman; CC Switch is LEGACY_OBSERVE, observe-only) are the *current*
  adapters, not permanent dependencies; future AI software plugs into the same
  contract. DSH is a replaceable agent runtime (temporary executor in the model
  control-plane taskpack), not a Hermes replacement; see
  [`docs/decisions/PROJECT_POSITIONING.md`](docs/decisions/PROJECT_POSITIONING.md).
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
`packages/client-neutral-core`. Hermes Home, credentials, sessions, cron
metadata, provider routes and live caches remain **global platform state**; they
are never absorbed into this repository. Project task data and generated
evidence stay under the current Git root's ignored `.project-local/` boundary.

## Canonical active modules

- `packages/client-neutral-core` — global, client-neutral workflow governance,
  task/telemetry ledgers, sidecar, adapters and delivery gates
- `services/` — orchestration, policy, execution-federation, receipts,
  session-federation, task-governance, radar, security and cleanup
- `apps/observer` — strictly read-only derived observation,
  projections and evidence reports

Frozen history lives under `docs/history/` (single retrieval anchor, incl.
converged report history from `90-archive/` via MOVE-005; `90-archive/`
retains only its `BOUNDARY.md` gate marker). MiniGame and pre-cutover
r4-era material remain archive evidence, not active modules.

The repository preserves source history and keeps module implementations under
their canonical prefixes. Root governance owns stable contracts, task/evidence
formats, CI, release policy and cross-module ownership; it does not duplicate
module implementations.

## Task-pack responsibility

All substantial work is represented by a reviewed task pack under
`taskpacks/current/`. A task pack must identify the writer, read-only reviewers,
allowed/forbidden roots, input evidence, completion contract, verification
commands, rollback handle and external-mutation approval. Missing evidence,
dirty ownership, boundary violations or incomplete required jobs fail closed.

## Safety boundaries

- One Git root; module rules may narrow root rules but never weaken them.
- `.project-local/` holds ignored runtime + evidence data; frozen history
  lives under `docs/history/` (single retrieval anchor — `90-archive/`
  converged into it, retaining only its `BOUNDARY.md` gate marker).
  Durable handoffs may be retained only when explicitly
  covered by a recovery contract.
- Secrets, credentials, prompt/response bodies and private browser data never enter evidence.
- Project artifacts never spill outside the project Git root; any spill is
  traceable, locatable, cleanable and migratable (see
  `.project/governance/project-data-boundary.json`).
- The `E:` and `F:` data volumes are protected: any access requires explicit per-path,
  per-operation user authorization.
- External mutation, active-path switching and release actions require explicit approval.
- Windows paths are checked case-insensitively before release.

See `docs/decisions/PROJECT_POSITIONING.md`, `.project/governance/projects.json`,
module `AGENTS.md` files, and
`taskpacks/current/WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918.md` for the
current positioning and migration record.
