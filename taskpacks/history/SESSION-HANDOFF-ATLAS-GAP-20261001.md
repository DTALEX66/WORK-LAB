# WORK-LAB SESSION HANDOFF — Atlas gap remediation (2026-10-01)

**Class:** dated session handoff / continuation record. **NOT** a taskpack, **NOT** a new
authority, and it grants nothing. The task ledger of record is and remains
`taskpacks/current/OPEN-TASK-REGISTER.md` (rows `AG-*`), with the work breakdown in
`taskpacks/current/WORK-LAB-ATLAS-GAP-REMEDIATION-TASKCARD-20261001.md`.

Read in this order before acting: `WORK-LAB-AUTHORITY.md` →
`.project/governance/project-authority-index.json` → `AGENTS.md` → the CURRENT taskpack →
`taskpacks/current/OPEN-TASK-REGISTER.md` (the `SESSION DELIVERY STATUS` block first) →
this file last.

## 1. Where things actually stand

> **ADDENDUM (2026-10-01, rounds 8-11).** The table below was written at round 8
> (`9e68469`). Work continued to round 11 (`c3a38fc`) and added: the AG-05c
> resolvable model→runtime binding and orphan-digest honesty; the AG-05d
> field-level closure report (new gate `registry-closure-report`, reaching
> `closed=47 explicitly_open=11 unclosed=0`); and the AG-05e re-anchoring of the
> reranker runtime note. **`verify` is now 45 gates and the branch is 46 commits
> ahead of `main`.** Nothing about the "not merged / not released / no exact-SHA
> CI" position changed. New gates: `model-registry-integrity`,
> `acp-adapter-honesty`, `observer-readonly-boundary`, `registry-closure-report`.
> New negative controls: `nf20`-`nf26`, **111 tests** (18 / 6 / 28 / 7 / 13 / 24 / 15),
> all green locally.

| Item | Value |
|---|---|
| Branch | `task-decomposition/atlas-gap-archive-20261001` |
| Head at handoff | `9e68469` (self-audited ledger status block) |
| `main` | `cd4daa83e107afab8438c0e85f63a10e75314d5a` — **unchanged; nothing from this session is merged** |
| Commits this session | 21, all local. No PR opened. **No exact-SHA CI has run.** |
| Released / deployed | **NO.** Nothing pushed, published, installed or migrated. No global or machine config changed. |
| Canonical suite | `run_quality_gate.py verify` → **PASS, 44 gates** |
| Toolchain required | `.project-local/toolchains/wl-py311/Scripts/python.exe` (Python 3.11.15, yaml 6.0.3, jsonschema 4.26.0) |

**The toolchain point is load-bearing.** Running the gate under the bare DSH-bundled
interpreter fails closed with `QUALITY_GATE_DEPENDENCY_FAIL` (no yaml/jsonschema). That is a
wrong-interpreter artifact, **not** a repo defect — do not "fix" it by installing anything;
use the declared toolchain. A whole round was lost to this before it was caught.

## 2. Authority and scope actually exercised

Authorized and exercised: read attachments, read repo/Git/cloud state, and make ordinary
reversible repairs inside WORK-LAB on an isolated branch, with tests. Continuation was
explicit ("全部开始", then "按优先级全部执行").

**NOT authorized and NOT done:** push, merge, release, deployment, global Codex/Hermes/DSH
config writes, installing or upgrading toolchains, downloading models, deleting weights or
history, paid calls, provider switching, or touching the other two projects' business data.
E:/F: access was never needed or attempted.

## 3. What was delivered (all local, all verified locally)

**Code fixes**

- **AG-01/02/03/04** `model_capability_resolver.py` — explicit user choice is now terminal
  (an overlay can no longer silently overwrite it); one shared gate so a missing required
  capability is refused on the explicit AND overlay paths, not just the scan path;
  SHA-256 session affinity instead of the salted builtin `hash()`; the previously dead
  `runtime_health` input is now an enforced gate. Also fixed a latent scan defect where
  alphabetical order could beat a better affinity score. `5a6d5cd`.
