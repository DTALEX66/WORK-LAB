# WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019

**Status:** CURRENT / MINIMAL_LOOP_DELIVERED (authority convergence + first real loop delivered; other tasks remain frozen)
**Date:** 2026-10-19
**Owner:** DTALEX66
**Authority source:** user directive 2026-10-19 + `WORK-LAB-AUTHORITY.md` + `.project/governance/project-authority-index.json`
**Source package:** `docs/history/owner-inputs/20261019/WORK-LAB_权威收敛任务包_20261019.zip` (`WL-REC-0105`)
**Product implementation:** DELIVERED under the 2026-10-19 user grant (“执行所有未完成的任务，按照最新发你的任务包”):
one product fix for `WORK-LAB-MINIMAL-LOOP-001` (`services/execution-federation/hermes_adapter.py`),
verified at the adapter layer and recorded as `SOLUTION-001`. No other product feature is implemented;
documentation update alone is still not feature completion.

## 1. Purpose

The owner directive of 2026-10-19 freezes other tasks and makes this package the current
authority and closed-loop target: verify the current authority/index/ledger/Git state,
converge the formal positioning and roadmap, and establish one real minimal problem loop
as the first current work item. It is not a new Agent, not a rewrite of WORK-LAB, and not
implementation of historical proposals.

The formal positioning is the one recorded in `WORK-LAB-AUTHORITY.md` §2:
WORK-LAB is a client-neutral, personal-AI-environment workflow management, governance,
runtime monitoring and problem closed-loop system. It is not an Agent, a generic Agent
Runtime, a model gateway, a generic chat client, or a universal professional auditor.

## 2. Baseline recorded before any edit

| Item | Value |
| --- | --- |
| Branch | docs/handoff-20261018-qoder（分支名，非仓库路径） |
| HEAD | `0369d349d46b75c7048b884331bb40a0f42d4e34` |
| `origin/main` | `f6077d18cfc76d588d9315ec0ac82769c3009d9a` |
| `origin/main` tree | `6dcb2094ffa5fdb693e959de5aaa870eea8b1f78` |
| HEAD vs `origin/main` | 1 commit ahead (`0369d349` is a descendant of `f6077d18`) |
| Worktree | 59 porcelain entries before this task; 4 are the protected parallel-writer files (`AGENTS.md`, `config/adapter-registry.json`, `config/client-evidence.json`, `taskpacks/current/error-ledger.json`) |
| Top human authority | `WORK-LAB-AUTHORITY.md` |
| Top machine authority | `.project/governance/project-authority-index.json` |
| Scoped taskpack authority | `.project/governance/taskpack-authority-index.json` |
| Single open-task register | `taskpacks/current/OPEN-TASK-REGISTER.md` |

The dirty worktree contains prior WUI/HUD work. This task does not revert, overwrite or
commit it. Only the files listed in §7 and the new files created for this convergence are
edited.

## 3. Scope

Allowed:

- Authority and roadmap convergence: `WORK-LAB-AUTHORITY.md`, the two governance indexes,
  the new CURRENT taskpack, the convergence report/roadmap, and the index/handoff surfaces
  that would otherwise misdirect the next reader to the superseded UI-first current.
- Registration of this owner package in the existing owner-material catalog.
- Read-only inspection of the repository to build the conflict matrix and capability map.

Not allowed:

- Product feature implementation, Agent/Runtime framework work, model gateway work, or
  rewriting historical proposals into code. **Amended 2026-10-19:** the user directive
  “执行所有未完成的任务，按照最新发你的任务包” is the concrete Task Grant for the minimal
  loop only (one product fix, ML-001); it does not authorize any other feature work.
- Modifying `DESIGN-LAB` or `AAOS` repositories, or writing their internal state.
- Overwriting the dirty worktree; reverting or committing protected parallel-writer files.
- Creating a second task truth, a second open register, or closing tasks without evidence.
- Claiming tests, live runtime verification, solution solidification or AAOS acceptance that
  did not happen.

