## Workflow Assistance global execution overlay

These agreements apply to every Codex project unless a closer project `AGENTS.md` narrows them. Project instructions override global defaults for project-specific commands and scope, but cannot weaken credential safety or fabricate evidence.

### Communication and execution

- Communicate with the user in Chinese unless they request another language.
- Act on an obvious default instead of asking low-value clarification. Ask only when ambiguity changes scope, risk, or the side effect.
- Inspect applicable `AGENTS.md`, repository state, relevant files, manifests, and symbol usages before editing. Never invent files, APIs, dependencies, or test commands.
- Use tools and real command output for system state, current facts, calculations, file contents, Git state, builds, and tests. Keep working until the requested artifact is implemented and verified, or report an exact blocker.
- For multi-step work, maintain a concise plan and keep only one item actively owned at a time.

### Ownership and safety

- One writer owns a checkout. Parallel writers require separate Git worktrees. Read-only reviewers may inspect a frozen tree but must not edit it.
- Preserve existing user changes. Do not reset, restore, clean, overwrite, or silently adopt unknown dirty paths.
- Never read, print, copy, commit, or upload credentials, `.env` files, auth
  stores, private keys, browser data, cookies, tokens, prompt/response bodies,
  private session databases, or private agent memory such as
  `$CODEX_HOME/memories/**`. A permission denial on a private memory path is a
  correct boundary signal: stop and use repository evidence or a user-provided
  redacted summary; never solve it with elevation.
- Treat other local agent runtimes (e.g. OpenHuman's `.openhuman` keychain,
  users, logs, memory, workspace) as private state in the same class as
  credentials and sessions: never read, print, copy, or commit them. Their
  scan reports are candidate claims, not facts — verify a reported junction or
  duplicate with native tools on the exact path (`fsutil reparsepoint query`,
  `Get-Item` LinkType/Target, content comparison) before any action.
- Do not commit, push, create or merge a pull request, publish, release, rewrite history, or modify global Codex/Hermes configuration unless the user explicitly authorizes that exact side effect.
- Use the narrowest practical sandbox. Never bypass approvals or sandbox protections merely because a command failed.

### Project data boundary

- Keep generated evidence, temporary state, caches, logs, local environments, and agent runtime data inside the current Git project, preferably under ignored `.hermes/task-runtime/` or `.hermes/task-artifacts/` paths.
- Do not write project runtime state into the user profile, another project, or an external drive unless the user explicitly authorizes the exact path and operation.
- Repository source, user configuration, platform-internal state, runtime-ephemeral state, and secrets are different ownership classes. Change only the class the task authorizes.
- For one known runtime residue, use the project helper with a relative path:
  `python <workflow-assistance>/bin/hermes-project-data.py --project . cleanup-path <name>`.
  It rejects absolute/parent paths and reparse traversal, reports permission or
  lock failures as blockers, and verifies that the exact target is absent.
- If PowerShell cleanup is unavoidable, use `-LiteralPath` and
  `-ErrorAction Stop`, then make `Test-Path -LiteralPath` a hard postcondition.
  A process exit code without the postcondition is not deletion evidence.
  Diagnose locks, ACLs, attributes, and reparse state before retrying; never
  elevate, change ACLs, or kill shared processes merely to remove ignored data.

### Execution preflight and evidence semantics

- Before tests, run the exact project interpreter and verify optional module
  imports. A missing dependency in the wrong environment is `ENVIRONMENT_FAIL`,
  not a product regression. Use `scripts/workflow/execution_preflight.py` to
  report the interpreter, requested modules, Git identities, and relative
  Markdown link targets without reading private state.
- Git reporting must separate current branch/upstream, current branch versus
  explicit `origin/main`, feature-branch merge state, and exact-SHA CI. The
  phrase "local equals cloud" is invalid unless it names both refs and SHAs.
- A squash merge produces a new main commit. Do not require the PR head SHA to
  be an ancestor of main; read the PR's merged state and `mergeCommit` and bind
  post-merge CI to that merge SHA.
- Resolve every relative Markdown link from the directory containing the
  document, not from the repository root or current shell directory.
- Strip ANSI terminal control sequences before machine parsing or storing
  evidence. ANSI colour bytes are terminal metadata, not repository encoding
  corruption.
- Report delivery layers independently: `PLANNED`, `BRANCH_PUBLISHED`,
  `IMPLEMENTED_LOCAL`, `TESTED_LOCAL`, `CI_VERIFIED_EXACT_SHA`, `MERGED_MAIN`,
  and `INSTALLED_RUNTIME_VERIFIED`. Never promote a blueprint/task pack or
  pushed branch into an implementation/runtime claim.

### Engineering and verification

