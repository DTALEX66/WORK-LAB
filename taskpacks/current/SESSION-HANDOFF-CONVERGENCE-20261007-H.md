# Session handoff — convergence round H (2026-10-07)

Scope of this round: AG-11 measured, CI-command portability, the `.project-local` citation debt,
the llama.cpp archive, and the source-ledger licence review. Branch
`task-decomposition/atlas-gap-archive-20261001`, no merge, no tag, no release.

## What shipped, by commit

| head | what | state |
|---|---|---|
| `daeb76c` | AG-11 instrument + 9-cell evidence + re-deriving gate + round-G handoff | local gates green |
| `30802cc` | locale-independent CI command + locale gate, citation audit + gate, ERR-131/132, register rows | **CI RED — my gate's fault, see ERR-133** |
| `41858fe` | gate split into CI-stable agreement + named local skip; llama.cpp archive released on its extraction proof; ERR-133; AG-11 status column → PARTIAL | CI readback in progress at the time of writing |
| (this round's tail) | licence readback landed in `source-ledger.json`, `docs/audits/LICENCE_READBACK_2026-10-07.json`, `test_source_ledger_licence_evidence.py`, LICENCE-20261007 row | governance 187 modules / 1,971 tests PASS locally; CI readback at its own head follows |

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

## Still owed

- **Owner-side, unchanged:** U02 publish; AG-09/AG-10 (BLOCKED); AG-12/13/15/16/17/18 decisions; the
  writable Control Surface; the owner's on-screen desktop readback. `mcp-inspector`'s licence pick
  and whether WORK-LAB declares a licence at all are now also owner decisions.
- **Merge the duplicate row** `otel-semconv` into `opentelemetry-genai-reference` or retire one.
- **AG-11 real material:** ASR on a user recording, OCR over a multi-page PDF. Both stay UNKNOWN
  until the material exists; `page-order` used three synthetic pages.
- **Licence depth DONE 2026-10-07:** all 14 named rows are bound to the SHA-256 of the LICENSE bytes they were read from (`scripts/audit/licence_file_bytes.py`, 14/14 fetched, 0 failures), and the gate compares the ledger hash to the audit hash. Doing it exposed a self-contradiction in the shipped audit — prose said three file-confirmed rows, its own method fields said six — recorded as ERR-134 and reproducible against the committed blob. What is NOT closed: no row has a commit/tag basis, so `reviewedCommit` stays null and freshness stays `review-required`.
- **Scratch originals** under `.project-local/runs/convergence-20261007-{d,e,f,h}` are still on disk
  (~40 scripts, plus the 272 MB `wl-ag11` venv). They may go once the promoted paths have survived
  one full cleanup cycle.
- **Readback for `41858fe` and the licence commit** must be recorded in this file's table before the
  round is called closed.

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
