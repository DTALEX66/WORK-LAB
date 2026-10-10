# SESSION HANDOFF — CONVERGENCE 2026-10-07 (round D)

Position at the end of this round. Read this before the older handoffs; it supersedes their
"what is owed" lists where the two disagree, and it records one thing I got wrong earlier.

## What this round proved

**CI was red because of my own digest basis, not the repository.** `workflow-assistance` failed at
`1cffd9f`, `e7ede1f` and `ab33537` with `src-brand-observer-icons.svg drifted from its recorded
digest`, while the identical 45-command step list passed 45/45 locally at the same head. Cause: the
recovered-source registry recorded sha256 over **working-tree** bytes, and `.gitattributes` carries
`* text=auto`, so the same commit is CRLF on this machine and LF on the runner. Three of six tracked
entries recorded digests that could only ever match here. Fixed forward in `71c6a9c`: tracked entries
now record the blob at HEAD, the gate hashes the blob, `digestBasis` declares the rule, and a new
test executes each recorded `git cat-file -p 6de25fe:<original path>` command and requires it to
reproduce the recorded digest and the HEAD blob — which turns `byte-identical` from an adjective into
a computed relation (verified for all five brand files). ERR-125. Falsified 5/5: a CRLF→LF flip of
the working tree must stay **green** (that is the portability property), and digest drift, size
drift, a bogus recovery commit and a removed recovery command each turn their named case red.

**The candidate pool is now decided, not just deferred.** All 22 rows over the 19 landed §16 rows
carry a discovery readback, an absorption level, repository paths as evidence and a decision:
**15 REJECT, 7 KEEP_CANDIDATE, 0 PROMOTED**. Nothing was promoted because no candidate has pilot
evidence, and promotion by editing a status word is the failure mode this file exists to prevent.
Identities came from the GitHub API on 2026-10-06 (13 RESOLVED, 7 AMBIGUOUS, 2 NOT_FOUND) and the
licence recorded is what the readback returned — `UNKNOWN` and `NOASSERTION` are results, not
blanks. Three pre-existing registry/code contradictions were corrected: OpenHands' role already
exists as an honest fleet adapter (default not launchable), Hindsight already exists as a POC on the
unified nine-operation memory contract, and n8n is already barred in code as a fourth task core
(`thin_deployment.FORBIDDEN_TASK_CORES`, asserted by `nf11`). ERR-126, with the original failure
reproduced: the previous verifier caught **0 of 10** injected lies on the same registry.

**The gate now refuses specific lies.** `verify_future_candidate_registry.py` hard-fails on a
decision missing or disagreeing with the status word, a RESOLVED row without an org/repo and the
licence returned, an AMBIGUOUS/NOT_FOUND row claiming a verified licence, `windows_support=VERIFIED`
without the artifact that proved it, any `native_evidence` path that is not on disk (55 distinct
paths, all present), absorption claimed with no path, `status=PILOT` with `absorption=NONE`,
KEEP_CANDIDATE with no blocker, REJECT with no reason, a placeholder word (TBD / not yet assessed /
recorded at DISCOVER) in any trigger, criterion or overlap field, and `governance.decisions` drifting
from the enforced vocabulary. Schema and contract updated to match.

## Second half of the round — 模型与工具入库

**A recorded hash is only evidence if it says what it was taken over.** Nine of ten models in
`.project/governance/model-registry.json` carried a 64-hex `sha256` and health words like
`DOWNLOADED_HASH_VERIFIED`, and `verify_model_registry_integrity.py` checked the *shape* of those
values and passed — a digest copied back from an upstream page was indistinguishable from one
recomputed on this disk. New tool `scripts/audit/model_library_readback.py` re-hashed the declared
root: **48,531,408,516 B (45.20 GiB) over ten entries, nine digests matched**. The directory-backed
zipformer entry now carries twelve per-file digests instead of one truncated prefix claim. It is
deliberately **not** wired into the aggregate gate: the runner has no weight root, and AGENTS.md
says a required job that can only skip fails the aggregate — so the CI-side gate checks the claim's
internal consistency (check 7, AG-05g: presence, digestState, bytesObserved, dated basis, tool; a
RECOMPUTED_MATCH must equal the recorded `sha256` and agree with `file.bytes`) and the on-machine
tool produces the numbers, failing closed if its root is missing.

Three findings came from measuring rather than reading:

- The two `RETIRED_PENDING_DECISION` weights **are on disk** (5,225,374,496 B and 18,556,688,736 B,
  each blob hashing to its own content-addressed name). The registry now records `bytesRetained`
  beside each, so an open decision stops looking free.
- `runtimes-tmp/reranker-dl.gguf` is the same byte length as the registered reranker weight but has
  a different full digest — so it is **not** a duplicate, and the owner rule (deletion only after a
  confirmed duplicate plus a rollback point) does not authorize removing it. The row had implied it
  was a deletable leftover.
