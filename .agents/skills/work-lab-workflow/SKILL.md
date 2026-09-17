<!-- GENERATED — DO NOT EDIT -->
<!-- source: projections/agents/source/work-lab-workflow/SKILL.md -->
<!-- generator: projections/agents/generate.py v1.0.0 -->
<!-- content_hash: sha256:6b3e785cb184cba5212a7ee69e5ac3d65753bdf3214a171fe0e3610a796be9bb -->
---
name: work-lab-workflow
description: "Use for WORK-LAB workflow tasks; follow the project ledger, module, and verification boundaries."
version: 1.0.0
---

# WORK-LAB Workflow Contract

Use this skill only inside the WORK-LAB Git repository.

## Ownership

- `services/` + `packages/` + `integrations/` owns workflow configuration, Task Ledger, Telemetry Ledger, sidecar, adapters, and delivery gates.
- `apps/observer` is read-only. It may read Workflow-owned projections but must not execute, approve, retry, apply, rollback, change task state, or write the Telemetry Ledger.
- Open Design and MINIGAME are archive/transferred scope and must not be restored as active modules.

## Writer boundary

- One writer owns a checkout.
- Parallel writers require separate worktrees.
- Do not edit a checkout concurrently with another writer or reviewer.
- Do not commit, push, publish, create a PR, merge, or modify global Codex/Hermes configuration unless the user explicitly authorizes that exact side effect.

## Runtime and evidence

- Keep temporary files, caches, logs, test environments, Task Ledger state, and generated evidence under the project `.project-local/` directory.
- Never read or expose credentials, `.env` files, auth stores, private keys, browser data, tokens, prompt bodies, or response bodies.
- Never access `E:\` without explicit authorization for the exact path and operation.

## Verification

Run checks from the exact module path. Prefer the canonical gate:

```text
python services/orchestration/run_quality_gate.py verify
```

Distinguish structural checks, local runtime checks, exact-SHA CI, and release evidence. A local test pass is not proof of exact-SHA CI or publication.

## Task execution

Before changing code, read the relevant `AGENTS.md`, inspect the project task contract, and locate the symbol or configuration owner. Use the Workflow-owned Task Ledger for durable task state when the task contract requires it. Observer projections are read-only and are never a second source of truth.
