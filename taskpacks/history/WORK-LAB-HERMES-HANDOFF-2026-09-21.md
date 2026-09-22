# WORK-LAB HERMES HANDOFF — 2026-09-21 (U17 convergence closeout + repo hygiene)

Branch `u17/global-agent-policy-20260918`. All work is commit-anchored below —
nothing lives only in chat. Remote tip at handoff: `dafd479`; this commit adds
`359a0ae`'s successors: raw-socket CDP discovery + swiftshader flag.

## 1. Progress by unit (honest, evidence-anchored)

| Unit | Status | Anchor |
|---|---|---|
| U03–U08 frontend | DONE | `f0926e2` React rewrite to real v3 snapshot (phantom schema deleted) + `87618d1` 18 vitest/RTL tests + observer cargo CI. tsc 0, vite build green. |
| U09 usage one-truth | DONE | `50abfe6` `verify_usage_convergence.py` (schema-level, in CI) + `9b918e4` value-level one-truth conformance + fabricated-cost negative test (governance batch 1640 OK). Source audit: token-monitor has NO cost engine — spec deliverable #2 precondition ("its own rate table") does not hold; nothing to route. |
| U10 config transaction | DONE | `04a25f4` five gap mechanisms (revision floor, MISSING-vs-null, write-set OCC, expected-after, typed readback) + tests. |
| U11 REAL evidence binding | DONE | `f510516` additive REAL `EvidenceRecord` fields + `validate_real_binding`/`reject_fabricated_cost` + 4 tests. |
| U12–U14 | VERIFIED ALREADY IMPLEMENTED | 29 tests green; register corrected (was stale). |
| U15 language ADR | DONE | `25158bf` `docs/decisions/language-architecture.md` (5 concerns + reject big-bang Rust + grounded). |
| U16 contract SSOT | DONE | `25158bf` `verify_contract_ssot.py` + generated `packages/client-neutral-core/generated/contracts.ts` + CI step. |
| U18 universal real slices | PARTIAL (infra green, label auth-gated) | 47 tests green (nf08_a/nf08_e/nf14/real_adapters). **External-project WRITE stays NOT_AUTHORIZED** (AGENTS.md / STAGE3_BASELINE `externalProjectWrite`) — do not attempt. |
| U19 Windows Tauri E2E | PARTIAL (layered, honest) | see §2. |
| P0-06 tail | DONE | `ff08787` (pnpm remnants, workflow pyc, taskpack archive, NOTICE dead paths). |
| CI observer platform fix | DONE | `922c25c` — observer job ubuntu→windows-latest (Tauri needs MSVC native deps; mirrors token-monitor job), nf11 frozen manifest synced to `package-lock.json`. Verified by 04a25f4/f510516 work-lab-gate runs = SUCCESS. |

## 2. U19 layered evidence (release iron law: no closed-loop claim without evidence)

Proven layers:
1. backend: real sidecar v3 snapshot on loopback — PASS (CI + local, evidence `.project-local/runs/u19_webview_readback.json`).
2. native shell: MSVC-built `app.exe` LAUNCHES on CI (`tauri_launch: RUNNING`) — local GNU toolchain SEGVs (broken link chain), so CI is the only build that works.
3. web-engine: `scripts/u19_chromium_readback.py` — real Chromium CDP readback of real React `dist` + real sidecar data, DOM `rootTextLen>0`, **a11y live region "已切换为深色主题" present** (proves the U03 a11y migration landed in a real engine).

Pending layer: in-app WebView2 DOM readback.
- Root cause established (wry 0.55.1 source read): `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` env var is NOT consumed — wry always passes app-level args to `unwrap_or_else`. The only reachable path is the Rust builder API. `lib.rs` now has an **opt-in, default-off** CDP probe window (`WORK_LAB_U19_CDP_PORT`, `.additional_browser_args("--remote-debugging-port=… --remote-allow-origins=* --use-angle=swiftshader")`) — shipped behavior unchanged unless the var is set.
- CDP discovery in the harness switched from urllib to raw-socket HTTP (`_cdp_http_get`) — urllib was throwing `BadStatusLine` from proxy/transport pollution, not a closed port.
- GDI render-proof layer (`_gdi_render_proof`, user32 PrintWindow + pixel diversity) is the fallback proof that "not about:blank".
- NEXT: the CI run at the SHA containing `359a0ae` + the two follow-up commits verifies this layer. If `webview_readback` or `gdi_render_proof` lands PASS, U19 closes to DONE. Until then it is PARTIAL — say so, don't claim closed.

