# Public Workflow Audit Ticket

## Task
Audit and improve a public/work project using the Hermes ⇄ GPT/DeepSeek ⇄ CC Switch ⇄ Codex workflow.

## Mode
- [ ] plan
- [ ] implement
- [ ] verify
- [ ] review

## Allowed paths
- `src/**`
- `tests/**`
- `docs/**`

## Forbidden paths
- `.env*`
- `auth.json`
- credential stores
- browser cookies
- user private data
- generated large binaries unless explicitly requested

## Required context
- Project README
- Existing test commands
- Relevant AGENTS.md / CODEX.md / SECURITY.md / DESIGN.md
- `python scripts/workflow/hermes_workflow_doctor.py` output if this is a Hermes workflow repo

## Required commands

```bash
git status --short --branch
python scripts/security/scan_agent_rules.py templates skills docs scripts || true
python scripts/workflow/hermes_workflow_doctor.py || true
# project-specific tests here
```

## Output contract

Return:

1. Files changed
2. Verification commands and real output summary
3. Remaining risks/blockers
4. Whether the change is safe to commit/push

## Rollback plan

```bash
git diff --stat
git restore <changed-files>
```
