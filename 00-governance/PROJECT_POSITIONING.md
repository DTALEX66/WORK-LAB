# WORK-LAB canonical project positioning

**Position:** client-neutral workflow control plane for the user's whole AI
workflow — it owns the highest user-level capability layer (global
configuration), not any single client's runtime and not any project's domain
logic.

**Repository:** `DTALEX66/WORK-LAB`

## What this repository is

WORK-LAB manages the user's **global configuration layer** — Rules, Skills,
plugin/MCP declarations, portable Memory, Capabilities and workflow policy —
as one client-neutral canonical source, then adapts it into native projections
for each current client. It stays neutral and unbound: no software platform,
agent platform, model, provider, version, port or install path is a hard
dependency of the core contract.

## Neutrality contract (unbound, unlocked)

- **Client-neutral**: one canonical source → per-client native projection;
  never six byte-identical copies.
- **Unbound**: Hermes, Codex, CC Switch, GitHub, Open Design and OpenHuman are
  the *current* adapters, not permanent dependencies; future AI software plugs
  into the same Adapter contract.
- **Unlocked**: core schemas use stable IDs, capability discovery and Adapter
  contracts — never hard-coded programs, model IDs, versions, ports or paths.
- **Global configuration scope**: the current workflow software plus any future
  AI software; managed as desired state, applied only through an approved
  Adapter transaction (`UNSUPPORTED_APPLY` when no safe official write
  interface exists).

## Current client workflow

The current managed clients are:

```text
Hermes · Codex · CC Switch · GitHub · Open Design · OpenHuman
```

Open Design is an external **client** (`nexu-io/open-design`, adapter id
`open-design`); `DTALEX66/DESIGN-LAB` is a separate, independent **project**.
These are two distinct identity axes and must never be merged.
`DTALEX66/OPEN-DESIGN-Assistance` is retained only as DESIGN-LAB's historical
migration alias.

## Canonical active modules

1. `10-workflow/workflow-assistance` — client-neutral workflow governance,
   execution control, portable contracts and delivery boundaries.
2. `30-observer/work-lab-observer` — strictly read-only derived observation,
   projections and evidence reports.

`30-products/minigame` is product history/fixture/archive material, not an
active canonical module.

## Data containment and spill governance

- Project task data, caches, logs and artifacts stay inside the project Git
  root (ignored `.hermes/` boundary) — never the user home, desktop, system
  temp or another project.
- The `E:` data volume is protected: any access requires explicit per-path,
  per-operation user authorization.
- Any spill (a write outside the project boundary) is traceable, locatable,
  cleanable and migratable. See `00-governance/project-data-boundary.json`.

## Explicit non-positioning

WORK-LAB is **not**:

- Hermes, Codex, CC Switch or another agent runtime;
- a model/provider gateway, credential store, chat UI or prompt/response
  archive;
- a platform deployment service, commercial marketplace or release host;
- an active MINIGAME product repository;
- a second database product or multi-user SaaS;
- permission to apply any client's live configuration, modify external
  systems, or publish releases.

## Authoritative source files

- `00-governance/projects.json` — canonical module registry;
- `00-governance/module-ownership.json` — ownership and writer boundary;
- `00-governance/project-data-boundary.json` — data containment + spill governance;
- `00-governance/contracts/contract-catalog.json` — canonical contract catalog;
- `10-workflow/workflow-assistance/config/config-ownership.json` — field-level ownership;
- `10-workflow/workflow-assistance/config/adapter-registry.json` — client adapter inventory;
- `50-taskpacks/TASKPACK_SUMMARY.md` — current task-pack summary;
- `README.md` — public repository entrypoint.

If another README, historical handoff or external description conflicts with
this file and the machine-readable registries, classify it as stale
documentation and update it; do not infer a second architecture.
