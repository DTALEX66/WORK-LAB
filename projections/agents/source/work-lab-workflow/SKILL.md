---
name: work-lab-workflow
description: "Use for WORK-LAB workflow tasks; follow the project ledger, module, and verification boundaries."
version: 1.1.0
---

# WORK-LAB Workflow Contract

Use this skill only inside the WORK-LAB Git repository.

## What this product is

WORK-LAB is a client-neutral workflow control, governance, task, delivery and observability layer. It is not
an agent, not a chat application, and not a model gateway; external software executes the business work. The
repository is an auditable portable source, and Hermes, Codex, CC Switch, GitHub, OpenHuman and Open Design
are replaceable Adapters behind one contract, not the product itself.

## Three projects, one boundary each

- WORK-LAB: project observation, reusable capability evaluation / adaptation / target verification, and
  declared configuration governance. It is not a mandatory total dispatcher.
- ArcheAxis-Knowledge-OS (AAOS): full knowledge lifecycle, human knowledge work, research and learning, AI
  learning assets, bidirectional learning and long-term project memory.
- DESIGN-LAB: professional design of all types, native assets, the design-specific execution core and
  professional acceptance.

Machine authority: `.project/governance/three-project-boundary.json`. A task in one project grants no write
access to another. Design capability is neither collected nor managed here.

## Ownership

- Module roots are exactly two (`.project/governance/module-ownership.json`): `packages/client-neutral-core`
  (Task Ledger, Telemetry Ledger, sidecar, adapters, delivery gates) and `apps/observer` (read-only
  projection). `services/`, `integrations/`, `config/`, `apps/token-monitor/` and `scripts/` are active
  supporting surfaces, not module roots.
- `apps/observer` is read-only. It may read Workflow-owned projections but must not execute, approve, retry,
  apply, rollback, change task state, or write the Telemetry Ledger.
- Retired module paths must not be restored.

## Desktop scope

The product surface is the desktop Observer window plus the existing desktop floating HUD. Mobile is out of
scope: it is not built, not queued, and not recorded as a deferred or frozen task.

## Truth discipline

- Unknown is never padded to zero, and an absent field is not an empty one; report PROJECTED, NULL_FIELD and
  SOURCE_GAP as different origins.
- A lost connection is not a stopped subject, and a `turn_end` signal is not the completion of a project.
- Demo and fixture data never enter production code paths.
- A colour or layout proposal from an inbound task pack becomes an opt-in theme
  (`?palette=master`) and never overwrites the shipped default values.

## Writer boundary

- One writer owns a checkout; parallel writers require separate worktrees.
- Do not edit a checkout concurrently with another writer or reviewer.
- Do not commit, push, publish, create a PR, merge, install software, or modify global client configuration
  unless the user explicitly authorizes that exact side effect.
- Whether an external client is actually deployed is recorded as unverified unless it was read back in this
  session; an unverified claim is written as unverified, not as satisfied.

## Runtime and evidence

- Keep temporary files, caches, logs, test environments, Task Ledger state and generated evidence under the
  project `.project-local/` directory (`runs/` for transient state, `artifacts/` for evidence).
- Never read, print, copy, commit or upload credentials, `.env` files, auth stores, private keys, browser
  data, tokens, prompt bodies or response bodies.
- Never access `E:\` or `F:\` — read or write — without explicit per-path, per-operation authorization
  (`.project/governance/project-data-boundary.json`).

## Verification

Run checks from the exact module path. Prefer the canonical gate:

```text
python services/orchestration/run_quality_gate.py verify
```

Distinguish structural checks, local runtime checks, exact-SHA CI, and release evidence. A local test pass is
not proof of exact-SHA CI or publication. A render or measurement receipt must name the bytes it looked at.

## Task execution

Before changing code, read the relevant `AGENTS.md`, inspect the project task contract, and locate the symbol
or configuration owner. The single live task register is `taskpacks/current/OPEN-TASK-REGISTER.md`, and the
current taskpack for this round is `taskpacks/current/WORK-LAB-UI-PRIORITY-TASKPACK-20261009.md`. Use the
Workflow-owned Task Ledger for durable task state when the task contract requires it. Observer projections
are read-only and are never a second source of truth.

## Scoped references

Read repository-relative `docs/current/workflow-assistance/skill-references/observer.md` only for Observer
delivery, or `docs/current/workflow-assistance/skill-references/external-clients.md` for Open Design /
OpenHuman boundary work. Generic debugging or testing advice is not a separate required workflow.