## 4. Problem loop and first real minimal loop

The tracked problem loop is:

`发现 → 去重/关联 → 问题摘要 → 匹配历史方案 → 建议或 Agent 修复任务包 → 用户/授权策略交接 → Agent 实际修复 → 测试与运行读回 → 关闭或继续 → 方案固化 → 必要时 AAOS 知识候选`

The stages are recorded separately. Agent self-report, HTTP 200, a single exit code, a
document edit or a submitted candidate is never by itself a verified repair or an AAOS
acceptance.

The first real minimal loop was delivered on 2026-10-19 under the user grant.
`WORK-LAB-MINIMAL-LOOP-001` started from a real, reproducible, locally observable problem
(the tracked AG-06 capability verifier failing on the live tree), produced an issue summary
and a manual repair handback (no live handoff interface exists), was repaired in the product
(`services/execution-federation/hermes_adapter.py`), verified by re-running the exact gate,
12+49 regression tests and an adapter-level readback, and recorded as
`docs/current/authority-convergence-20261019/solutions/SOLUTION-001-ACP-HERMES-RESUME.md`.
No simulated data stood in for the real source. Details and receipts:
`docs/current/authority-convergence-20261019/implementation/WORK-LAB-MINIMAL-LOOP-001-ACP-HERMES-RESUME.md`.

## 5. Deliverables and acceptance

| Deliverable | Where | State after this task |
| --- | --- | --- |
| Repository baseline | this file §2 + convergence report | RECORDED |
| Positioning conflict matrix | `docs/current/authority-convergence-20261019/AUTHORITY-CONVERGENCE-20261019.md` | DELIVERED |
| Updated formal authority | `WORK-LAB-AUTHORITY.md` | DELIVERED (documentation) |
| Updated machine authority | `.project/governance/project-authority-index.json`, `.project/governance/taskpack-authority-index.json` | DELIVERED (documentation) |
| Converged roadmap | `docs/current/authority-convergence-20261019/ROADMAP.md` | DELIVERED |
| Current capability map | convergence report §capability map | DELIVERED with measured evidence and gaps |
| Future capability list | roadmap CURRENT/NEXT/FROZEN/DEFERRED/RETIRED + unfreeze conditions | DELIVERED |
| Test report | convergence report §test report | DELIVERED with commands, exit codes, exact HEAD |
| Source package registration | `docs/history/owner-inputs/RECORD-ARCHIVE-REGISTER.json` (`WL-REC-0105`) + member register | DELIVERED |
| One real minimal loop | `WORK-LAB-MINIMAL-LOOP-001` + `SOLUTION-001` | DELIVERED (implementation card; verifier + 12/49 tests + adapter readback; AAOS NOT_SUBMITTED; CI not run) |

Acceptance follows the owner package: positioning is workflow management/governance/
runtime monitoring/problem closed loop; the non-goals are explicit; the loop and its
separate states are recorded; UNKNOWN/STALE are honest; Observer is read-only and writes
only through separately authorized Control; AAOS keeps formal knowledge review and
acceptance; cross-project memory/session federation/autonomous Agent collaboration are
frozen or deferred; no parallel ledger; no dirty work overwritten; no test or feature
overclaim.

## 6. Freeze of other tasks

| Scope | State | Effect |
| --- | --- | --- |
| WUI-00..WUI-21 and all rows in the open register other than this convergence task | FROZEN_20261019 | No dispatch, no status rewrite, no evidence-free closure. Recorded statuses stay as they were. |
| Prior UI taskpack `WORK-LAB-UI-PRIORITY-TASKPACK-20261009` | SUPERSEDED_20261019 / FROZEN | Kept for history; no longer CURRENT. |
| Historical taskpacks, handoffs and blueprints | FROZEN_HISTORY | Non-normative; do not reopen by name alone. |
| Future capabilities in the roadmap | FROZEN or DEFERRED per roadmap | Unfreeze only through the roadmap gate and a new explicit user decision. |
| Product implementation of the minimal loop | DELIVERED (2026-10-19 user grant) | ML-001 one-file product fix; no further product work is authorized by this taskpack. |

