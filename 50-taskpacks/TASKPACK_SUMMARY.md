# Task-pack summary

WORK-LAB is the global project-workflow control plane plus three delivery
modules. The root task-pack system owns task scope, writer/reviewer boundaries,
evidence contracts, recovery and cross-module integration; it does not own a
fourth product implementation.

Completed migration baseline:

- DISC evidence and boundary decisions recorded locally.
- MIG-001..MIG-008: recoverable bundles, dirty-state preservation, candidate,
  non-squash prefixed history imports, collision ledger and machine map.
- GOV-001..GOV-008: root layout, instruction precedence, compatibility locks,
  stable contracts, aggregate CI gate, release policy, asset routing and
  privacy-safe evidence contracts.

Evidence generated under the ignored local `.hermes/task-artifacts` path is not
published as source content. The committed handoff records reproducible source
tips, module paths, recovery locations and remaining approval gates. Hermes
global config, auth, sessions, cron, skills, plugins and caches remain platform
state and are never absorbed by a task pack.
