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

## 3. Paths, workdirs, and Git-Bash

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

For several projects, probe the page title or a known health endpoint on each candidate port before opening a browser preview. Do not use an old screenshot or stale tab as evidence that the current project is running.

For Git-Bash commands with non-ASCII JSON, write the payload to a UTF-8 file and pass `curl -d @file`; do not rely on inline shell encoding.

Avoid Windows redirection `>NUL` in Git-Bash: it can create a real repository file named `NUL`. Use `>/dev/null 2>&1` for Bash commands, or keep `NUL` inside a deliberately quoted `cmd.exe /c` command.

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
  --repo "$REPO_ROOT" --home "$HERMES_HOME" --apply --approved
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

## Common pitfalls

1. Treating Git-Bash as PowerShell.
2. Launching a `.cmd` through Python/Node without `cmd.exe`.
3. Fixing PATH shadowing by editing global configuration instead of verifying the executable first.
4. Regenerating a lockfile before preserving the exact diff.
5. Restarting a server before checking `TIME_WAIT` and listener ownership.
6. Using a stale localhost port or cached screenshot as proof of the current project.
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