## 7. Files changed by this task

- `WORK-LAB-AUTHORITY.md`
- `.project/governance/project-authority-index.json`
- `.project/governance/taskpack-authority-index.json`
- `taskpacks/current/WORK-LAB-AUTHORITY-CONVERGENCE-TASKPACK-20261019.md` (new)
- `taskpacks/current/OPEN-TASK-REGISTER.md` (header freeze notice only; rows preserved)
- `taskpacks/current/README.md`
- `taskpacks/history/pre-convergence-20261019/WORK-LAB-UI-PRIORITY-TASKPACK-20261009.md` (superseded banner only)
- `README.md`
- `docs/decisions/PROJECT_POSITIONING.md`
- `docs/current/authority-convergence-20261019/ROADMAP.md` (new)
- `docs/current/authority-convergence-20261019/AUTHORITY-CONVERGENCE-20261019.md` (new)
- `docs/current/authority-convergence-20261019/implementation/WORK-LAB-MINIMAL-LOOP-001-ACP-HERMES-RESUME.md` (new, implementation card)
- `docs/current/authority-convergence-20261019/solutions/SOLUTION-001-ACP-HERMES-RESUME.md` (new, first solution record)
- `services/execution-federation/hermes_adapter.py` (product fix: remove the unimplemented `Capability.RESUME` declaration)
- `.project-local/runs/authority-convergence-20261019/minimal_loop_readback.py` (new, adapter readback)
- `.project-local/artifacts/authority-convergence-20261019/minimal-loop/01-acp-honesty.out`, `02-federation-tests.out`, `03-nf22-tests.out`, `04-readback.out` (new receipts)
- `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 NEXT-AGENT-PROMPT） (freeze banner)
- `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 HANDOFF-20261018-QODER-SESSION） (freeze banner)
- `docs/current/workflow-assistance/workflow/active-authority-index.md` (current pointer)
- `docs/current/workflow-assistance/workflow/project-definition.md` (positioning supplement)
- `docs/current/DOCUMENT-CENSUS.md` (increment note)
- `docs/future/WORK-LAB-SUPER-ENTRY-COMMAND-CENTER-LAB-ROUTER-2026-09-27.md` (freeze banner)
- `docs/history/owner-inputs/20261019/WORK-LAB_权威收敛任务包_20261019.zip` (new archive)
- `docs/history/owner-inputs/RECORD-ARCHIVE-REGISTER.json`
- `docs/history/owner-inputs/RECORD-ARCHIVE-MEMBERS.jsonl`
- `docs/history/owner-inputs/RECORD-SOURCE-CENSUS.json`
- `scripts/maintenance/owner_material_catalog.py` (generated-index intro now points at the new CURRENT/roadmap/report)
- `scripts/audit/normalise_doc_citations.py` (default-load scope now follows the current bootstrap chain: convergence taskpack + report/roadmap; unused package-member allowance removed; verifier-output literal protected from mechanical rewrite)
- generated owner-material indexes (`docs/history/owner-inputs/INDEX.md`, `docs/history/owner-inputs/CATALOG.html`, CSV projections)
- `projections/agents/source/work-lab-workflow/SKILL.md` (default skill: new positioning, problem-loop state separation, current taskpack and freeze rule; v1.2.0)
- `.agents/skills/work-lab-workflow/SKILL.md` (regenerated projection, content hash updated)
- `config/skills-inventory.json` (regenerated: 8 of 19 stale hashes corrected from disk/HEAD, including this skill; no skill added or removed)
- `docs/history/archive/root-ui-records-20261019/ASSET_REPLACEMENT_MANIFEST.md`, `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip`（成员 HANDOFF-UI-L10B）, `docs/history/archive/root-ui-records-20261019/UI_DECISIONS.md`, `docs/history/archive/root-ui-records-20261019/UI_IMPLEMENTATION_REPORT.md`, `docs/history/archive/root-ui-records-20261019/UI_REFERENCE_MANIFEST.md`, `docs/history/archive/root-ui-records-20261019/VISUAL_QA_REPORT.md` (disposition banner authority chain only; body bytes outside the banner unchanged)

