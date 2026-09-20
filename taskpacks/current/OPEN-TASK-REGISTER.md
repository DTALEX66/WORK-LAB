# WORK-LAB CURRENT OPEN TASK REGISTER

**Register ID:** `WORK-LAB-OPEN-TASK-REGISTER-20260918`  
**Authority:** `WORK-LAB-AUTHORITY.md`  
**Current TaskPack:** `WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918`  
**Preparation baseline:** `main@803268da9dc356fe63f26b3b5405f724bc06b5b9`

This is the single live register.

> 2026-09-20 reconciliation: rows A03/A04/U01/U17/U17a are IMPLEMENTED and EXACT-SHA CI VERIFIED at head `0600d6f` (work-lab-gate 35460820372 / wlr-060 35460820357, both success). They are NOT DONE: lifecycle MERGED -> READBACK -> ACCEPTED not yet reached (merge_main=false; no main merge). U02 is PARTIAL (read-only path convergence only).
> 2026-09-20 reconciliation (2nd pass, branch head `656e7d2` on u17/global-agent-policy-20260918, merge_main=false): new rows U20 (real-time parallel agent-invocation P1-P3: commits 69e1025/2d92c6d/c367e22/bc3fe85, CI dual gate @bc3fe85 work-lab-gate 35468657962 + wlr-060 35468657960, both success) and U21 (software-update-postflight anti-recurrence gate + DSH update/maintenance RUNBOOK: commits 99bb300/656e7d2, contract catalog 36->37, CI dual gate @656e7d2 work-lab-gate 35518131963/35518131413 + wlr-060 35518131297/35518131970, all success). Handoffs: docs/history/archive/session-history/WORK-LAB/WORK-LAB-PARALLEL-DISPATCH-HANDOFF-2026-09-20.md and WORK-LAB-DSH-UPDATE-MAINTENANCE-RUNBOOK-2026-09-20.md.

