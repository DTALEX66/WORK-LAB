# WORK-LAB CURRENT OPEN TASK REGISTER

**Register ID:** `WORK-LAB-OPEN-TASK-REGISTER-20260918`  
**Authority:** `WORK-LAB-AUTHORITY.md`  
**Current TaskPack:** `WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918`  
**Preparation baseline:** `main@803268da9dc356fe63f26b3b5405f724bc06b5b9`

This is the single live register.

> 2026-09-20 reconciliation: rows A03/A04/U01/U17/U17a are IMPLEMENTED and EXACT-SHA CI VERIFIED at head `0600d6f` (work-lab-gate 35460820372 / wlr-060 35460820357, both success). They are NOT DONE: lifecycle MERGED -> READBACK -> ACCEPTED not yet reached (merge_main=false; no main merge). U02 is PARTIAL (read-only path convergence only).

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
| U03 | P0 | OPEN | React + Tauri sole production Observer UI; static UI parity then retirement |
| U04 | P0 | OPEN | Typed frontend view registry; fix Delivery/Trust/Settings navigation |
| U05 | P0 | OPEN | Real Full/Compact/Dark/Light handling |
| U06 | P0 | OPEN | Runtime Descriptor + Snapshot/SSE; remove URL double-append/fixed ports |
| U07 | P0 | OPEN | Frontend truth discipline; remove hard-coded price/FX/quota/fake zero/status fallthrough |
| U08 | P0 | OPEN | React behavior tests + Observer Rust CI + Windows Tauri E2E |
| U09 | P1 | OPEN | Token Monitor/Observer convergence with one usage/cost truth engine |
| U10 | P0 | OPEN | Config transaction safety/readback truth |
| U11 | P0 | OPEN | REAL evidence binding; empty REAL handle invalid |
| U12 | P0 | OPEN | Durable Inbox/outbox cross-process safety and exact receipt ACK |
| U13 | P0 | OPEN | Project isolation and usage/cost attribution truth |
| U14 | P0 | OPEN | Session/execution/worker native-effect truth |
| U15 | P0 | OPEN | Language architecture ADR; no big-bang Rust rewrite |
| U16 | P1 | OPEN | JSON Schema cross-language SSOT and conformance |
| U17 | P1 | IMPLEMENTED@0600d6f | Software Installation Identity + Update Preflight (P0-07, 2f3ab29/39b75bb/d73855a/0600d6f): 2 new contracts (catalog 35), pure resolver (UPDATE != RELOCATION, 8-state location_status, fail-closed), DSH 5-case golden regression + 7 negative tests, schema-conformance tests; location_readback FAIL closes overall. EXACT-SHA CI PASS at 0600d6f. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED. |
| U17a | P1 | IMPLEMENTED@0600d6f | P0-04 current-state de-duplication: two stale CURRENT projections (docs/decisions/CURRENT_STATE.md 2026-09-01 + CURRENT_EXECUTION_BASELINE r4/bf52df0) retired to docs/history/archive/superseded-current; single machine CURRENT + one human projection kept; CURRENT_STATE_TP20260819 preserved as SUPERSEDED-layer snapshot. EXACT-SHA CI PASS at 0600d6f. Lifecycle: awaiting MERGED -> READBACK -> ACCEPTED. |
| U18 | P1 | WAITING_AUTH_WHERE_REQUIRED | Universal Workflow real publish/external project/second executor/multi-environment/global-rule readback |
| U19 | P0 RELEASE | OPEN | Full Windows product E2E and exact-SHA release gate |
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