## 8. Verification

Executed commands, exit codes and the exact HEAD are recorded in the convergence report
§test report. Raw outputs and the machine receipt index are under
`.project-local/artifacts/authority-convergence-20261019/`; they are worktree gate receipts,
not exact-SHA CI. The 14 worktree gates pass (14/14); the report also records ten additional
read-only consumer checks. Of those, only one is red for a reason outside this task (drift in
the external source-inventory snapshot); the pre-existing ACP capability declaration mismatch
was fixed by ML-001 and its verifier now passes. The report states which items were not
executed and why.

## 9. Rollback

Revert only this task's files to the pre-task bytes; do not use destructive repository-wide
reset/clean. The prior UI taskpack and all historical records remain in place, so restoring
them as current is a matter of reverting the authority/index pointers and the freeze
banners. The new owner-material archive and register rows are additive and can be removed
as a unit if the archival decision is withdrawn.

## 10. Next step

The minimal loop in §4 is delivered (ML-001 / SOLUTION-001). Remaining steps require owner action:
confirm the result, then authorize commit/push so exact-SHA CI can judge the product change.
Any further loop or system capability needs a new explicit user Task Grant; until then all other
work stays frozen and this taskpack remains the only current plan.

## 11. Amendment 2026-10-19 — archive normalization (user directive)

**Directive (verbatim):** “任何旧的过时的冗余的陈旧的，不要再明面上，全部归档到该去汇总的地方，
包括仓库目录文件夹整体搬走，要么压缩归档到历史里。我描述不准确，按照规范化处理，防止再次索引路径到旧资料上”。

This is an amendment to this CURRENT taskpack, not a second task truth: no register row is
closed, reopened or rewritten in status, and no other work is unfrozen.

**Normalization target (existing conventions):** documents under `docs/history/archive/`,
taskpacks under `taskpacks/history/`, evidence under `reports/` and `docs/audits/`, external
copies under `knowledge-staging/`. Moves are `git mv`; nothing is deleted and no historical
body is rewritten.

**Executed moves — 54 items**, all recorded with `from`/`to`/`sha256`/`bytes`/`lastCommit` in
`docs/history/archive/MOVED-PATHS-20261019.json`:

| Group | Count | Destination |
| --- | --- | --- |
| Root UI records (six `.md` + `design.qa.yaml`) | 7 | `docs/history/archive/root-ui-records-20261019/` |
| Frozen UI round directory (formerly under `docs/current/`, named ui-priority-20261009; backticks in this repo mean "resolvable path", so the old name is written bare) | 20 | `docs/history/archive/ui-priority-20261009/**` |
| Non-current `taskpacks/current/**` (all but register, README, error ledger, this taskpack) | 23 | `taskpacks/history/pre-convergence-20261019/**` |
| Module instructions file (formerly at the `docs/current/` root, named workflow-assistance-AGENTS.md) | 1 | `docs/history/archive/workflow-assistance/module-instructions-20261019.md` |
| Two dated workflow records | 2 | `docs/history/archive/workflow-assistance/{handoffs,audit}/` |

Resulting surfaces: `taskpacks/current/` = 4 tracked files; root Markdown = 5
(`authority=2`, `convention-current=3`, `historical-non-normative=0`); `docs/current/` = 40 md.

