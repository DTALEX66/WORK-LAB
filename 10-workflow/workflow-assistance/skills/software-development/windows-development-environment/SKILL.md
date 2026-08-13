---
name: windows-development-environment
description: "Use when debugging Windows Node, Python, Git-Bash, PowerShell, path, encoding, or local-server failures."
version: 1.2.1
author: Hermes Agent
license: MIT
platforms: [windows]
tags: [windows, nodejs, powershell, python, git-bash, encoding, paths]
metadata:
  hermes:
    tags: [windows, nodejs, powershell, python, git-bash, encoding, paths]
    related_skills: [project-data-boundary]
---

# Windows Development Environment

## Overview

Use this skill for Windows-specific development failures and for safe execution from Hermes' Git-Bash/MSYS terminal. It covers shell selection, encoding, executable resolution, subprocess launching, paths, local servers, Git, and small deployment-pack checks.

This skill is **not** a provider, VPN, proxy, plugin, Desktop-layout, or credential-management skill. Use `model-switch` for provider/model work, `project-data-boundary` for project containment, and the official Hermes/Codex commands for authentication or runtime configuration.

## When to use

- Node.js, Next.js, npm, Python, or Git operations on Windows.
- `spawn EINVAL`, `WinError 2`, `ETIMEDOUT`, or npm exit-handler failures.
- PowerShell scripts with CJK/non-ASCII content.
- Git-Bash commands involving spaces, Unicode, or Windows `.cmd` wrappers.
- Local development servers that fail after a restart or appear on the wrong port.
- A repository or deployment pack needs encoding, path, or staging verification.
- Configuring/repairing a locally-installed desktop tool (Open Design / Codex /
  OpenHuman) whose `doctor`/`configure` diagnostic reports FAIL — see
  `references/desktop-tool-config-repair.md` for the diagnostic-script-staleness
  pattern (a FAIL may be the tool's stale expectation, not a real config problem)
  and the safe backup-before-edit repair sequence.

## 1. Shell and encoding

### PowerShell selection policy

Hermes `terminal` uses Git-Bash/MSYS by default. Use POSIX syntax there; do not assume the shell is PowerShell.

When PowerShell is required, prefer **PowerShell 7** via `pwsh`:

```bash
pwsh -NoProfile -Command '...'
```

### Git-Bash → PowerShell variable expansion

Git-Bash parses an inline command **before** it starts `pwsh`. Therefore a
PowerShell script wrapped in Bash double quotes lets Bash expand `$name` first;
an unset Bash variable becomes an empty string and PowerShell receives damaged
source. This is a shell-boundary issue, not a PowerShell variable issue.

For a short command, use Bash single quotes around the whole PowerShell source
and PowerShell double quotes inside it:

```bash
pwsh -NoProfile -Command '$value="safe"; Write-Output "value=$value"'
```

For a multi-line command or any command that creates, deletes, replaces, edits
registry state, controls a service, or changes a desktop shortcut, write a
reviewable ASCII/UTF-8 `.ps1` under the active project's ignored
`.hermes/task-runtime/`, then run:

```bash
pwsh -NoProfile -File .hermes/task-runtime/operation.ps1
```

Do not rely on PowerShell `--%` to fix this: it is processed only after Bash has
already expanded the command. Do not paper over the problem with scattered
`\$` escapes; they are easy to miss in a complex script. Verify preconditions,
perform the smallest approved change, then read back the exact target.

Use `powershell.exe -NoProfile` only for a legacy module or Desktop-only compatibility case.

PowerShell 5.1 can misparse UTF-8 scripts containing CJK when launched from Git-Bash. Prefer an ASCII-only `.ps1`, or save the script as UTF-8 with BOM before retrying. Keep explanations in Markdown rather than embedding large non-ASCII blocks in PowerShell source.

When a `.ps1` must stay ASCII-only but needs CJK **text** (e.g. synthesizing a Chinese audio fixture via System.Speech without a TTS package), express the CJK as code-point escapes instead of literals:

```powershell
$zh = [string]::Join('', @(0x673A,0x5668,0x5B66,0x4E60))  # 机器学习
# or write it out via [System.IO.File]::WriteAllText($p, $zh, [Text.Encoding]::UTF8)
```

Also: `powershell -Command "...$s..."` from Git-Bash expands `$s` as a **bash** variable before PowerShell sees it — a `$synth = New-Object ...` inline command breaks. Put the script in a file and run `powershell -ExecutionPolicy Bypass -File script.ps1` instead. Check available SAPI voices with a short `.ps1`:

```powershell
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
foreach ($v in $synth.GetInstalledVoices()) { $v.VoiceInfo.Name + " | " + $v.VoiceInfo.Culture }
```

Check touched text files before upload:

```bash
python -c "from pathlib import Path; p=Path('script.ps1'); b=p.read_bytes(); print('utf8', end=' '); b.decode('utf-8'); print('ok', 'crlf', b'\\r\\n' in b)"
git diff --check
```

Do not normalize unrelated historical files merely to remove noise; check the current change set.

## 2. Executable and subprocess resolution

### PATH shadowing

Hermes may bundle a Node runtime, while another Node or tool wrapper appears earlier in `PATH`.

```bash
command -v node
node --version
python -c "import sys; print(sys.executable)"
```

Use the project interpreter or active virtual environment. Do not assume `python` and `python3` resolve to the same interpreter. Do not guess that they refer to the same installation. Hermes workflow scripts use `python`.

### `.cmd` launchers

Win32 `CreateProcess` callers such as Node `child_process.spawn` and Python `subprocess.run` may not launch a `.cmd` wrapper directly. Prefer a real `.exe`; otherwise invoke the wrapper through `cmd.exe`:

```bash
cmd.exe /d /s /c "tool --version"
```

From Git-Bash, `cmd //c "C:\path\tool.cmd --version"` can print the Windows
banner and NOT execute (MSYS arg/path mangling). Use `cmd.exe /d /s /c "tool
--version"` (forward-slash form) or, most reliably, PowerShell:

```bash
powershell.exe -NoProfile -Command "& 'C:\path\tool.cmd' --version"
```

Node example:

```js
const command = process.platform === 'win32'
  ? (process.env.ComSpec || 'cmd.exe')
  : 'tool';
const args = process.platform === 'win32'
  ? ['/d', '/s', '/c', 'tool --version']
  : ['--version'];
spawn(command, args, {shell: false, stdio: 'inherit'});
```

Verify both shell and Python resolution before changing code:

```bash
command -v tool
python -c "import shutil; print(shutil.which('tool'))"
```

### Launching a GUI exe with spaces from Git-Bash (use PowerShell, not `cmd start`)

Do NOT launch a desktop GUI exe from Git-Bash with `cmd.exe /d /s /c "start \"\" \"C:\path with spaces\app.exe\""`. Git-Bash mangles the nested quotes and the `\"\"` title-argument pairing, so `start` mis-parses and Windows pops a spurious **"Windows 找不到 '\\' 文件"** dialog (it treats a stray `\` as the file to open). This is a launch-command quoting bug, NOT an app fault.

Launch the GUI with PowerShell `Start-Process` (handles paths-with-spaces and the working dir correctly):

```bash
powershell.exe -NoProfile -Command "Start-Process -FilePath 'D:\Programs\Open Design\Open Design.exe' -WorkingDirectory 'D:\Programs\Open Design'"
```

Then verify it actually came up, don't assume:

```bash
sleep 8
tasklist | grep -i "Open Design"          # expect the main + renderer + gpu processes
# GUI readiness: capture the app window via computer_use and read its AX tree
# (a `windows: []` / empty window_title on the process does NOT mean it failed;
#  the window renders on a later capture).
```

The same rule applies to any Electron/CEF desktop app launched from a project checkout
(Open Design, OpenHuman, Hermes desktop, CC Switch): prefer `Start-Process` and confirm
by process tree + a window snapshot rather than by the exit of the launch command.

## 3. Paths, workdirs, and Git-Bash

- **Git-Bash `$HOME`/`$PWD`（MSYS 形式 `/c/Users/...`）传给 Windows 原生 Python 会解析成错误路径。**
  `python script.py --home "$HOME"` 在 Windows Python 里变成 `C:\c\Users\ALEX\...`（Path 不转换 MSYS 前缀），
  导致脚本找不到文件并**误报配置漂移/FAIL**（例如 sync/verify 脚本报 `config_invalid`、`state_missing`，
  而手工用 `C:/Users/ALEX/...` 跑全部通过）。向 Windows 程序传路径参数时一律用 Windows 原生形式
  `C:/Users/...`（正斜杠），不要用 `$HOME`、`$(pwd)`、`/c/...`；MSYS 路径只用于 bash 自身 `cd`。
- **`PYTHONPATH` on Windows is `;`-separated, even from Git-Bash.** Python
  splits the env var on `os.pathsep` (Windows = `;`), not `:` — a CI-style
  `PYTHONPATH=src:scripts:...` silently becomes one bogus path and imports fail
  with `ModuleNotFoundError`. From bash, quote it:
  `PYTHONPATH='src;scripts;../../10-workflow/workflow-assistance/scripts/workflow' python -m unittest ...`
  Colon form is Linux-only (CI manifests use it on ubuntu; do not copy it to a
  local Windows run verbatim).
- Quote paths containing spaces: `cd '/d/All projects/example'`.
- Prefer forward slashes in Bash commands and JSON/YAML values.
- If a tool rejects a Unicode `workdir`, leave the tool workdir unset and `cd` inside the command instead.
- Do not rename a project merely to work around a shell path parser.
- For a clone destination containing spaces, inspect it first; never delete a non-empty target without explicit scope.

```bash
TARGET_POSIX='/d/All projects/example'
TARGET_WIN=$(cygpath -w "$TARGET_POSIX")
GIT_TERMINAL_PROMPT=0 git clone <approved-remote> "$TARGET_WIN"
cd "$TARGET_POSIX"
git status --short
```

If Git reports dubious ownership, inspect the repository and ask before changing global `safe.directory`. Do not add a global trust exception silently.

### Bash wrapper scripts: two silent breakers (validated 2026-08-12)

A project-local bash wrapper (e.g. `scripts/ci/run_tests.sh` that fixes
`--basetemp` and env vars, then `exec uv run ... pytest`) hits two silent
traps:

1. **`pwd` returns an MSYS path (`/d/All projects/...`) that Windows Python/uv
   cannot parse.** `$(cd ... && pwd)` inside git-bash gives `/d/...`; passing
   that as `--basetemp=` or any path argument to a Windows-native program makes
   it fail or silently ignore the argument (pytest reports `collected 0 items`
   with a correct-looking rootdir). Fix: derive the Windows path with
   `pwd -W` (or `cygpath -w`), normalize backslashes to forward slashes, and
   use that for every path handed to Windows programs; keep the MSYS path only
   for bash `cd`.
2. **A leading `--` is passed through as an argument when bash invokes a
   non-builtin script.** `bash scripts/run_tests.sh -- -x --collect-only`
   does NOT strip the `--`: `"$@"` becomes `(--, -x, --collect-only)` and the
   script's `pytest ... "$@"` then treats `--` as a file-path separator —
   pytest reports `ERROR: file or directory not found: -x` and collects
   0 items. Fix: strip a leading `--` inside the script before forwarding:
   `if [ "${1:-}" = "--" ]; then shift; fi` — then both
   `run_tests.sh -x ...` and `run_tests.sh -- -x ...` work.

Debug wrapper failures with `bash -x script.sh` — the final expanded command
line exposes both traps immediately.

## 4. npm and lockfiles

Common symptoms:

| Symptom | Likely cause | First check |
|---|---|---|
| `spawn EINVAL` | `.cmd` launched without `cmd.exe` | executable path and launcher type |
| `Exit handler never called!` | registry or npm process failure | registry configuration and network status |
| `ETIMEDOUT` | lockfile points at an unavailable registry | lockfile URLs, without printing credentials |
| wrong Node version | PATH shadowing | `command -v node`, `node --version` |

Lockfile regeneration is destructive. Before changing `package-lock.json` or `node_modules`:

1. identify the exact project paths;
2. save a reviewable backup or Git diff;
3. obtain explicit approval;
4. remove only those confirmed paths;
5. regenerate with the project's documented command, commonly:

```bash
npm install --ignore-scripts --no-audit --no-fund
```

Never print `.npmrc`, tokens, credential files, or private registry credentials.

## 5. Local Windows servers

After forcibly stopping a development server, the port may remain in `TIME_WAIT` briefly. Verify the listener before restarting; do not infer ownership from a remembered port.

```bash
sleep 2
netstat -ano | grep ':5173' | grep LISTENING || echo PORT_CLEAR
python -m http.server 5173 --bind 127.0.0.1
```

### Stale uvicorn/FastAPI child still serving OLD code

When a FastAPI server is started via a wrapper process (e.g. `python -m app.runtime_entrypoint core` that itself launches uvicorn), killing the wrapper (`process kill`) frequently leaves the **detached uvicorn child alive**. It keeps listening on the port AND — if the app takes a runtime/database lock at startup — keeps holding that lock. Symptoms that are easy to misread:

- A **new startup fails** with `RuntimeError: database operator requires the app to be offline` (the lock is held by the zombie child).
- The port still answers, but the answer comes from **stale code**: a route added after the child started returns `422` (the `Literal[...]` path-param validation rejects the new value) while the same request via TestClient against current source returns `200`. The response `workspace=200` can be true while a new sub-route 422s — both are the zombie, not a real code bug.
- `curl` to a *newly added* asset/route returns an error even though you just added it — this does NOT mean your edit is wrong; it means you are talking to an old process.

Diagnose by PID, not by port memory — find who actually LISTENs and kill that pid (use `taskkill /F /PID`, NOT `taskkill //PID` which Git-Bash mangles into an invalid option):

```bash
netstat -ano | grep ':8000' | grep LISTEN          # last column = pid
taskkill /F /PID <pid>
sleep 2
netstat -ano | grep ':8000' | grep LISTEN || echo PORT_FREE
```

If `taskkill /F /PID` itself fails (or the pid is a detached child you want to clean without knowing it), kill by port with PowerShell in one line — validated 2026-08-13, and it survives Git-Bash quoting where `cmd //c "taskkill /PID ..."` silently runs the wrong thing:

```bash
powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id \$_.OwningProcess -Force }"
# then verify the port is actually free:
netstat -ano | grep ':8000' | grep LISTEN || echo PORT_FREE
```

Then start fresh from current source. If a runtime/lock guard still complains after the port is free, check for the lock file / stale pid before assuming the code is wrong. Prefer `notify_on_complete=true` on the background server launch so you learn when the wrapper exits, and always re-verify readiness with a health check + a request against a *newly added* route before trusting the restart.

For several projects, probe the page title or a known health endpoint on each candidate port before opening a browser preview. Do not use an old screenshot or stale tab as evidence that the current project is running.

- For Git-Bash commands with non-ASCII JSON, write the payload to a UTF-8 file and pass `curl -d @file`; do not rely on inline shell encoding.
- **Native Windows git cannot open MSYS-style `/tmp/...` paths.** In Git-Bash, `/tmp` maps to `C:\Users\<user>\AppData\Local\Temp`, but `git apply /tmp/x.patch` (and other native-git path args) fails with `can't open patch ... No such file or directory` because native git does not translate the MSYS path. `ls`/`cp` work with `/tmp/...` (they're shell builtins / MSYS-aware), but `git` is not. When staging a saved patch between worktrees, pass the Windows-native form: `git apply "C:/Users/<user>/AppData/Local/Temp/x.patch"` (or `$(cygpath -w /tmp/x.patch)`), and copy support files with `cp` then reference them by their Windows path.

Avoid Windows redirection `>NUL` in Git-Bash: it can create a real repository file named `NUL`. Use `>/dev/null 2>&1` for Bash commands, or keep `NUL` inside a deliberately quoted `cmd.exe /c` command.

### Backticks in `git commit -m` are command substitution in Bash

Git-Bash executes backticks inside double-quoted `-m` strings. A commit message
like `git commit -m "report_csv blanked perfect CER 0.0 (falsy `or ""`)"` runs
`or` as a shell command and silently swallows the quoted text — the message lands
in the repo truncated/mangled. When a commit message contains backtick-worthy
content (code spans, `or`-style tokens), either:
- write the message to a file and use `git commit -F msg.txt` (most reliable), or
- avoid backticks entirely in the `-m` string (use plain quotes/plain prose).

After committing, `git log -1 --format=%B` and read the full message before
pushing — truncation is silent and irreversible once merged.

## 6. Workflow-assistance deployment boundary

Use the repository's canonical synchronizer. Do not replace it with ad-hoc `cp` commands:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
HERMES_HOME="${HERMES_HOME:?Set HERMES_HOME to the intended Hermes Home}"
python scripts/workflow/sync_hermes_workflow_assets.py \
  --repo "$REPO_ROOT" --home "$HERMES_HOME"
```

The command without `--apply` is the reviewable dry-run. After checking its paths,
ownership decisions, and drift results, an explicitly authorized deployment may use:

```bash
python scripts/workflow/sync_hermes_workflow_assets.py \
  --repo "$REPO_ROOT" --home "$HERMES_HOME" --apply
hermes config check
```

The post-apply config check is part of the deployment proof. Keep the generated
backup until the check and targeted runtime verification pass. If promotion or
verification fails, stop using the affected live assets and follow the synchronizer's
recorded backup/rollback path; do not repair the live Home with hand-copied files.

The normal sync path:

- deploys only explicitly owned skill roots, binaries, and file mappings;
- never promotes mixed-ownership `config.yaml` or workflow state;
- preserves provider/model/auth/MCP/plugin/session/memory and network-routing state;
- uses backup and rollback evidence;
- must fail closed on an unsafe path or ownership drift.

A drifted live managed root may be a user customization. Do not overwrite it silently. Either skip that exact root with a recorded reason or stop for explicit approval. Do not use this skill to enable plugins, change MCP servers, edit `AGENTS.md`, change provider routes, or copy credentials.

For a portable verification, use an empty Home under the project's ignored runtime. A structural portable pass is not proof that a real profile loaded every file.

## 7. Git changes and upload hygiene

### Provenance / digest hashes on Windows use CRLF-normalized bytes (validated 2026-08-13)

A repo that records file hashes (skill provenance, checksum manifests, state
files) must compute them from **CRLF→LF normalized bytes**, or Windows CRLF
checkouts will never match Linux LF hashes. `check_skill_provenance.py`
style validators do:

```python
data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
hashlib.sha256(data).hexdigest()
```

After editing any tracked file covered by a hash manifest, regenerate the
hash with the SAME normalization (plain `sha256(file_bytes)` gives a
different value on CRLF files) and run the provenance gate. Symptom:
`source SHA drift: <name>` with no content change visible in diff.

### gh CLI uninstalled: git credential helper points at a dead path (validated 2026-08-13)

After `gh` is uninstalled (or its scoop install moved), a leftover global git
config `credential.https://github.com.helper = !'C:\...\gh.exe' auth
git-credential` breaks every push with `could not read Username`. The Windows
Credential Manager still holds valid credentials; the dead helper shadows it.

Fix at the repo level (do not edit global config without asking):

```bash
git config credential.https://github.com.helper 'manager'
git config credential.https://gist.github.com.helper 'manager'
git push   # now authenticates via the Credential Manager
```

For REST API calls, the Credential Manager does NOT return a plaintext token
via `git credential fill` (interactive), so use `git credential fill` piped
to curl only when it returns a `password=` line (do not print it):

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | grep '^password=' | cut -d= -f2-)
curl -s -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/OWNER/REPO"
unset TOKEN
```

Note: `host=github.com` works for api.github.com too; `host=api.github.com`
has no stored credential.

### Anonymous GitHub API rate limit (60/hr) vs authenticated (5000/hr)

Bulk check-run / PR-status polling with anonymous `curl` exhausts the 60/hr
core limit fast; responses then come back as `403 rate limit exceeded` with
empty JSON. Authenticate every repeated API call (see token snippet above);
check remaining quota with the authenticated request:
`curl -s https://api.github.com/rate_limit -H "Authorization: Bearer $TOKEN"`.

### Rebase + force-push: CI push-event run fails on `before` sha (validated 2026-08-13)

After `git rebase` + `--force-with-lease`, the GitHub **push** workflow run
can fail in a `git diff "$BEFORE_SHA" "$HEAD_SHA"` step (e.g. gate-plan's
"Discover changed paths") because `github.event.before` is the pre-rebase sha
that no longer exists in the branch history. The **pull_request** run for the
same head stays green. Do NOT treat the push-run failure as a code bug:

- Read PR mergeState from the pull_request run's check-runs only.
- If branch protection requires `aggregate` and the stale push run blocks it,
  push an empty commit (`git commit --allow-empty -m "ci: retrigger"`) to
  supersede the failed push run, or merge via REST with the pull_request
  check green.

Before editing:

```bash
git status --short
git branch --show-current
git rev-parse --show-toplevel
```

Before staging:

```bash
git status --short
git diff --check
git diff --stat
```

Stage explicit paths only. Never stage `.env`, `auth.json`, databases, logs, caches, virtual environments, browser state, or generated runtime evidence. A clean local test is not release evidence; use the repository's canonical quality gate and verify CI against the exact commit SHA.

### Stale exported env vars redirect project DB/runtime paths

The Hermes terminal session persists exported environment variables across calls. A variable exported by an earlier run (e.g. `export COGNITIVE_DATA_DIR=/tmp/mfx-browser-smoke` from a previous smoke run) silently redirects the project's runtime path resolution — the app then opens/validates a different SQLite database, and `migrate` or server startup fails with confusing downstream errors (`phase4 research schema migration is pending`, `no such module: vec0`, or writes landing in the temp dir). The DB path looks wrong only if you check `python -c "from shared import storage; print(storage.DB_PATH)"`.

### Convention gate `--source head` checks git HEAD, not the working tree (validated 2026-08-13)

A repo convention checker invoked as `check_repository_conventions.py --source head` validates the **committed HEAD objects**, not the dirty working tree. Editing a file on disk does not change what the gate sees until the change is committed — so a gate that "failed locally" can pass immediately after commit+push of the identical fix, and vice versa. When a CI convention gate fails while your local `--source head` run passes, suspect a BOM/encoding difference introduced at write time (see below) rather than assuming CI parity.

### utf-8-sig / encoding='utf-8-sig' writes inject a UTF-8 BOM that convention gates reject (validated 2026-08-13)

`Path.write_text(..., encoding='utf-8-sig')` writes a leading `EF BB BF` BOM even when the original file had none. A repo convention gate that forbids BOMs (`unexpected-bom: UTF-8 BOM is prohibited`) then fails on files you merely touched. Symptom: your edit is correct, but CI/lint reports `unexpected-bom` on files whose content diff looks clean. Fix: read with `utf-8-sig` (tolerant) but **write with plain `utf-8`** (or `write_bytes` after stripping a leading `\xef\xbb\xbf`). Verify with `head -c 3 file | xxd` — must NOT be `ef bb bf`.


Diagnose and fix:

```bash
echo "COGNITIVE_DATA_DIR=${COGNITIVE_DATA_DIR-unset}"
unset COGNITIVE_DATA_DIR        # or export -n COGNITIVE_DATA_DIR
python -c "from shared import storage; print(storage.DB_PATH)"  # re-check the resolved path
```

When launching project servers from bash, explicitly `env -u COGNITIVE_DATA_DIR` (and `-u PYTHONPATH`) so a stray export cannot hijack the run. `env -u` on the command line beats relying on `unset` having taken effect in a long-lived session.

### `no such module: vec0` during migrate/fingerprint with sqlite-vec (validated 2026-08-12)

A project using the `sqlite-vec` extension can fail migrations with `sqlite3.OperationalError: no such module: vec0` even though `import sqlite_vec` succeeds: the extension is loaded **per-connection** (`conn.enable_load_extension(True); sv.load(conn)`), and a schema-fingerprint routine that opens a plain `sqlite3.connect` then `SELECT *` over every table hits `vec0` virtual tables without the module loaded. The vector rows are derived from a companion `<table>_id_map` table anyway, so the correct fix is to **skip virtual tables in the fingerprint** and let the id-map table carry the fingerprint:

```python
declared = str(item["sql"] or "")
if "USING vec0" in declared or "VIRTUAL TABLE" in declared:
    continue  # rows derived from *_id_map; can't SELECT without extension
```

Symptoms to recognize: migrate succeeds on a fresh DB then startup fails with a confusing `phase4 ... schema migration is pending` / `no such module: vec0` traceback pointing at `migration_runner`/`index_manifest` fingerprint code. The fix is in the fingerprint routine, not in the migration SQL.

### `uv pip install` without `--python` targets the wrong venv (validated 2026-08-12)

With `UV_PROJECT_ENVIRONMENT` set, `uv run --frozen` executes against that venv,
but a bare `uv pip install <pkg>` installs into the **project `.venv`** instead.
The package then cannot be imported by the same `uv run` command:
`find_spec('<pkg>')` returns `None`, and anything keyed off it (e.g. an engine's
`available` flag) silently stays off. This looks like the detector is broken when
the real problem is two different interpreters.

```bash
# wrong: goes to project .venv
uv pip install rapidocr-onnxruntime
# right: target the venv uv run actually uses
uv pip install --python "D:/All projects/OS configuration/cognitive-loop-os-ci-venv/Scripts/python.exe" rapidocr-onnxruntime
# verify with the SAME interpreter the run uses:
uv run --frozen --group ci python -c "import importlib.util; print(importlib.util.find_spec('rapidocr_onnxruntime'))"
```

`uv pip show <pkg>` prints the `Location:` — compare it against
`uv run --frozen python -c "import sys; print(sys.prefix)"` before assuming the
install landed where the run looks.

### pytesseract OCR skips: TESSDATA_PREFIX must point at the versioned dir (validated 2026-08-12)

On this machine, scoop installs language data under a **versioned** directory and there is NO `tesseract-languages/current` symlink. The stale default `TESSDATA_PREFIX=/c/Users/ALEX/scoop/apps/tesseract-languages/current` makes pytesseract fail with `Error opening data file .../tessdata/eng.traineddata` and OCR tests **skip silently** (they do not fail). Fix: set the env var to the actual data dir and export it for the pytest run:

```bash
export TESSDATA_PREFIX="D:/All projects/OS configuration/toolchains/scoop/apps/tesseract-languages/4.1.0"
tesseract --list-langs   # sanity: should print eng
# then run pytest with TESSDATA_PREFIX=... in the env (env -u PYTHONPATH TESSDATA_PREFIX=... uv run ...)
```

Verify the real data location with `find "D:/All projects/OS configuration/toolchains/scoop/apps" -maxdepth 4 -name "eng.traineddata"`. A skipped OCR test is a sign to check this env var, not evidence the OCR path is fine.

## Common pitfalls

1. Treating Git-Bash as PowerShell.
2. Launching a `.cmd` through Python/Node without `cmd.exe`.
3. Fixing PATH shadowing by editing global configuration instead of verifying the executable first.
4. Regenerating a lockfile before preserving the exact diff.
5. Restarting a server before checking `TIME_WAIT` and listener ownership.
6. Using a stale localhost port or cached screenshot as proof of the current project.
7. Killing the wrapper process but leaving a detached uvicorn child alive — it still serves OLD code (new routes 422) and may hold the runtime/database lock. Find and kill the LISTENING pid (`taskkill /F /PID`).
7. Replacing a canonical deployment with direct copies.
8. Treating a managed-root drift as permission to overwrite possible user customization.
9. Reading or printing credentials while diagnosing registry, OAuth, proxy, or provider symptoms.
10. Staging `NUL`, `.env`, runtime databases, or task artifacts.

## Verification checklist

- [ ] Shell and interpreter were identified explicitly.
- [ ] Executable resolution was checked before changing code.
- [ ] Touched text files are UTF-8 and pass `git diff --check`.
- [ ] Paths were quoted and no unsafe deletion or global trust change was made.
- [ ] Local server ownership and port state were verified if relevant.
- [ ] Deployment used the canonical path and only owned assets.
- [ ] User configuration, credentials, provider/model routes, plugins, MCP, sessions, and memory were preserved.
- [ ] Runtime artifacts remain under the project ignored runtime/evidence directories.
- [ ] Tests and the canonical quality gate were run after edits.
- [ ] Exact changed paths, commit, and verification evidence are recorded.