## 3. Repo hygiene performed (2026-09-21)

- Removed junction scratch `D:\wlu19` (space-free cargo build path, 1.86 GB; `rmdir` junction-only, canonical repo untouched, verified).
- `.project-local` 7159 → 2752 MB: removed `runs/tmp` (292 MB, regenerable), `runs/pycache` (39 MB), `runs/pytest-tmp` (2 MB), `quarantine/agent-observability` (3362 MB, third-party phoenix-venv/node_modules), `quarantine/codex-bin` (406 MB, re-downloadable), `quarantine/observer-webview2` (305 MB, re-downloadable), 440 `__pycache__`/`.pytest_cache` trees (~54 MB).
- RETAINED (deliberate): `quarantine/dsh-011-removed-20260824` (2409 MB, DSH recovery backup — provenance per DSH handoff docs), `dsh-202`/`dsh-cover-backup-*`, active `runs/venv` + `gate-venv` (the project test venv the gate requires), all `task-runtime` evidence, `artifacts`, `toolchains`, `wlc`.
- `D:\tmp` (36 files, 1 MB, DESIGN-LAB mmx-* mockups + blog.txt) is user-level cross-project scratch — NOT a WORK-LAB spill; left untouched.
- Protected drives E:/ F: never touched. `git status` clean after all cleanup.

## 4. Environment facts (for the next session)

- Test iron law: `env -u PYTHONPATH uv run --frozen --group ci --group ci-adapters pytest` (governance gate runs 163 modules / 1640 tests).
- Governance gate: `python services/orchestration/run_quality_gate.py governance` — prints `QUALITY_GATE_GOVERNANCE_PASS modules=…` when green.
- CURRENT_STATE churn: the pre-commit hook rewrites `CURRENT_STATE.json/.md` `generated_at` on every commit. The CI freshness gate checks **source_digest**, which only changes when canonical files change. After changing `work-lab-gate.yml` or any CANONICAL file, run `scripts/ci/generate_current_state.py` + `git add` the two files in the SAME commit. `--check-current` PASS means the digest matches.
- Local toolchain reality: MSVC rustc in `~/.rustup` has NO linker (no link.exe/cl.exe anywhere on the box); GNU toolchain lacks dlltool until `D:\All projects\OS External Configuration\toolchains\mingw\mingw64\bin` is on PATH, and GNU-linked `app.exe` SEGVs at runtime. Conclusion: **do not try to build the Tauri exe locally** — CI's windows-latest MSVC toolchain is the only working build path.
- Subagent channel is broken: `delegate_task` children fail with HTTP 401 (the custom API key is not inherited). Do NOT re-dispatch; do the work centrally.

## 5. Merge & release posture

- `merge_main = false` stays in the taskpack register UNLESS the user explicitly re-authorizes the merge in THIS session's thread. The CI dual-gate (work-lab-gate + wlr-060) must be SUCCESS on the exact merge SHA; the observer job carries the U19 E2E step (Windows Tauri shell CDP/GDI readback), so a RED observer job blocks the merge gate.
- Unproven items in the register (§9 of the taskpack): real-Host E3 / real-tag E5 evidence — unchanged, still to be proven at release.

## 6. Open items to verify first on resume

1. CI work-lab-gate on the newest push (contains raw-socket CDP + swiftshader + GDI fix): did `webview_readback`/`gdi_render_proof` stage land? If PASS → flip U19 register row to DONE + update §U19 evidence.
2. If the CDP probe still fails on CI, the remaining options are: (a) accept GDI-only proof as the WINDOWS_TAURI_E2E evidence (recorded decision), (b) move to `--headless` chromium-equivalent proof only, or (c) user decision on shipping an opt-in CDP hook in the release binary. Do not silently widen scope.
3. `.project-local/quarantine/dsh-*` retention review if DSH work is ever closed out (only with explicit authorization).
4. `D:\tmp` cleanup is a user-level decision, not a WORK-LAB one.
