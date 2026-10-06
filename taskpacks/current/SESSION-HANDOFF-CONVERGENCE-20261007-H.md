# Session handoff — convergence round H (2026-10-07)

Scope of this round: AG-11 measured, CI-command portability, the `.project-local` citation debt,
the llama.cpp archive, and the source-ledger licence review. Branch
`task-decomposition/atlas-gap-archive-20261001`, no merge, no tag, no release.

## What shipped, by commit

| head | what | state |
|---|---|---|
| `daeb76c` | AG-11 instrument + 9-cell evidence + re-deriving gate + round-G handoff | local gates green |
| `30802cc` | locale-independent CI command + locale gate, citation audit + gate, ERR-131/132, register rows | **CI RED — my gate's fault, see ERR-133** |
| `41858fe` | gate split into CI-stable agreement + named local skip; llama.cpp archive released on its extraction proof; ERR-133; AG-11 status column → PARTIAL | **CI ALL_SUCCESS, 24 runs** |
| `e6bb43c`…`522fe80` | licence values + LICENSE-byte hashes, ERR-134/135/136/137, U02 live-path re-point with the managed SKILL.md held back, canonical snapshot regenerated, scratch originals released, ledger fix-commit bindings, tool inventory | **CI ALL_SUCCESS, 24 runs at 522fe80** |

## What this round proved

- **AG-11 is measured, not asserted.** Nine declared cells against the live LM Studio serving of
  `qwen2.5-vl-7b-instruct` and in-process faster-whisper: OCR probe recovery 11/11, 11/11, 4/4, 4/4,
  8/8, 15/15, 3/3; ASR CER 0.0 at RTF 1.23; the vendor wav set recorded `MEASURED_NO_TRUTH`. The
  gate re-derives every rate from its own hits/probes and refuses a score on a no-truth cell.
- **A recorded CI command was passing by accident of platform.** `wlr-060 / Validate all JSON
  schemas` read five UTF-8-bearing schemas with the default locale encoding and fails outright under
  GBK (`byte 0x94`). The whole-workflow repro found it because it runs commands in a bare shell —
  which is the only reason it exists (ERR-128). It now states `encoding='utf-8'`, and a new gate
  refuses the class.
- **The "28 stale citations" figure was a scanner scope, not a debt.** 365 distinct `.project-local`
  tokens, 165 present, 200 absent across 265 citations. Reading the sentences: 183 frozen narrative,
  36 destinations a program will create, 15 negative assertions/removals, 7 placeholder patterns.
  Two sentences genuinely lied and are corrected in place with the original text kept:
  `error-governance.md` named a nonexistent error-ledger snapshot as a *Canonical file*, and the P0C
  handoff sent a reader to `.project-local/runs/p0c-diag-20261006` while the bytes live in the
  WorkBuddy import. The other 14 review-queue paths each carry a written disposition.
- **264,519,230 B released on a byte-level proof.** All 52 members of
  `llama-b11221-bin-win-cuda-12.4-x64.zip` matched the extracted tree by name+size+CRC-32
  (missing 0, disagree 0, treeOnly 0). Audit written before the delete; one named file removed;
  root re-measured 53 files/883,039,067 B → 52 files/618,519,837 B. `runtime-registry.json` already
  carried the archive's sha256 and byte count — recomputed this round and equal — so identity
  survived; only its free-text `status_note` changed, because the schema closes properties.
- **13 licence values from documents fetched this round, 1 deliberately still UNKNOWN.**
  `mcp-inspector`'s LICENSE contains MIT, Apache-2.0 and CC-BY-4.0 simultaneously during an
  in-flight relicensing — choosing one SPDX id is a legal decision, not a readback. The two
  self-owned rows stay UNKNOWN because the repo has **no** LICENSE file (`git ls-files` → 0) and no
  licence section in README; that is a measured answer, and it is the owner's to change. Two
  canonical URLs were replaced after upstream renames with the old values preserved in the note, and
  `otel-semconv` is a duplicate of `opentelemetry-genai-reference` — recorded, not silently merged.

## What this round retracted

- I wrote a CI-discovered gate that asserted the existence of a directory under `.project-local`.
  A clean checkout has no such root, so CI went red at `30802cc`. Reproduced in a detached worktree
  (`AssertionError: … the re-pointed evidence root is not on disk`), then split into an
  agreement-between-tracked-records test (unconditional) and a machine-local presence test with a
  named `skipUnless`. ERR-133.
- The same worktree exposed a bad instrument: a worktree nested **inside** the ignored root is not a
  clean-checkout simulation — the repo's own boundary guards threw 17 unrelated failures that belong
  to the simulation, not to the tree. Do not reuse that trick; read the runner log instead.
- My first citation scanner reported 200 "broken" paths; the classifier's destination bucket was
  under-filled (a regex that required the path literal to follow `=` immediately, missing `Path(`).
  Fixed before any record was written from the wrong number.

## U02 live-path convergence (same round)

The documents had never been re-asked after ERR-115: 104 command-shaped references in live surfaces pointed at paths that no longer exist, 77 of them mechanically re-pointable to a single tracked namesake, 29 kept with a written reason. `scripts/audit/live_doc_command_targets.py` (report + `--apply`) and `tests/workflow-assistance/test_live_doc_command_targets.py` now make that a machine check; ERR-135 records the unanchored-replace regression my first apply produced and how it was caught before commit.

## Still owed

- **Owner-side, unchanged:** U02 publish; AG-09/AG-10 (BLOCKED); AG-12/13/15/16/17/18 decisions; the
  writable Control Surface; the owner's on-screen desktop readback. `mcp-inspector`'s licence pick
  and whether WORK-LAB declares a licence at all are now also owner decisions.