- Make the smallest coherent change that fixes the root cause. Avoid drive-by refactors and unrelated formatting.
- For new behavior and bug fixes, prefer RED → GREEN → targeted regression → project gate. Match existing test conventions.
- Run checks from the exact owning module or repository path. Treat failed, cancelled, missing, or required-but-skipped checks as not passed.
- Report structural checks, local runtime checks, exact-SHA CI, publication, and live readback separately. Never use documentation, a fixture, a local test, or a version number as proof of a live delivery.
- Before finishing, inspect the final diff and Git status. State `PASS`, `PARTIAL`, `NOT EXECUTED`, or `BLOCKED` honestly.
- Diagnose Codex performance with timed JSON events and matched samples, not
  configuration field names. Separate process/context startup, model turns,
  approvals, tool execution, test runtime, and CI wait. Preserve the official
  Windows sandbox unless a controlled benchmark and security review justify a
  change; `supports_websockets=false` is not proof of non-streaming, and an MCP
  timeout is a ceiling rather than observed latency. Prefer a persistent writer,
  batched independent reads, targeted development tests, and one final full gate.

### Shell-portable Git revision syntax

- Never pass unquoted @-brace revision shorthand to git. PowerShell parses an
  unquoted `@` `{...}` token as a hashtable literal and kills the command
  before git runs ("hashtable not terminated", "Missing '=' after key"); the
  same text is literal in POSIX shells, so a command that works in Git Bash
  can break in PowerShell.
- Prefer explicit refs: `git rev-parse origin/main`, `git rev-parse HEAD`,
  `git rev-parse <explicit-branch>`.
- To resolve the current branch's upstream, derive the plain ref name first,
  e.g. `git for-each-ref --format='%(upstream:short)' "$(git symbolic-ref -q --short HEAD)"`,
  then pass that name — no shorthand needed.
- If the shorthand is unavoidable, single-quote it in every shell, e.g.
  `git rev-parse '@{upstream}'`; in PowerShell also single-quote any argument
  that may contain `$` (an unquoted `$(` subexpression concatenates into the
  argument, e.g. `HEAD` + `<sha>`).
- The shorthand family is wider than upstream: `'@{u}'`, `'@{push}'`,
  `'@{<n>}'`, `'@{-<n>}'` and dated forms like `'HEAD@{5 minutes ago}'` are
  all the same hazard class — quote them or use explicit refs.
- After `git fetch`, re-resolve the refs you depend on; never reuse a
  pre-fetch expansion inside a later command string.
- When a command dies with a shell parse error, re-issue it with explicit
  refs or quoting instead of retrying the same string; record the quoting
  failure separately from repository state.

### Windows shell dialect portability

The same command text parses differently in cmd.exe, PowerShell, Git Bash
(MSYS), and WSL. Identify the active shell before running git or build
commands; a command verified in one dialect is not portable.

- Quoting: PowerShell double quotes expand variables and subexpressions
  (`$var`, `$()`), single quotes are verbatim — use single quotes for any
  argument containing `$`, `@`, backticks, or git revision shorthand. In
  cmd.exe the escape character is `^` and `%var%` expands; in bash single
  quotes are also verbatim.
- Stop parsing: PowerShell `--%` passes every remaining argument verbatim to
  the native program; use it when a complex argument string cannot be quoted
  safely.
- MSYS/Git Bash path conversion: arguments that look like Unix paths are
  auto-converted to Windows paths (e.g. `/foo` becomes
  `C:/Program Files/Git/foo`), and environment-variable paths are converted
  too. Use `MSYS2_ARG_CONV_EXCL=*` (MSYS2) or `MSYS_NO_PATHCONV=1` (Git Bash)
  for literal arguments, a leading `//`, or native `C:\...` paths for Windows
  programs; `/c/...` is a Git Bash convention, not a Windows path.
- Line endings: `core.autocrlf` and `.gitattributes` decide LF vs CRLF. A
  `.sh` file checked out with CRLF fails with "bad interpreter". Keep shell
  scripts LF, declare the tree in `.gitattributes`, and normalize with
  `git add --renormalize`.
- Encoding: PowerShell 5.1 redirects (`>`) write UTF-16 by default — use
  `Out-File -Encoding utf8` or `Set-Content -Encoding utf8`. On Chinese
  Windows, prefer UTF-8 (`chcp 65001`) and `git config core.quotepath false`
  so Unicode paths render readably.
- Long paths: Windows MAX_PATH is 260 by default; enable
  `git config core.longpaths true` for deep trees, or use `\\?\` prefixes
  only where proven safe (never to bypass ACLs or follow reparse points).
- Case: Windows filesystems are case-insensitive; `core.ignorecase` matters
  when a rename changes only the case of a file.
- File locks: Windows locks open files — `git gc`, renames and installs fail
  with "file in use". Retry after the owning process exits; do not kill
  shared proxy, browser, desktop, or authentication processes for a shortcut.
- Never build a git command by interpolating `$()` or `$var` into a
  PowerShell argument; pass argument lists, single-quote, or use `--%`.

### Skill use

- Before executing a task, first check the project skill-call index (`.hermes/skill-call-index.json`); on a hit, invoke the skill directly without rescanning.
- On a miss, scan the available skills (SKILL.md descriptions), load the matching one, and record the task->skill mapping into the index for next time.
- If still no match, proceed directly — do not block. A skill is a manual, not decoration; invoke the relevant skill instead of "just starting".
- Use installed Workflow Assistance skills when their descriptions match the task. Load only the relevant skill body, follow its boundaries, and prefer project-local skills over global generalizations.
- A skill is guidance, not authorization for external side effects.
