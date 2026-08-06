# Task-pack summary

WORK-LAB is the global project-workflow control plane plus three delivery
modules. The root task-pack system owns task scope, writer/reviewer boundaries,
evidence contracts, recovery and cross-module integration; it does not own a
fourth product implementation.

Historical migration/governance snapshot (not the current attachment task-pack
completion state):

- `HIST-MIG-001..HIST-MIG-008`: historical migration evidence, recoverable
  bundles, dirty-state preservation, candidate and collision records.
- `HIST-GOV-001..HIST-GOV-008`: historical governance evidence for root layout,
  instruction precedence, contracts, CI and privacy-safe evidence.
- The old `MIG-*` and `GOV-*` names are deliberately namespaced as `HIST-*` in
  this active summary because the attached task-pack reuses some IDs with
  different acceptance criteria.

Final active task-pack baseline:

- Source: `WORK-LAB-HERMES-TASKPACK-v1.0.0.zip`.
- Canonical reconciliation: `WORK-LAB-HERMES-TASKPACK-RECONCILIATION.md` and
  `.json` in this directory.
- Full current per-ID evidence remains under the ignored
  `.hermes/task-artifacts/taskpack-assessment-20260806.json`.
- The attachment is the final priority source; compatible historical work is
  retained, divergent historical work cannot override it, and unresolved
  destructive/live/Git actions remain separately approval-gated.

Evidence generated under the ignored local `.hermes/task-artifacts` path is not
published as source content. The committed handoff records reproducible source
tips, module paths, recovery locations and remaining approval gates. Hermes
global config, auth, sessions, cron, skills, plugins and caches remain platform
state and are never absorbed by a task pack.