| ID | Priority | Status | Work |
|---|---|---|---|
| A00 | P0 | BLOCKED_CURRENT_CHATGPT_GITHUB_SCOPE | Land authority package; current ChatGPT GitHub integration returned 403 for branch creation and file creation |
| A01 | P0 | OPEN | Restore/verify PR-first main protection and required `aggregate` exact-SHA gate |
| A02 | P0 | OPEN | Clean/freeze obsolete current docs and legacy roots, but only after A04 removes current CI/generator dependencies |
| A03 | P0 | IMPLEMENTED@0600d6f | Machine authority-reference verifier + allowlist gate landed (commit 63d50ba): referenced-paths existence + supersedes graph verified, not trusted; 13/13 authority negative controls; EXACT-SHA CI PASS at 0600d6f (work-lab-gate 35460820372). Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED (merge_main=false). |
| A04 | P0 | IMPLEMENTED@0600d6f | CURRENT_STATE de-Stage3 + dynamic contract count (2a78aaa/a19de2a): stage3 demoted to compatibility_history, generator + 3 consumers synced, 2 stale CURRENT projections retired to docs/history/archive/superseded-current; FRESHNESS_PASS 51c8363; EXACT-SHA CI PASS at 0600d6f. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED. |
| A05 | P0 | OPEN | Preserve truthful squash-cutover lineage and MiniGame `FOREIGN_HISTORICAL` semantics |
| U01 | P0 | IMPLEMENTED@0600d6f | Mandatory test truth landed (a84495a): unified test_*.py + nf*.py discovery (modules=153 -> 154), 5 fail-closed guards (empty-set/not-run/non-zero/failed-batch/real negative mutation); governance batch exit 0. EXACT-SHA CI PASS at 0600d6f. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED. |
| U02 | P0 | PARTIAL | P0-06 read-only path convergence done (986d6a9): README + PROJECT_POSITIONING now point to packages/client-neutral-core, apps/observer, .project/governance, taskpacks/current, config/; no file moves. manifest/profile/setup/runtime-root/package-manager cleanup NOT claimed. |
| U03 | P0 | PARTIAL | React + Tauri production Observer UI is the SSOT (`f0926e2`); **parity matrix authored** (`apps/observer/parity-matrix-u03.md`). Valid a11y capability (`WlA11y.announce` WCAG AA live region) **migrated to React** `src/lib/a11y.ts` + wired into `App.tsx` + 5 real-DOM tests (`b1a7e3d`). Intentionally NOT migrated: `WlCharts` (no v3 time-series data → would be a phantom KPI) / `escapeHtml` (React-native). **Static `web/` deletion stays gated**: it is the live browser read-only entry via `sidecar.py` → retirement is a **U19** step, not executed here |
| U04 | P0 | IMPLEMENTED@f0926e2 | Typed frontend view registry (viewRegistry.ts), registry-driven Sidebar; Delivery/Trust/Settings all reachable. Merge-pending lifecycle. |
| U05 | P0 | IMPLEMENTED@f0926e2 | Real Full/Compact/Dark/Light: CompactHUD dedicated view, index.css CSS-variable surfaces + light remap, index.html no hard-coded `class="dark"`. |
| U06 | P0 | IMPLEMENTED@f0926e2 | RuntimeDescriptor + Snapshot/SSE; removed URL double-append + fixed ports (api.ts 343L). |
| U07 | P0 | IMPLEMENTED@f0926e2 | Frontend truth discipline: Views.tsx real v3 schema, no `Number()||0`/fake-zero fallthrough, mock.ts + 4 phantom dashboard components deleted, no hard-coded price/FX/quota. |
| U08 | P0 | PARTIAL | React behavior tests (18 vitest+RTL) + Observer `cargo test/check --locked` CI @87618d1. **Windows Tauri real-WebView E2E deferred to U19** (needs real WebView readback, not a bare exe launch). |
| U09 | P1 | IMPLEMENTED@2a3756b | One canonical usage/cost truth contract: verify_usage_convergence.py (fail-closed, schema-driven) proves usage-observation.schema.json is the single canonical contract + token-monitor Rust is a cost-free specialist helper (no second engine, §22). CI step added. |
| U10 | P0 | IMPLEMENTED@04a25f4 | Config transaction truth: 5 gap mechanisms added additively to config_control_plane.py — monotonic revision floor (STALE_REVISION), MISSING-vs-explicit-null (strict diff), expected-before+write-set (CONFLICT/WRITE_SET_VIOLATION), intended-after (READBACK_MISMATCH), typed readback (READBACK_FAILED_TYPED). 33 passed, governance gate 162 PASS. |
| U11 | P0 | IMPLEMENTED@f510516 | REAL evidence binding: EvidenceRecord +6 verifiable-identity fields (evidence_type/receipt_digest/producer/verifier/observed_at/source_sha), empty REAL handle rejected up front, validate_real_binding + real_binding_status. 18 passed, single importer (nf02). |
| U12 | P0 | IMPLEMENTED@gate | Durable Inbox/outbox cross-process + exact receipt ACK — already implemented; verified green in the 162-module governance gate (nf08_b durable_inbox + test_durable_inbox), not a new commit. Register row was stale (§33). |
| U13 | P0 | IMPLEMENTED@gate | Project isolation + usage/cost attribution truth — already implemented; verified green in the 162-module gate (nf08_h + cross_project_isolation). Register row was stale (§33). |
| U14 | P0 | IMPLEMENTED@gate | Session/execution/worker native-effect truth — already implemented; verified green in the 162-module gate (canonical L0-L3 + acp_facade + test_native_effect_truth). Register row was stale (§33). |
| U15 | P0 | IMPLEMENTED@25158bf | Language architecture ADR: docs/decisions/language-architecture.md (React/TS UI + Rust/Tauri + Python + JSON Schema SSOT; no big-bang rewrite). |
| U16 | P1 | IMPLEMENTED@9a6ea95 | JSON Schema cross-language SSOT: verify_contract_ssot.py (catalog-driven, 37 contracts, no hard-coded counts) + generate_contract_types.py → packages/client-neutral-core/generated/contracts.ts. 13 on-disk helper schemas surfaced as advisory, not hard-fail. |
| U17 | P1 | IMPLEMENTED@0600d6f | Software Installation Identity + Update Preflight (P0-07, 2f3ab29/39b75bb/d73855a/0600d6f): 2 new contracts (catalog 35), pure resolver (UPDATE != RELOCATION, 8-state location_status, fail-closed), DSH 5-case golden regression + 7 negative tests, schema-conformance tests; location_readback FAIL closes overall. EXACT-SHA CI PASS at 0600d6f. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED. |
| U17a | P1 | IMPLEMENTED@0600d6f | P0-04 current-state de-duplication: two stale CURRENT projections (docs/decisions/CURRENT_STATE.md 2026-09-01 + CURRENT_EXECUTION_BASELINE r4/bf52df0) retired to docs/history/archive/superseded-current; single machine CURRENT + one human projection kept; CURRENT_STATE_TP20260819 preserved as SUPERSEDED-layer snapshot. EXACT-SHA CI PASS at 0600d6f. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED. |
| U18 | P1 | WAITING_AUTH_WHERE_REQUIRED | Universal Workflow real publish/external project/second executor/multi-environment/global-rule readback |
| U19 | P0 RELEASE | OPEN | Full Windows product E2E and exact-SHA release gate |
| U20 | P1 | IMPLEMENTED@bc3fe85 | Real-time parallel agent-invocation (P1-P3): `ParallelDispatcher.fanout`/streaming events (services/execution-federation/parallel_dispatch.py), contract `execution-parallel-dispatch` (catalog 36), passive receipts evidence adapter (services/receipts/parallel_dispatch_evidence.py); tests 31 green; dual-gate CI @bc3fe85 success. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED (merge_main=false). |
| U21 | P1 | IMPLEMENTED@656e7d2 | DSH update anti-recurrence hardening: `software-update-postflight` pure gate module + contract (catalog 37, closed 10-value reasons enum, 21 tests incl. 12 negative controls: NSIS .lnk reset / DSH_HOME session-freeze C-fallback / resources\app wipe each fail-closed) + WORK-LAB-DSH-UPDATE-MAINTENANCE-RUNBOOK-2026-09-20.md (7-step SOP + 3 traps + rollback). Dual-gate CI @656e7d2 success. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED (merge_main=false). |
| B3 | P1 | MAPPED_U17 | Codex/DSH governance follow-up from legacy OPEN register |
| C1 | P1 | MAPPED_U17 | ACP/MCP/AG-UI/model-alias adaptation |
| C4 | P1 | MAPPED_U14_U18 | Real Codex cancellation |
| C6 | P1 | MAPPED_U13 | Real usage workbook/data source |
| D1 | ENV | BLOCKED_SCOPED | Sandbox ACL synthetic acceptance only; does not block unrelated work |
| D2 | USER AUTH | BLOCKED | Legacy `.bak` deletion requires explicit user authorization |
| C2 | OPTIONAL | DEFERRED | Paid four-arm model experiment |
| C3 | OPTIONAL | DEFERRED | Kimi / Agents API / Bolt research |
| O1 | OPTIONAL | DEFERRED | Hermes state.db optimize-storage |
| O2 | OPTIONAL | DEFERRED | API-key doctor / convenience checks unless a concrete defect makes them blocking |
