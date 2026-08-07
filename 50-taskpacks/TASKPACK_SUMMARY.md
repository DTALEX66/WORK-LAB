# Task-pack summary

WORK-LAB is the global project-workflow control plane plus two canonical
active modules. The root task-pack system owns task scope, writer/reviewer
boundaries, evidence contracts, recovery and cross-module integration; it does
not own a fourth product implementation.

The active module registry is authoritative:

- `10-workflow/workflow-assistance` — client-neutral workflow governance;
- `30-observer/work-lab-observer` — strictly read-only observation and evidence.

Open Design was transferred to `DTALEX66/OPEN-DESIGN-Assistance`; the one-time
pointer and migration evidence are retained under `90-archive-manifests/` and
ignored `.hermes/` artifacts.

`30-products/minigame` is product history/fixture/archive material, not an
active v2 canonical module. See `00-governance/PROJECT_POSITIONING.md`.

Historical migration/governance snapshot (not the current attachment task-pack
completion state):

- `HIST-MIG-001..HIST-MIG-008`: historical migration evidence, recoverable
  bundles, dirty-state preservation, candidate and collision records.
- `HIST-GOV-001..HIST-GOV-008`: historical governance evidence for root layout,
  instruction precedence, contracts, CI and privacy-safe evidence.
- The old `MIG-*` and `GOV-*` names are deliberately namespaced as `HIST-*` in
  this active summary because the attached task-pack reuses some IDs with
  different acceptance criteria.

Current active task-pack baseline:

- Source: `WORK-LAB-HERMES-TASKPACK-v2.0.0.zip`.
- Canonical reconciliation: `WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md` and
  `.json` in this directory.
- Full current per-ID evidence remains under the ignored
  `.hermes/task-artifacts/taskpack-assessment-20260806.json`.
- The v2 attachment is the final priority source; compatible historical work is
  retained, divergent historical work cannot override it, and unresolved
  destructive/live/Git actions remain separately approval-gated.

Evidence generated under the ignored local `.hermes/task-artifacts` path is not
published as source content. The committed handoff records reproducible source
tips, module paths, recovery locations and remaining approval gates. Hermes
Hermes global config, auth, sessions, cron, skills, plugins and caches remain platform
state and are never absorbed by a task pack.

## Current local predecessor slice

`WL-300` is locally implemented as an offline model/context/cost policy
contract. It uses capability classes instead of permanent model or provider
IDs, enforces context overflow fail-closed behavior, keeps unknown cost as
`UNKNOWN_COST` rather than inventing a zero value, and allowlists numeric usage
fields while excluding prompt/response bodies and credentials.

- Contract: `10-workflow/workflow-assistance/schemas/workflow/model-policy.schema.json`.
- Evaluator: `10-workflow/workflow-assistance/scripts/workflow/model_policy.py`.
- Tests: `10-workflow/workflow-assistance/tests/test_model_policy.py`.
- Local evidence: `.hermes/task-artifacts/wl300-model-policy.json` (ignored).
- Scope: local and fixture-only; no live provider, credential, prompt body,
  Hermes live apply, commit, push, PR, merge, release, or paid-provider smoke.

`WL-400` now adds memory-layer metadata, explicit candidate quarantine, manual
promotion boundaries, and report-only rule-drift projection. Memory and rule
content bodies are not stored; only digests, layer/state metadata, and redaction
flags are retained. Evidence is `.hermes/task-artifacts/wl400-growth-watch.json`
and remains ignored.

`WL-500` now projects normalized Token Monitor usage summaries through the
strictly read-only Observer event store. The adapter accepts only explicit
non-negative usage integers, excludes model IDs and raw log/prompt/response
content, and exposes aggregate input/output/total/record counts in the
rebuildable Observer projection. Evidence is
`.hermes/task-artifacts/wl500-observer-usage.json`; no live log was read and no
external or authoritative state was mutated.

`WL-600` now tracks one non-authoritative evidence card per visual benchmark.
All 12 cards remain `not-run`/E0 and bind only local brief, rubric, and report
schema fixtures. The evidence-card verifier rejects accepted cards without
completed human calibration and passing hard gates; the Open Design aggregate
verifier runs this check as a secondary gate. No visual score or human review
was fabricated.

`WL-720` completed a non-destructive local size/duplicate audit across the
three canonical scopes, the preserved MiniGame fixture, and archive manifests.
The proposal recorded five scopes and 23 duplicate content groups; every group
is manual-review-only, and the archive proposal retains both the fixture source
and its manifest. Evidence is `.hermes/task-artifacts/wl720-audit-proposal.json`.

## Queued successor: Stage 2 absorption and interoperability

The successor attachment
`.hermes/desktop-attachments/WORK-LAB-STAGE-2-ABSORPTION-INTEROPERABILITY-HERMES-TASKPACK.md`
is registered as:

```text
WORK-LAB-STAGE-2-ABSORPTION-INTEROP
status=QUEUED_WAITING_FOR_PREDECESSOR_EVIDENCE
predecessor=WORK-LAB-FINAL-CONSOLIDATED
first_task=NX-000
```

The tracked registration and handoff is
`50-taskpacks/WORK-LAB-STAGE-2-ABSORPTION-INTEROPERABILITY-HANDOFF.md`.
It preserves the attachment's single-writer, strictly read-only Observer,
explicit publication/live/paid-provider approval and forbidden-destructive
defaults. Stage 2 must not start implementation until predecessor Gate A and
NX-000 produce an inheritance/overlap matrix.

The queued order is:

```text
NX-000 → NX-100/NX-110 → NX-200/NX-210 → NX-300/NX-310/NX-320
→ NX-400/NX-410 → NX-500/NX-510/NX-520 → NX-600
→ NX-700/NX-710/NX-720
```

The Stage 2 queue does not add a fourth active module, a second Observer UI,
another Task Ledger/runtime, a memory service, an Agent/chat product, or a
default cloud/paid provider. Current local predecessor work remains separate
from this queued successor and must not be treated as published or cloud-CI
verified until independently delivered and read back.
