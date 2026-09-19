# U17 Closeout — Global Agent Policy SSOT + Native Projection + Protected-Drive Enforcement

- Date: 2026-09-19
- Branch: `u17/global-agent-policy-20260918`
- PR: #127 (OPEN, MERGEABLE, base main) — https://github.com/DTALEX66/WORK-LAB/pull/127
- Taskpack: `WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918` (section U17), authority taskpack v2 (2026-09-18)
- Status: **IMPLEMENTED + VERIFIED on branch; merge is a user decision (grant: create_pr=true, merge_main=false)**

## Commits (main..HEAD)

| SHA | Scope |
|---|---|
| `3aecfc6` P0 | `config/global-agent-policy.yaml` SSOT (19 capabilities) + schema + config-ownership / adapter-registry projection + A03 authority verifier |
| `0272d61` P1 | Fail-closed projection contract (`services/policy/policy_projection.py`) + Codex/Hermes renderers + regenerated goldens + loss reports + tests |
| `bc5685f` P2 | `capability-matrix.json` `global_agent_policy_coverage` block + registry 19-cap alignment + `verify_policy_coverage` freshness gate |
| `eac6aa9` P3 | Wire U17 gates into `work-lab-gate.yml` (policy-coverage + core-schemas + adapter-registry + capability-matrix) |
| `fbe789e` P4 | Close the protected-drive gap: user standing rule protects BOTH data drives (E + F); SSOT `protected_storage.protected_drives: [E, F]` + `drive_default: deny` (revision 1→2), fail-closed machine-baseline invariant, native guards generalized, goldens + loss reports regenerated (@rev2) |

## P4 audit finding (the "problem" the full audit caught)

The standing user rule protects BOTH data drives, but every machine-side guard
in the repo protected only the first one (regex `[Ee]:`, `^E:\` match, single
entry in DEFAULT_FORBIDDEN / forbiddenRoots). The P0/P1 SSOT inherited the same
single-drive shape, so the hermes loss report's `protected_storage:
NATIVE_ENFORCED` claim was dishonest against the user's rule. P4 fixes the
boundary end-to-end; the native `NATIVE_ENFORCED` claim is now honest.

### P4 change surface (21 files, +122/−62, all tightening-only)
- **SSOT**: `protected_storage` → `protected_drives: [E, F]` + `drive_default: deny`; schema aligned; revision 2
- **Fail-closed invariant**: `PROTECTED_DRIVE_BASELINE = {E, F}` in `policy_projection.validate_policy` — dropping either drive (or weakening drive_default) is rejected before any projection; `invariants_checked` 12→13
- **Native guards**: `services/policy/e_drive_guard.py` (regex now covers both protected drives; live hook filename + auth marker preserved for compatibility), `services/authority/machine_identity._reject_protected_drive`, `project_registry.DEFAULT_FORBIDDEN`, `projects.json` `forbiddenRoots`, `verify_project_data_boundary.py` assertion
- **Projections**: codex + hermes extensions, `global-guidance.md`, `config/SOUL.md`, both loss reports — regenerated through the canonical `--write` renderer entrypoints (never hand-edited)
- **Authoritative docs / deployment mirror**: `global-execution-standard.md`, `deploy_global_rules.py`, adapter-registry note — single-drive wording aligned to both protected drives
- **Tests**: F-block guard cases, machine-identity F rejection, drop-F negative control

## Evidence (branch, 2026-09-19)

- `run_quality_gate.py verify` (full VERIFY_ORDER sequence): **exit 0 PASS**
- `verify_policy_coverage`: **POLICY_COVERAGE_PASS** (loss reports codex + hermes, 10 software rows, 19 capabilities; golden freshness re-render clean)
- `verify_project_data_boundary`: **PASS** (forbiddenRoots now both protected drives)
- Targeted suites: guard 12/12, policy-projection 21/21, machine-identity 14/14, project-registry 4/4 — all green
- Isolated Codex native chain (P4 pre-check): plan → apply → VERIFY PASS (14 skills) → rollback
- Residual scan: no live E-only remnant in code/config/tests; `docs/history/archive/` keeps historical wording (immutable record, intentionally untouched)
- `CURRENT_STATE.*` generated artifacts left uncommitted (gate-run churn; P0–P4 convention)

## Boundaries honored
- No second authority / governance / ledger / adapter registry created; existing registry + ownership + executors reused
- Codex Markdown not raw-copied to all software; per-software native projection with honest loss reports
- No new long-term recovery branches
- model / provider / reasoning / auth / endpoint settings untouched (OBSERVE only)
- Deployment mirror change (`deploy_global_rules.py`) is source-only; live Hermes home sync is a separate explicit step

## Open items
- [ ] PR #127 CI green, then merge (user decision; this agent's grant is create-pr-only)
- [ ] After merge: run live Hermes/Codex syncer chains to deploy rev2 goldens into live homes (explicit operation, separate authorization)