**Consumer repointing.** Every active index and consumer was repointed in the same change:
the two governance indexes, `WORK-LAB-AUTHORITY.md`, the open register, `docs/current/**`,
`docs/decisions/**`, `docs/future/**`, Observer design contracts and tests, path constants in
`packages/client-neutral-core/scripts/`, and the anchors/default targets in
`scripts/ci|audit|maintenance`. Frozen `original-tree/**` bytes and the error ledger's historical
citations are deliberately unchanged.

**Fixture changes.** The uppercase-filename falsifiers in
`tests/workflow-assistance/test_control_service.py` and
`tests/workflow-assistance/test_path_text_is_one_predicate.py` no longer depend on a root UI
record: the control-service case now uses root-level `NOTICE.md` (`docs/` is a non-diffable root),
and the predicate case uses the nested archived path and asserts the nested relative result.
`tests/workflow-assistance/test_refs_surface_policies.py` and `tests/workflow-assistance/test_root_document_dispositions.py` use `NOTICE.md` as the
non-authority example.

**Re-index prevention.** `scripts/ci/verify_stale_surface_paths.py` reads the move map and fails
if any old path appears on an active surface. Frozen history, evidence, `knowledge-staging/` and
`.workbuddy/` are out of scope; `taskpacks/current/error-ledger.json` and `AGENTS.md` are named
allowances that must still be used. `tests/ci/test_stale_surface_paths_are_gone.py`
proves the gate reds on a planted old path and reds on an unused allowance.

**Files changed by this amendment:** the 54 moved paths above; the governance indexes and
consumer files listed in `docs/history/archive/MOVED-PATHS-20261019.json`;
`.project/governance/root-document-dispositions.json`; `scripts/ci/verify_root_document_dispositions.py`;
the four test files named above; `scripts/ci/verify_stale_surface_paths.py` (new);
`tests/ci/test_stale_surface_paths_are_gone.py` (new); `docs/current/DOCUMENT-CENSUS.md`
(§4, §7, §9, §10 and new §11); and this section.

## 12. Amendment 2026-10-19 (second) — consolidate, then delete (user directive)

**Directive (verbatim):** “旧交接和一些提示词的资料 汇总到一起归档后 就删除了吧”. This overrides the
standing "archive, never delete" convention for the named class only, and only because the bytes
are proved to survive elsewhere first.