- **U02 publish is PINNED, not vague (ERR-137):** `sync_hermes_workflow_assets.py --plan-json` (plan
  only, nothing written) refuses to publish because
  `skills/software-development/requesting-code-review` has unreviewed live content in Hermes Home —
  `live=a219c2579a2e9864` vs `candidate=abf9ca1b3549dc41`, `baseline=None`. Unlocking it means
  `--adopt-baseline --adopt-target <t>@<reviewed-sha256> --adopt-operator <name>`, i.e. a named human
  attesting they reviewed content I did not write. I did not adopt it and did not write to Hermes
  Home. Because of that same invariant, one managed `SKILL.md` re-point from the U02 document round is
  held back (restored to its 51c723d content; the re-pointed bytes are preserved at
  `.project-local/runs/convergence-20261007-h/project-data-boundary.SKILL.repointed.md`) and must land
  in the same change as the deployment, which is what refreshes the live hashes in
  `config/skill-provenance.yaml`.
- **Merge the duplicate row** `otel-semconv` into `opentelemetry-genai-reference` or retire one.
- **AG-11 real material:** ASR on a user recording, OCR over a multi-page PDF. Both stay UNKNOWN
  until the material exists; `page-order` used three synthetic pages.
- **Licence depth DONE 2026-10-07:** all 14 named rows are bound to the SHA-256 of the LICENSE bytes they were read from (`scripts/audit/licence_file_bytes.py`, 14/14 fetched, 0 failures), and the gate compares the ledger hash to the audit hash. Doing it exposed a self-contradiction in the shipped audit — prose said three file-confirmed rows, its own method fields said six — recorded as ERR-134 and reproducible against the committed blob. What is NOT closed: no row has a commit/tag basis, so `reviewedCommit` stays null and freshness stays `review-required`.
- **Scratch originals — closed as far as it is worth (2026-10-07):**
  `scripts/audit/scratch_promotion_redundancy.py` compares each scratch script against its tracked
  namesake by sha256 and releases only byte-identical copies: 5 released (27,147 B), proof per file in
  `docs/audits/SCRATCH_PROMOTION_REDUNDANCY_2026-10-07.json`. One file is DIVERGENT and kept
  (`runs/legacy-task-runtime/test_apply_safety.py` — neither copy contains the other, so deleting it
  would destroy a version). Deliberately retained: the 272 MB `wl-ag11` venv, because the AG-11 matrix
  cannot be re-run without it, and everything under `.project-local/artifacts/`, which is the evidence
  root AGENTS.md says to preserve — an identical digest does not make a rescue copy worthless.
- **Readback for `41858fe` and the licence commit** must be recorded in this file's table before the
  round is called closed.

## Retracted again, same shape (ERR-136)

I pushed 51c723d after running the gates I thought were relevant and skipped `scripts/ci/reproduce_ci_commands.py`. CI's integration job went red on `generate_current_state.py --check-current`: `.project/governance/generated/CURRENT_STATE.json` pins the digest of every CANONICAL_FILE, and source-ledger.json is one — so landing 14 licence hashes invalidates the snapshot, and no other verifier notices. Regenerated and committed with the change. The rule is now stated where it can be enforced by the next session: **repro before every push, read the receipt**.

## Ledger fix-commit binding (same round)

21 error records now name the commit that fixed them, each validated against that commit's tree rather than typed in; 8 more were recovered from commit messages that cite the ERR id, and 99 PASS records are publicly owed with a stated reason (their fixing commit never names the id, or several do). Inventing a SHA is what ERR-125/ERR-134 forbid, so they are listed instead. Two new gates hold the line: `test_ledger_fix_commit_binding.py` (10 tests, the owed set must match the ledger exactly so it can only shrink) and `test_tool_inventory_coverage.py` (11 tests, 33 tracked instruments vs `docs/audits/TOOL_INVENTORY_2026-10-07.json`, digests on the blob-at-HEAD basis). See `docs/audits/LEDGER_FIX_COMMIT_BINDING_2026-10-07.json`.

## AG-16 handback round-trip (same round, ERR-138)

The link AG-16 said had never been exercised has now been exercised once against the live local model server, and it refused — correctly. 7 cases in `docs/audits/AG16_HANDBACK_ROUNDTRIP_2026-10-07.json`: a bare model return is refused for the missing envelope; the same plan inside a real harness-supplied envelope is refused at the capability gate because the contract probes agent-operations (`publish`) and the registry advertises inference operations (`chat.completions`) — the two vocabularies never meet and no executor is registered under the first. Dedupe, blocking-before-authorization, and self-grant-ignored all behaved as specified. Nothing executed; the automatic connection is still AG-17/OD02. Two gate controls earned their keep on first run: an exact-word `AUTHORIZED` comparison hid the fixture case because the contract composes `AUTHORIZED_NOT_EXECUTED`, and a substring body check tripped on `/chat/completions`.

## Verification discipline in force

`python scripts/ci/reproduce_ci_commands.py --skip "pip install" --skip cargo --skip "npm ci"
--skip "npm run build"` then read
`.project-local/runs/ci/reproduce_ci_commands_receipt.json` — the receipt is the verdict, never the
wrapper exit code. Expect exactly three failures from those skips (no cargo, no binary, binary
older than `frontend/dist`); anything else is a repo defect. CI is read at the exact pushed SHA by
`.project-local/runs/convergence-20261007-d/watch_exact_sha_ci.py`. Interpreter:
`D:\All projects\OS External Configuration\ArcheAxis-Knowledge-OS-ci-venv\Scripts\python.exe` with
`PYTHONUTF8=1` and `PYTHONDONTWRITEBYTECODE=1`. Governance is now 187 modules — new
`tests/workflow-assistance/*.py` files are picked up automatically, no manifest edit.
