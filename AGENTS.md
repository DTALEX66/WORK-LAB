# WORK-LAB execution rules

## Scope

This is a single-root monorepo. Allowed active module roots are exactly:
`10-workflow/workflow-assistance` and `30-observer/work-lab-observer`. The
Open Design module and the MiniGame product tree were transferred to
`DTALEX66/OPEN-DESIGN-Assistance` on the authorized migration branch; neither
`20-design/open-design` nor `30-products/minigame` remains here. Only the
handoff pointer and Git history remain for the transferred scope.

## Ownership

One writer owns a task. Read-only reviewers may inspect exact trees but may not
edit them. Cross-module changes require one explicit cross-module task card.
Module instructions can narrow these rules, never weaken them.

## Safety

Do not read, print, copy, commit, or upload credentials, `.env` files, auth
stores, private keys, browser data, tokens, prompt bodies, or response bodies.
Do not access `E:\`. Never use destructive reset/clean/force-push operations.
Generated evidence belongs under ignored `80-evidence/` or `.hermes/task-runtime/`.

## Verification

Run checks from the exact module path. Report structural checks separately from
live execution checks. Any failed, cancelled, missing, or skipped required job
fails the aggregate gate.