Measured result: 91 tracked files matched the handoff/prompt name patterns inside
`docs/history/` and `taskpacks/history/`; **52** were consolidated into
`docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip` (first batch: 484,845 B of content, 263,031 B archive,
sha256 recorded in `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019-MANIFEST.json`) and then
`git rm`'d; **4** were kept because a machine pointer or a piece of code reads them by path
(`staticHandoffViews[].entry_record`, `frozenTaskCards[].path`, the citation auditor's fixture name,
and `scripts/ci/generate_current_state.py`'s source list); **35** were excluded by rule -- the byte-frozen
`original-tree/**`, owner inbound records and recovered last copies, imported `session-history/**`,
and the `reports/` + `knowledge-staging/` evidence and third-party-copy surfaces.

Proof before deletion: the manifest records `path`/`bytes`/`sha256`/`crc32` per member, the builder
reopened the archive and compared each member against both its own recorded hash and the bytes on
disk (52/52), and only then did `git rm` run. Recovery is either unzipping at the repository root
or reading the file from Git history, since these were committed before removal.
`tests/ci/test_stale_surface_paths_are_gone.py` asserts the archive's recorded sha256 against the
shipped bytes, every member's hash/size/CRC32, and that no member is still tracked or still on disk.

25 live citations were repointed to the archive with the member named in place, and the generated
owner-material index now routes its "UI 历史交接" row to the manifest. Post-deletion surfaces,
measured with `git ls-files -z`: 2,550 tracked, `docs/history/` 167 md, `taskpacks/history/` 108,
`docs/current/` 40 md, `taskpacks/current/` 4, repository root 5 md.
**One gate stays red, named and attributed (not worked around):**
`tests/workflow-assistance/test_project_local_citation_audit.py` reports `unadjudicated != 0` on a fresh
scan. Evidence gathered this run: the shipped record's `generatedAt` is 2026-10-10T14:38:39Z（counts.unadjudicated=0, reviewQueue=8, presentOnThisMachine=309） with
`counts.unadjudicated=0`, `reviewQueue=8`, `presentOnThisMachine=309`, last committed in 5f14677d;
the test's corpus is the whole git-ignored `.project-local/` tree (nine days of runtime residue from
several sessions, including this round's scratch scripts), so the drift is not produced by the tracked
changes in §11/§12. The test is not registered in CI -- neither `.github/workflows/` nor the
`services/orchestration/run_quality_gate.py` stage map names it. The audit script also mutates: it disposes
`.project-local/runs/...` directories and rewrites the tracked record; one run this round corrupted that
record and it was restored by bytes. Owner decision needed: reissue the derived audits in the documented
order together with a runtime-residue cleanup, or register the gate, or record it as a local observation.
**First exact-SHA CI verdict after this amendment, and the fix:** pushing `249e5fea` made
`work-lab-gate` run 39226565397 report `aggregate=failure`; the only red module was
`workflow-assistance` -> `test_the_shipped_inventory_describes_the_tree` (gate-plan,
supply-chain-security, integration, observer and token-monitor all success). Cause: the derived
inventory `docs/audits/TOOL_INVENTORY_2026-10-07.json` stores each tool's git-index blob sha256, and
nine `scripts/audit|maintenance` tools edited by §11/§12 still carried their old hashes. Fixed by the
tool's own ordering rule (ERR-151: stage, then re-measure, then commit): after staging,
`scripts/audit/tool_inventory_readback.py` produced `trackedTools=77 withLedgerPromise=19
referencedSomewhere=77 unclaimed=0` and `tests/workflow-assistance/test_tool_inventory_coverage.py`
re-ran `Ran 12 tests / OK`. The new stale-path gate is outside that inventory's scope (it covers
`scripts/audit` and `scripts/maintenance` only); it reaches CI because
`tests/ci/test_stale_surface_paths_are_gone.py` is discovered by `scripts/ci/run_root_governance_suite.py`.
**A clean-checkout reproduction found two defects in the new control itself, both fixed here.** To avoid
declaring green from local-only evidence, a detached worktree with no `.project-local/` was created and
the six targeted modules re-run there. It immediately reported one failure: the move record's `sha256`
values were computed over **worktree bytes**, while `.gitattributes text=auto` stores LF and checks out
CRLF on Windows, so the two CSVs edited this round could never match on a fresh checkout. Fix: measure the
git blob (`scripts/ci/verify_stale_surface_paths.py:tracked_blob`, via `git show HEAD:<path>`), compare the
record against the blob, and additionally assert that the worktree text equals the blob text modulo line
endings — the only cross-host claim is "the words did not change". Second defect found in the same pass:
regenerating the record reset the named allowances' `minOccurrences` back to hand-written constants (19 and
12) while the measurement is 8 and 6, so the gate convicted itself with `ALLOWANCE_UNMET`; the generator now
calls the gate's own `--write-allowances` after writing, making the minimums a measurement instead of a
constant. The clean worktree then re-ran `Ran 16 tests / OK`.

## 13. Amendment 2026-10-19 (third) — owner authorized the pointer changes

Recorded verbatim from the owner's answers this round: for `AGENTS.md` lines 12 and 16 the answer was
**“授权改这两行”** (authorized to change those two lines), and for the four handoffs kept because a
machine pointer named them the answer was **“删文件并同步改指针”** (delete the files and move the pointers
in the same change). The standing "archive, never delete" convention is overridden for these named
objects only; this is a per-decision authorization, not a new permanent rule.

