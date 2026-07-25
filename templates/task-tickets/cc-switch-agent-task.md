# CC Switch / Coding Agent Task Ticket

## Task Name

<short task name>

## Mode

- [ ] plan
- [ ] implement
- [ ] verify
- [ ] review

## Allowed Paths

```text
<project-relative paths>
```

## Forbidden Paths

```text
.env
auth.json
.git/
node_modules/
.venv/
user data folders
```

## Source Docs to Read First

```text
README.md
AGENTS.md
SECURITY.md
DESIGN.md
<project-specific docs>
```

## Requirements

1. <requirement>
2. <requirement>
3. <requirement>

## Verification Commands

```bash
<exact commands>
```

## Execution / Review Boundary

- Writer: `<Hermes / Codex / other>`; exactly one writer owns the checkout.
- Review backend: `<Hermes / Codex native review>`; review the exact frozen tree `<git write-tree>`.
- Codex review, when selected: use generic `codex exec --sandbox read-only --ephemeral` with an
  exact-tree prompt and a temporary JSON output schema; no sandbox or approval bypass is permitted.
  Any finding is fail-closed as NO-GO.
- Route evidence: record only listener/transport status; do not copy proxy URLs, subscriptions,
  OAuth files, tokens or route databases.

## Output Contract

Return:

- files changed
- verification output
- risks
- rollback notes
- next recommended task