- **AG-05** registry integrity — OCR `binds_to_model` corrected off the legacy Ollama blob
  name; new `binding_status` separates binding truth from endpoint truth (the "OPERATIONAL
  but not served" contradiction); two truncated digests completed to full 64-hex, three with
  no recoverable value moved to explicit `null` + `assetDigest{state:TRUNCATED, reason}`;
  in-process ASR libraries declared distinctly as `processLibraries[]`. `6e16684`.
- **AG-06** adapter honesty — removed a false `Capability.RESUME` declaration from
  codex/dsh/openhands (they advertised a capability whose operation was the base no-op);
  `test_native_effect_truth` rewritten to defend its own stated contract instead of pinning
  one status string. `6e16684`.
- **AG-07** de-pinned the DSH install path; official-build detection now *resolves* the root
  (override env → `%LOCALAPPDATA%` vendor default → uninstall entry matched on `DisplayName`
  prefix, because the key is a GUID); Hermes version corrected to the natively-read-back
  `0.21.5+3115.g10938a7`. `a676e63`.
- **AG-14b** two silent-truth defects: `config/software-registry.json` carried a UTF-8 BOM
  that made `software[]` **always empty** with the error swallowed by a bare `except`
  (registry 0→7, projection 0→7); and `platform_discovery._probe_install` took the first
  merely-*existing* root without expanding env vars, so DSH resolved to a stale directory
  (`SINGLE_UNVERIFIED @ D:` → `SINGLE_VERIFIED @ <vendor default>`). `8f049d2`.
- **AG-16** `plan_candidate.py` — the missing middle link of the super-entry chain
  (ContextEnvelope → PlanningCandidate → check/authorize → executor → Receipt). Pure and
  deterministic; planning output **never** authorizes execution, a verdict is **never** an
  execution, unresolved blocking items stop a plan even with a valid grant, dedupe is
  content-addressed, capability is checked before authorization, malformed input fails closed
  with a verdict rather than an exception. `774a514`.

**New fail-closed gates (3)** — `model-registry-integrity`, `acp-adapter-honesty`,
`observer-readonly-boundary`; all wired into `GATES`, `VERIFY_ORDER` and `CHANGED_PATHS_MAP`.

**New negative controls (87 tests, `nf20`–`nf25`)** — 18 / 6 / 19 / 7 / 13 / 24. Writing them
found and fixed **three real bugs in the new code itself**, which is the point of them: the
model-digest rule was only applied to providers, the ACP over-claim check tested method
presence instead of real effect (so it could not fire on the defect it exists to catch), and
`plan_candidate._verdict` crashed with `AttributeError` on a `None` return instead of failing
closed.

**Repairs to the ledger itself (three, all found by auditing rather than trusting narration)**

- The UI L10b / B10 replication was **already finished and merged** (PR #143 `612d5aa`,
  PR #144 `9ffb0c5`) while a stale handoff still read as an open assignment;
  `HANDOFF-UI-L10B.md` now carries a CLOSED banner with the PR numbers and the replaced SHA.
- A pre-existing order-dependent test flake was root-caused (an unsynchronized read of an
  asynchronously written collector health record while the sibling test already polled) and
  fixed; 20/20 stress runs pass. `0c0a6c7`.
- The AG section header still claimed nothing was executed, and nothing said the work was
  unmerged; both corrected with a `SESSION DELIVERY STATUS` block. `9e68469`.

## 4. Evidence locations

- Gates: `python services/orchestration/run_quality_gate.py verify` (44 gates).
- ACP honesty matrix: `.project-local/runs/ag06-acp-honesty-matrix.json`.
- Frontend (run with the off-PATH bundled Node against existing `node_modules`, since npm and
  pnpm are absent from PATH): `tsc -p tsconfig.json --noEmit` 0, `vitest run` **72/72**,
  `vite build` 0.
- Live readbacks: DSH `official-deepseek-harness` `0.2.0-rc.2` @ vendor default path;
  `git fetch origin --prune` exit 0.

## 5. Deliberately NOT done, with the real reason

| Item | State | Reason |
|---|---|---|
| Merge / PR / release | NOT_RUN | Not authorized. Branch is 21 commits ahead of `main`. |
| Exact-SHA CI | NOT_RUN | Requires a push. Local gates are **not** CI evidence. |
| AG-09/10/11 real dual-executor chain, model consumer acceptance | BLOCKED | Needs a user-selected project, two executors, and per-operation authorization. |
| Tauri/Rust desktop build | BLOCKED | The shared CARGO_HOME lacks `tauri-plugin-log`; a build needs an approved network fetch or a vendored cache. **The Rust GNU toolchain itself works** (`rustc`/`cargo` 1.97.1); the MSVC toolchain is partial (cargo but no `rustc`) and there is no Visual Studio/VC toolset at all. |
| AG-15 writable Control Surface | OWNER DECISION NEEDED | Its prerequisite is now machine-enforced, but the backend does not exist: the sidecar is deliberately read-only (non-GET → 405) and the control-plane services are in-process only. Shipping just the UI would be the fake-success demo the repo forbids. |
| AG-12 rerank scores, AG-13 unattended scope, AG-17 web-GPT transport, AG-18 thin-entry split | OWNER DECISION NEEDED | Product/scope calls, recorded in the register. |
| `DSH_HOME` / D: data-root migration | OWNER DECISION NEEDED | The user env var still points at `D:\All projects\DSH\.dsh`, which holds the user's existing sessions. Nothing was changed; whether the official build honours `DSH_HOME` was **not** tested. |
| AG-19/20 history recovery | BLOCKED | **This session has no ChatGPT history access and does not claim to have searched there.** "Not found" ≠ deleted ≠ non-existent. |

## 6. Traps that cost time here — do not repeat

1. **Wrong interpreter.** Use `.project-local/toolchains/wl-py311`. The bare bundled runtime
   has no yaml/jsonschema and makes the gate fail closed.
2. **PowerShell + git.** Multi-line `-m` messages break; use `-F <file>`. Also avoid backticks,
   `2>/dev/null`, `<<<`, and `>` for restoring files (it writes UTF-16 and yields
   `null bytes` / `SyntaxError`).
3. **PATH is not the whole truth.** Classify tools as *on PATH* / *off PATH but working* /
   *broken or partial*. Re-checking only PATH produced a false "Rust is absent" claim for
   several rounds.
4. **A pinning path rots.** No drive letter belongs in a registry or an inventory. Two
   separate code paths had this bug.
5. **A swallowed parse error is invisible.** `except Exception: return []` turned a BOM into a
   permanently empty projection with no failure anywhere. When a projection is suspiciously
   empty, invoke the real loader rather than reading the file.
6. **Trust the code, not the note.** Three separate stale records (the 9/26 audit's "three
   projection gaps", the L10b handoff, the AG header) were wrong in a way that would have cost
   a round each.

## 7. Recommended next steps, in order

1. **Decide the owner-gated items** (AG-15 (a)/(b), AG-17, AG-18, AG-12, AG-13, `DSH_HOME`).
2. **Get this branch reviewed.** 21 local commits on a branch based on `ec275a3` (19 commits
   ahead of `main` before this session's work). Rebase onto `main@cd4daa83` first if a clean PR
   is wanted; push/PR needs explicit authorization.
3. **If a Rust build is wanted**, authorize a one-off dependency fetch (or provide a vendored
   cache) and then re-attempt `cargo check` with the GNU toolchain — note the earlier finding
   that local GNU-built Tauri binaries failed at runtime with `WebView2Loader` missing, so the
   desktop layer likely still needs MSVC.
4. Only then the authorization-gated real-execution lanes (AG-09/10/11).

## 8. Recovery checklist

- [ ] `git rev-parse HEAD` — expect `9e68469` or a descendant on
      `task-decomposition/atlas-gap-archive-20261001`.
- [ ] `git status --porcelain` — expect only the user's pre-existing edits
      (`CURRENT_STATE.json/.md`, `App.tsx`, `Sidebar.tsx`, untracked `docs/future/`).
- [ ] Read the `SESSION DELIVERY STATUS` block in the register **before** any AG row.
- [ ] Run `verify` with the declared toolchain; expect 44 gates PASS.
- [ ] Do **not** re-run the historical taskpacks, and do **not** treat this handoff as
      authority.