`AGENTS.md`: the section heading now reads 当前任务范围更新（用户2026-10-19明确决定，取代2026-10-09的UI优先范围）,
the only CURRENT points at this taskpack, and the UI-round handoff routes to `docs/history/archive/HANDOFFS-AND-PROMPTS-20261019.zip` with the member named
in parentheses. Every rule from that section that is still in force (default main line, no mobile work,
HUD as a desktop overlay, single-writer and privacy rules preserved) was carried over verbatim -- fixing a
stale pointer is not a licence to weaken a rule.

Pointers moved: the `staticHandoffViews` entry for HERMES-UPDATE-HANDOFF-20260927 and the `frozenTaskCards`
entry for WORK-LAB-UI-PROMPT-PACK-EXECUTION-TASKCARD-20261007 were removed from
`.project/governance/taskpack-authority-index.json`; the dead `taskpacks/current/` entry in
`scripts/ci/generate_current_state.py`'s source list was dropped -- it had been silently skipped by an
`is_file()` filter, which is the "one evidence source went missing and nobody was told" shape.

**The archive builder had to become cumulative (second self-inflicted defect this round, fixed).** It
originally rewrote the archive from whatever matched today, so when the first 52 documents were already
untracked it produced a 6-member archive: had that been committed, the byte-preservation promise for the
first batch would have been silently void. The builder now reads the shipped archive and manifest,
re-verifies every carried member by sha256 and size, copies those bytes forward untouched, appends the new
additions, refuses to shrink, and excludes the archive and its own manifest by name from the candidate set.
Shipped state measured: **56** members (52 carried forward + 4 added), 492,296 B of content,
268,142 B archive, sha256 `1b1effdf7f80128b4007181dbc7fdb1af01d0776db9ce5f26eb8199d93503347`. The
destructive rewrite was reverted by bytes with `git checkout --` and redone.

Four allowances expired rather than being loosened: the two `AGENTS.md` named allowances in
`docs/history/archive/MOVED-PATHS-20261019.json`, the two rows in
`.project/governance/live-doc-path-exceptions.json`, the two `QUOTED_AS_ABSENT` entries in
`scripts/audit/normalise_doc_citations.py`, and the two `AGENTS.md` rows in the ratchet baseline. The
stale-path gate went from 8 allowances to **4** and reports
`STALE_SURFACE_PATHS_PASS scanned=1289 enforced=104 allowances=4 taskpacks/current/error-ledger.json=8 tests/ci/test_project_authority_reference.py=2 tests/ci/test_stale_surface_paths_are_gone.py=10 tests/workflow-assistance/test_project_local_citation_audit.py=1`; the baseline reissued at 293 rows.
`tests/ci/test_stale_surface_paths_are_gone.py` gained a case asserting the four paths are archive members,
absent from the tree, and named by no entry in the machine index.

Surfaces after this amendment, measured with `git ls-files -z`: **2,548** tracked, `docs/history/` 167 md
(unchanged -- all four deleted documents lived under `taskpacks/history/`), `taskpacks/history/` **104**,
`docs/current/` 40 md, `taskpacks/current/` 4, repository root 5 md. The re-index gate reports
`STALE_SURFACE_PATHS_PASS scanned=1289 enforced=104 allowances=4 taskpacks/current/error-ledger.json=8 tests/ci/test_project_authority_reference.py=2 tests/ci/test_stale_surface_paths_are_gone.py=10 tests/workflow-assistance/test_project_local_citation_audit.py=1`, and 106 targeted test cases across eight
modules ran green.
**The gate was extended in the same pass.** `old_patterns()` consumed only the record's `from` paths, so a
pointer at a document that now survives only as an archive member was invisible. The consolidation's 56
`deletedPaths` are enforced too (48 -> **104** patterns), the required gate grew from 16 to **18** cases --
one plants a deleted-member path and must convict, one asserts the live tree names none -- and the
population test recomputes its expectation from the record instead of a literal, so growing the record
cannot leave the gate describing an older world.
