# Multi-Package Project Structure (Docs + Shared + Apps)

The Star-Trails-Log / Fan Memory OS project established a reproducible directory layout for a full-stack app with shared types, multiple deployable packages, and documentation.

## Directory layout

```
project-root/
├── docs/                              # Long-lived project documentation
│   ├── ARCHITECTURE.md                # System architecture, data flow, module map
│   ├── DATA_MODEL.md                  # Complete data model definitions
│   └── PHASE_PLAN.md                  # Phased development roadmap
├── shared/                            # Cross-package shared code
│   ├── models/index.ts                # TypeScript type definitions
│   └── utils/                         # Pure utility functions
│       ├── id.ts                      # ID generation (no deps)
│       └── platform.ts                # URL platform identification (no deps)
├── packages/
│   ├── app-a/                         # e.g. uni-app frontend
│   │   ├── src/
│   │   │   ├── shared/               # LOCAL copy of shared types (for build isolation)
│   │   │   │   ├── models/index.ts
│   │   │   │   └── utils/
│   │   │   ├── pages/
│   │   │   ├── stores/
│   │   │   └── utils/
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── service-b/                     # e.g. FastAPI backend
│       ├── app/
│       │   ├── routers/
│       │   ├── services/
│       │   └── models.py
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
├── scripts/                           # Ad-hoc utility scripts
│   └── test-core-logic.js             # Cross-cutting tests
├── assets/                            # Project-level shared assets
├── docker-compose.yml                 # Deploy all packages at once
├── .gitignore
└── README.md
```

## Rationale

### `shared/` at root level

- Contains **pure functions and type definitions** with zero external dependencies
- Can be consumed by any package without bundler issues
- The `id.ts` and `platform.ts` utils here were copied into the uni-app project's `src/shared/` because:
  - The `@shared/*` path alias in Vite resolves outside the project root, which `tsc` linting doesn't support
  - **Copy-in pattern**: Keep the canonical version at root `shared/`, mirror into each package's `src/shared/` for build-time isolation

### `packages/` per app/service

Each package is **independently buildable, deployable, and versioned**:
- Has its own `package.json` / `requirements.txt`
- Has its own build tooling (`vite.config.ts`, `Dockerfile`)
- Can be developed and tested in isolation

### `docs/` stays at root

Project-level docs (architecture, data model, roadmap) belong at root, not inside a package, because:
- Multiple packages reference the same architecture
- New developers find them without guessing which package contains them
- They document cross-cutting concerns

### `scripts/` for cross-cutting automation

Scripts that test or operate on multiple packages (e.g. end-to-end tests, code generation) live at root `scripts/`, not inside any package.

## When to use this pattern

Use for any project that has:
- A frontend AND a backend (different tech stacks)
- Cross-package type definitions that must stay in sync
- Multiple independently deployable artifacts
- Long-lived documentation that spans packages

## Concrete example from this project

```text
Star-Trails-Log/
├── docs/
│   ├── ARCHITECTURE.md    → uni-app + FastAPI architecture
│   ├── DATA_MODEL.md      → Person/Content/Team/Source/Reminder
│   └── PHASE_PLAN.md      → 3-phase development plan
├── shared/models/index.ts → TypeScript interfaces for ALL models
├── packages/
│   ├── fan-memory-app/    → uni-app Vue 3 (16 pages, 4 stores)
│   │   └── src/shared/    → local copy of shared models
│   └── discovery-service/ → FastAPI backend (SQLite, 14 APIs)
│       └── tests/         → 12 API tests
├── scripts/test-core-logic.js  → 38 cross-cutting tests
└── docker-compose.yml          → one-command deploy
```