- One `candidateOrphans` row asserted 3,389,971,840 B of retained fragments behind a path written as
  prose (`sha256-81fb60c7…-partial (+16 zero-length part files)`), which no tool can open. It is now
  `UNRESOLVABLE_AS_WRITTEN`: the honest verdict is "unverifiable as written", not "proven absent".
  And a 5,969,233,408 B ollama weight layer for the `qwen2.5vl/7b` family belonged to **no entry at
  all** — now registered, content address verified, and left in another runtime's store.

**No tool was installed for the tool half of the item.** `docs/current/workflow-assistance/workflow/wloss-reference-decisions.md`
records each `source-ledger.json` tool (OPA, conftest, trivy, actionlint, zizmor, cosign, promptfoo,
mcp-inspector, superpowers, agent-skills) as deliberately REFERENCE-only with its own trigger
condition, and the compatibility policy declares no licence allowlist. Nothing in a gate or an open
task lacks one of them, so "缺工具就下载到工具库里" has no subject here and inventing an install
would have been the failure. The real residue in that file is still owed: all 17 rows carry
`license: UNKNOWN`, and its `agent-skills` canonicalUrl (`https://agent-skills.org/`) could not be
verified — the specification resolves at agentskills.io.

ERR-127; the new rules were falsified 14/14, and the same harness run against the committed
verifier is recorded as the reproduced original failure: **0/14 caught**.

## The mistake worth carrying: I validated part of CI and called it CI

Pushing `8c78b0d` turned the **integration** job red in 17 seconds: `Additional properties are not
allowed ('identityReadback' was unexpected)`. I had added a readback field to the agent-skills row
in `.project/governance/source-ledger.json`; `verify_source_ledger_v4.py` passed it because it does
not enforce the closed property set, and the CI-invoked `verify_source_ledger.py` validates against
`.project/governance/contracts/source-ledger.schema.json`, which declares
`additionalProperties: false`. My pre-push check had reproduced the 45 commands of the
workflow-assistance STEP and nothing else.

This is the third occurrence of one shape in this session — ERR-109 (a pinned command count inside
a required group), ERR-125 (a digest basis only the runner could contradict), and now this. The
cause is not the field or the hash: it is treating a slice of the CI command set as the whole.
`scripts/ci/reproduce_ci_commands.py` is now the durable answer: it parses BOTH workflow files with
a YAML parser, splits each `run:` block the way a shell groups statements (continuations and quoted
multi-line arguments), honours `working-directory`, and classifies what it cannot reproduce by name
— `CI_CONTEXT` for steps whose command or `env:` map comes from `github.*` or a previous job's
output, `STEP_ENV` for commands referencing a variable the runner exports, `TOOL_NOT_ON_PATH` for
cargo/npm on a machine that has them elsewhere. 107 interpreter commands across the two workflows;
the integration job alone contributes 12 that my earlier harness never ran. Everything still failing
locally is environmental, and each is named as such rather than passed off: cargo absent
(`observer-desktop-crate`), no local `app.exe` for the artifact receipt, the U19 WebView2 E2E needing
a real desktop, and `tests/ci` inline commands that read the UTF-8 default the Linux runner has while
this console is GBK.

The provenance I wanted to record did not get thrown away either: it moved into `integrationNote`,
a field the contract allows, keeping the previous URL, the readback command and the date. ERR-128.

## Round E — the greening residue, done by class rather than by directory

Two defects met in the same place. Durable records (four `error-ledger.json` entries, three
register rows) gave `regressionCommand` values starting with `python .project-local/runs/<scratch>/…py` —
a reproduce path inside the git-ignored runtime root, which the cleanup rounds themselves delete.
And the trees that greening had *retained* because one file inside them was cited turned out to be
mostly not evidence: **116,216,094 B across 1,395 files** were WebView2 and headless-Chrome
user-data (`EBWebView-cdp-*`, `EBWebView-final-*`, `l10b-verify/chrome-profile`).

- Five probes (62,484 B, 1,485 lines) copied byte-for-byte into tracked `scripts/audit/`, with
  both-side digests and the count of durable records naming each old path in
  `docs/audits/PROBE_TOOL_PROMOTION_2026-10-07.json`. Originals stay until the records are
  re-pointed, so nothing is orphaned in either direction.
- The release ran behind four guards (browser-name pattern plus two profile markers, outermost
  match only, no cited path inside a deletion target, and a re-check of every tracked-referenced
  `.project-local` path afterwards): **0 cited paths lost**. Measured after: p0c-oracle 154→112 MB,
  p0c-final 33→1 MB, ui-suite 71→34 MB.
