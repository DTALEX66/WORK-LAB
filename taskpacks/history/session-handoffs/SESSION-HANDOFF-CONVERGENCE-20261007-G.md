# SESSION HANDOFF — CONVERGENCE 2026-10-07 (rounds F and G)

Read this one first: it is later than `SESSION-HANDOFF-CONVERGENCE-20261007-D.md` and supersedes
its "what is owed" list where they disagree. Round D/E content is not repeated here.

## Objective status after these two rounds

| Objective item | State | Evidence |
|---|---|---|
| 开源候选池真实吸收/迁移/退役 | closed 2026-10-07 (round D) | registry + `verify_future_candidate_registry.py` falsified 10/10; ERR-126 |
| AG-19 缺失原件恢复 + Source Registry | closed with honest remainder (round C) | `.project/governance/recovered-source-registry.json` + gate; ERR-125 fixed the digest basis |
| 模型与工具入库 | closed for the model half (round D/E); tools deliberately not installed | `scripts/audit/model_library_readback.py`, `docs/audits/MODEL_LIBRARY_READBACK_2026-10-07.md`, AG-05g gate falsified 14/14; ERR-127 |
| 本仓库绿色化与外溢数据可追踪 | 116 MB released with 0 cited paths lost; three obligations open | `docs/audits/RELEASED_BROWSER_STATE_2026-10-07.json`; ERR-129 |
| AG-11 OCR/ASR 矩阵 | **measured 2026-10-07** (round G) | `docs/audits/AG11_OCR_ASR_MATRIX_2026-10-07.json` + `test_ag11_matrix_evidence.py` |
| 持久记录可复现性 | every ledger promise now resolves to a tracked file | `tests/workflow-assistance/test_error_ledger_regression_commands.py`; ERR-130 |
| AG-09/10, AG-12/13/15/16/17/18, U02 publish | owner-side or human-verified, unchanged | register rows; skipped per the standing "真人操作先跳过" instruction |

## Round G — AG-11 got measured rather than re-described

The gap had stood for nine days as "weights exist; existence verified, quality not". Both halves
turned out to be reachable with no download and no GUI: LM Studio is live on `:1234` serving the
registered `qwen2.5-vl-7b-instruct`, and the registered faster-whisper weights load in-process on
CPU. `scripts/audit/ag11_ocr_asr_matrix.py` runs nine cells; the measured result:

- OCR probe recovery, all cells 100%: mixed zh/en page 11/11, the same page degraded to a
  0.5×/JPEG-q32/blurred "scan" 11/11, Chinese-prompt 4/4, English-prompt 4/4, PDF page 8/8
  (probes read mechanically out of that page's own text layer), synthetic 5×3 CJK table 15/15,
  three-page ordering 3/3 with the order preserved. Roughly 6-7 s per call.
- ASR: the synthesised 4.12 s fixture transcribed with `character_error_rate 0.0`, 5.05 s of work
  → `real_time_factor 1.23`. The vendor zipformer wavs have no transcripts, so those runs are
  recorded as `MEASURED_NO_TRUTH` with their transcripts and durations — no quality number is
  claimed from them, and the objective's "unknown stays unknown" holds for real-user audio, which
  this machine does not have.
- New project-local environment `.project-local/toolchains/wl-ag11` (272,004,834 B: pillow,
  pypdfium2, faster-whisper). Inside the project root, nothing elsewhere.
- The gate re-derives the numbers instead of trusting the status word: an inflated hit rate, hits
  above probes, a score on a ground-truth-less run, a missing cell, a reasonless skip, a failed
  cell, a real-time factor that does not follow its own seconds, and a stale summary are each
  rejected (10 cases, 8 negative controls), discovered by the governance group.
- One honest correction during the run: the first pass reported the PDF cell FAILED because this
  pypdfium2 version exposes `get_text_range()`, not `get_text_broad()`; and the failure was
  labelled with the function name instead of the cell id. Both fixed, and the re-run is the
  artifact above. My first probe of the library also failed on `pypdfium2.__version__`, which is
  not an attribute — the dependency was installed and working.

## Round F — what a "regression command" is allowed to mean

`command` is history; `lifecycle.regressionCommand` is a promise. 17 of 43 promises pointed into
the git-ignored runtime root; 17 instruments are now tracked under `scripts/audit/` and
`scripts/maintenance/`, each entry keeping its original string in `regressionCommandPrior` with a
dated note, and a gate refuses an untracked, `.project-local`, dropped or undated promise. Two
"broken" paths I first reported were my own scanner double-applying a `cd` prefix — reverted, and
the lesson is in ERR-130.

## Still owed, with the numbers attached

- 28 tracked documents cite `.project-local` paths that no longer exist (enumerated in
  `docs/audits/RELEASED_BROWSER_STATE_2026-10-07.json`): restore, re-point, or mark absent — per
  path, on evidence, never by deleting the record.
- The scratch originals behind the promoted tools are still on disk; they can go once the
  re-pointed commands have survived a cleanup cycle.
- `toolchains/lambda/llama-b11221-bin-win-cuda-12.4-x64.zip` (253 MB) — release candidate after an
  extraction-completeness check.
- `source-ledger.json`: 17 rows still `license: UNKNOWN` besides `agent-skills`, each with a
  `review-required` trigger; the pool item is closed, this one is a per-row review.
- ASR on real user material, and OCR over multi-page PDFs (`page-order` used three synthetic
  pages, and `governance.pdf` is single-page): both stay UNKNOWN until material exists.
- U02 publish, AG-09/10, AG-12/13/15/16/17/18 owner decisions, the writable Control Surface, the
  owner's on-screen desktop check.

## Verification discipline in force

Pre-push validation is `scripts/ci/reproduce_ci_commands.py` (both workflow files, 107 interpreter
commands, non-reproducible steps named as `CI_CONTEXT`/`STEP_ENV`/`TOOL_NOT_ON_PATH`), and the
receipt file — not the wrapper exit code — is the verdict. Exact-SHA CI is read from the remote ref
by `.project-local/runs/convergence-20261007-d/watch_exact_sha_ci.py`. Heads pushed and green:
`08ca2e6` (ALL_SUCCESS 24), `e0b296d`, `9af7c16`, `5c6bfe9` (in readback). No merge, no release,
no tag: the owner forbade publishing.
