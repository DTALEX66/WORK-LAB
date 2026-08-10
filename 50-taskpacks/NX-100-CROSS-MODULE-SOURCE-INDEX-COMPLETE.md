# NX-100 — Cross-Module Source Ledger V3 / Honest Absorption Index

**Status:** `COMPLETED`
**Task pack:** `WORK-LAB-STAGE-2-ABSORPTION-INTEROP`
**Date:** 2026-08-08

## Goal

Establish an honest cross-module source index so that a *decision* status
(`adopt-now`, `adapter-next`, `reference-now`) is never presented as an
claim WORK-LAB absorption.

## Deliverables

1. **`00-governance/cross-module-source-index.json`**
   - Each marked `decisionStatus=external-optional`, `implementationStatus=not-implemented`
   - Accounting: `adopt_now_total=33`, `complete_in_worklab=0`,
     `partial_in_worklab=0`, `no_worklab_targets=33`.

2. **`scripts/ci/verify_cross_module_source_index.py`**
   - Fails if a `local-verified` claim lacks real existing target paths.
   - Reconciles adopt-now accounting (complete + partial + none = total).

3. **`tests/ci/test_cross_module_source_index.py`** (4 tests)
   - local-verified requires existing target.
   - Removing a target auto-downgrades → verification fails.
   - local-verified on an existing WORK-LAB path passes.

4. **CI** `.github/workflows/work-lab-gate.yml` integration job now runs the
   cross-module index verifier + tests.

## Verification

```text
CROSS_MODULE_SOURCE_INDEX_PASS entries=33 adopt_now=33 complete=0 partial=0 none=33 honest=true
tests/ci/test_cross_module_source_index.py: Ran 4 tests OK
```

## Honesty principle

`adopt-now` is a *decision* to consider absorption; it is **not** an
WORK-LAB target paths, therefore they are recorded as `not-implemented` in

## Rollback

Remove `cross-module-source-index.json`, the verifier, the test, and the two CI
steps. No runtime dependency.