- Retained **with sizes and reasons**: `u19-msvc-20261006` 1.39 GB (cargo target holding the release
  binary the U19 desktop evidence refers to, cited 14×), `imported-from-workbuddy-20261006` 453 MB
  (the only surviving copy of another agent's worktree evidence — 2,309 files verified identical at
  import, source retired; it is an original, not a cache), `dsh-backup-pre-deploy` 225 MB (rollback
  point), `toolchains/lambda` 843 MB (the installed optional llama.cpp runtime; only its 253 MB
  source archive is a candidate, pending an extraction-completeness check), `wl-py311` 22 MB (the
  gate's own dependency).
- Found and *not* papered over: **28 tracked documents cite `.project-local` paths that no longer
  exist** (some traceable to the six files lost to the ERR-123 bug). That is a traceability defect
  owed its own pass — the post-check's raw count was 37, of which 9 were my own regex eating
  trailing punctuation.

Pre-push validation was the new `scripts/ci/reproduce_ci_commands.py`: 86 commands run across both
workflows, 4 failures, all four classified as local-environment (cargo not on PATH, no
`app.exe` at the default target dir because the MSVC build used a separate `CARGO_TARGET_DIR`, the
U19 WebView2 E2E needing the real binary, and the workflow's inline `python -c` JSON-schema check
reading UTF-8 files with Windows' GBK default). 21 commands reported `CI_CONTEXT`/`STEP_ENV`/
`TOOL_NOT_ON_PATH` rather than being quietly dropped. ERR-129 records the round; commit `473a3f9`
carries it (one-line subject — the message body lives in the two audit manifests, and the commit was
already pushed so it was not amended).

## What is owed after this round

- **Finish the command re-pointing.** The five promoted probes are copies; four `error-ledger.json`
  entries and three register rows still name the `.project-local/runs/...` path. The mapping with
  digests is in `docs/audits/PROBE_TOOL_PROMOTION_2026-10-07.json`; the remaining step is a dated
  correction inside those records (keep the original sentence, add the tracked command), after
  which the scratch originals can be released with their own manifest.
- **28 stale citations** from tracked documents into `.project-local` paths that do not exist,
  enumerated in `docs/audits/RELEASED_BROWSER_STATE_2026-10-07.json`. Each needs the same choice:
  restore, re-point, or mark historically absent. Do not close it by deleting records.
- `toolchains/lambda/llama-b11221-bin-win-cuda-12.4-x64.zip` (253 MB) is the next plausible
  release — an installed runtime plus its own source archive — after checking extraction
  completeness and that `runtime-registry.json` still resolves.
- **FUT-001 Orca pilot** — still the only external-workspace candidate, needs an owner-authorized
  pilot on a real external project *and* a launch path that does not exist in this repository.
- **Licence decisions for the owner**, not mine: OpenViking AGPL-3.0, EvoMap GPL-3.0, n8n fair-code.
  The repository declares no licence allowlist, so those questions stay visible.
- **`.project/governance/source-ledger.json`**: its `agent-skills` row is corrected (commit
  `e0b296d`: canonicalUrl → `github.com/agentskills/agentskills`, Apache-2.0 from the API readback,
  the unverifiable `agent-skills.org` kept inside `integrationNote`). Still open: all 17 rows carry
  `license: UNKNOWN` except that one, `windowsSupport: unknown`, and the row-level review each
  `review-required` entry asks for has not been done. The pool item is closed; the ledger item is not.
- **REQ-RANGE-20261007** — the byte-range artifact-slicing gap migrated out of the retired FUT-031
  row into a register row, because the missing piece is ours to write, not a project to import.
- U02's publish step (`sync_hermes_workflow_assets.py --apply`), AG-09/10/11 (inference path for
  AG-11 does not exist in any environment the gates can reach — see the register row), the writable
  Control Surface, and the real-desktop readback. The three retained large trees are resolved:
  116 MB of browser user-data released with 0 cited paths lost, the rest retained with sizes and
  reasons, and the leftover obligations are the three bullets above this list.

## Method notes worth carrying

- A local green is not a CI green when the claim is about bytes: run the **CI-invoked command list**,
  not the groups you touched. `.project-local/runs/convergence-20261007-d/ci_step_repro.py` parses
  one step out of the workflow and reports exit codes per command, so the check cannot drift from CI.
- When a script regenerates a governance file, keep every field it did not intend to change. My
  digest-rebind script overwrote `verificationCommand` and deleted the `6de25fe` recovery commands;
  `test_migrated_assets_record_where_they_came_from` caught it on the next run. The gate protected a
  claim I was about to destroy — that is the value of asserting on provenance text.
- Auditing a candidate pool means reading the registry **and** the code together. Every one of the
  three drifts above was visible only in the pair.
