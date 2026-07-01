# AGENTS.md — Portable Agent Rules

## Mission

Work from evidence, keep changes surgical, verify with real commands, and leave the repository in a clean, resumable state.

## Operating Loop

1. Read project orientation docs first (`README.md`, `docs/*`, `AGENTS.md`, `CODEX.md`, `SECURITY.md`, `DESIGN.md` if present).
2. Inspect current state (`git status`, relevant files, tests/build config).
3. Choose one real, evidenced gap.
4. Implement the smallest coherent fix.
5. Run the project’s verification command.
6. Summarize changed files, verification result, and remaining risk.

## Boundaries

- Do not read or print secrets: `.env`, `auth.json`, `*.pem`, SSH keys, browser cookies, credential stores.
- Do not delete or move user data unless explicitly instructed.
- Do not run destructive git commands (`reset --hard`, `clean -fd`) without explicit user approval.
- Keep generated artifacts out of git unless they are intentional deliverables.

## Quality Bar

A task is not done until the requested artifact exists and has been exercised by a real command or inspection.
