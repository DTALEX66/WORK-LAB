# Workflow-assistance repository rules

This repository is the portable source of truth for the global Hermes, CC
Switch, Codex, and GitHub workflow. Changes must improve a reusable workflow,
not rely on one desktop session or one agent implementation.

## Scope and safety

- Work only inside this repository unless the user explicitly authorizes an
  exact external path and operation.
- Do not read, print, copy, or commit credentials, `.env` files, auth stores,
  private keys, browser data, or tokens.
- Treat `E:\` as protected user data. Do not access it without explicit,
  per-operation user approval.
- Do not modify Hermes Home, Codex Home, CC Switch, or GitHub settings unless
  the user explicitly asks to apply a reviewed deployment.
- Do not run destructive Git commands, delete user data, or overwrite an
  existing project instruction file without explicit approval.

## Change and verification rules

- Read the affected source and tests before editing; keep changes small.
- Before editing, run `git status --short`; after editing, report
  `git diff --stat` and `git status --short`.
- Add or update tests whenever behavior changes. Run the narrowest relevant
  test first, then the project quality gate when the change touches deployment,
  safety, configuration, or portability.
- Project-scoped runtime data belongs in ignored `.hermes/`; do not write task
  caches, logs, or generated artifacts to a user profile or another project.
- Clearly distinguish structural checks from live execution checks. Never
  claim a component is globally active unless its installed location and
  runtime behavior were both verified.
