# WORK-LAB Stage 2 Absorption and Interoperability - Queued Handoff

> STATUS: `QUEUED_WAITING_FOR_PREDECESSOR_EVIDENCE`
>
> This file registers the successor task pack only. It does not start Stage 2
> implementation and does not replace or rerun WORK-LAB-FINAL-CONSOLIDATED
> WL-000 through WL-820.

## Task pack identity

```yaml
taskpack_id: WORK-LAB-STAGE-2-ABSORPTION-INTEROP
snapshot_date: 2026-08-07
predecessor_taskpack: WORK-LAB-FINAL-CONSOLIDATED
repository: DTALEX66/WORK-LAB
preferred_local_root: 'D:\\All projects\\WORK-LAB'
observed_remote_head: 471e90a99b4234e4f5c031c4280c2eba8b065439
execution_mode: CONTINUOUS_LOCAL_SAFE_AFTER_GATE
writer_policy: SINGLE_WRITER
observer_policy: STRICTLY_READ_ONLY
publication_policy: EXPLICIT_APPROVAL
live_global_apply_policy: EXPLICIT_APPROVAL
paid_provider_policy: EXPLICIT_APPROVAL
destructive_policy: FORBIDDEN_WITHOUT_EXPLICIT_APPROVAL
source_attachment: .hermes/desktop-attachments/WORK-LAB-STAGE-2-ABSORPTION-INTEROPERABILITY-HERMES-TASKPACK.md
```

The attachment is the authoritative source. This tracked file is the
repository-local successor handoff and is not a substitute for the attachment.
The attachment's observed_remote_head is comparison evidence only; never reset,
overwrite, delete, or abandon local work to match it.

## Start gate

Stage 2 remains queued until all Gate A conditions are satisfied:

- predecessor Task Ledger, current tree digest, worktree status, and active
  writer lease have been reconciled;
- predecessor WL-000 through WL-820 has a machine-readable state export that
  distinguishes complete, partial, not-started, blocked, and deferred;
- CURRENT_STATE, the three module contracts, Adapter Registry, event schemas,
  and Observer read-only state are readable;
- predecessor P0 ownership is explicit for security, single-writer,
  Task Ledger, CI watcher, event contracts, and Observer read-only boundaries;
- no second writer, second worktree, or parallel task modifies this checkout;
- NX-000 confirms one owner, task ID, and write path for every overlap.

If Gate A is not satisfied, only an `NX-000-PREDECESSOR-GAP-REPORT` may be
created. No Stage 2 implementation write may begin. At registration time the
predecessor worktree is dirty, so Stage 2 stays in the waiting state.

## Ordered successor tasks

| Order | ID | Batch / priority | Goal | Dependency | State |
|---:|---|---|---|---|---|
| 1 | NX-000 | NX-0 / P0 | predecessor coverage, inheritance matrix, overlap dedupe | Gate A | QUEUED_WAITING_FOR_PREDECESSOR_EVIDENCE |
| 2 | NX-100 | NX-1 / P0 | cross-module Source Ledger V3 and honest implementation states | NX-000 | QUEUED |
| 3 | NX-110 | NX-1 / P0 | license, security, install, telemetry, credential and size audit | NX-000 | QUEUED |
| 4 | NX-200 | NX-2 / P0 | ACP protocol/capability mapping and read-only observe bridge | NX-100, NX-110 | QUEUED |
| 5 | NX-210 | NX-2 / P0 | Agent Skills structure, namespace and MCP conformance/malicious fixtures | NX-100, NX-110 | QUEUED |
| 6 | NX-300 | NX-3 / P0 | OpenTelemetry/OpenInference mapping without message bodies | event/Observer contracts, NX-100, NX-110 | QUEUED |
| 7 | NX-310 | NX-3 / P1 | multi-agent usage adapters, read-only incremental ingestion and coverage | NX-300 | QUEUED |
| 8 | NX-320 | NX-3 / P1 | cost, retention, rollup, freshness and quality semantics | NX-310 | QUEUED |
| 9 | NX-400 | NX-4 / P1 | memory pollution, cross-project leakage, stale facts and malicious-skill negatives | predecessor WL-400/410/420 | QUEUED |
| 10 | NX-410 | NX-4 / P1 | Task Ledger replay, crash, old-writer and side-effect idempotency fixtures | predecessor WL-200/Task Ledger | QUEUED |
| 11 | NX-500 | NX-5 / P1 | DTCG, DESIGN.md and Open Design input/output round-trip contracts | predecessor WL-500/600, NX-100/110 | QUEUED |
| 12 | NX-510 | NX-5 / P1 | minimal production evidence for Playwright/axe, SVGO, PPTX and charts | NX-500 | QUEUED |
| 13 | NX-520 | NX-5 / P1 | WCAG/ARIA/CJK/print/exhibition standards linked to evidence cards | NX-500 | QUEUED |
| 14 | NX-600 | NX-6 / P1 | OSV/Scorecard/SPDX/REUSE source health and upstream-change monitoring | NX-100, NX-110 | QUEUED |
| 15 | NX-700 | NX-7 / P0/P1 | three offline pilots: Workflow, Observer, Open Design | selected scope complete | QUEUED |
| 16 | NX-710 | NX-7 / P1 | dependency/source/asset size, performance and boundary regression | NX-700 | QUEUED |
| 17 | NX-720 | NX-7 / P0 | exact-tree review, evidence, license and rollback approval package | NX-710 | QUEUED |

## Scope and exclusions

- The only active canonical modules remain:
  - `10-workflow/workflow-assistance`
  - `20-design/open-design`
  - `30-observer/work-lab-observer`
- `30-products/minigame` remains historical/fixture/archive material and is
  not a fourth active module. MINIGAME UI may only be an Open Design fixture.
- Do not add an Agent, chat UI, model gateway, LLMOps platform, task platform,
  database platform, second task runtime, second memory service, second
  Observer UI, or fourth product.
- Do not auto-install unknown Skills/MCP/clients. Do not read credentials,
  auth stores, prompts/responses, full session bodies, OAuth tokens,
  Credential Manager, or private quota endpoints.
- Do not default-install collectors, Langfuse, Phoenix, OpenLIT, LiteLLM Proxy,
  Mem0/Graphiti/Temporal/Trigger.dev/Dagu services. Absorb only audited
  methods, contracts and fixtures.
- Do not vendor complete upstream repositories or commit node_modules, caches,
  downloaded binaries, or code with unknown licensing.
- Commit, push, PR, merge, release, Hermes live/global apply, paid-provider
  smoke, real OS profile writes, destructive archive work, and human aesthetic
  calibration remain separately approval-gated.

## Completion definition

Stage 2 may stop only at:

```text
LOCAL_VERIFIED_READY_FOR_USER_APPROVAL
```

Only real implementations, fixtures, negative controls, readback and source/
license evidence qualify. Links, README entries, directories, registry rows,
download counts, or research notes do not prove adapter, conformance, privacy,
round-trip, production-output, rollback, or human-calibration completion.

## Next action

After the predecessor reaches a stable handoff, the only first action is NX-000:
read the predecessor Task Ledger and current tree, generate the inheritance/
partial/blocked/deferred matrix, and confirm that Stage 2 does not duplicate
predecessor work. Before NX-000, do not modify Stage 2 implementation files,
create a second writer, or perform external platform writes.
