---
name: windows-development-environment
description: "Use when debugging Windows Node, Python, Git-Bash, PowerShell, path, encoding, or local-server failures."
version: 1.3.0
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
- Configuring/repairing a locally-installed desktop tool (Open Design / Codex / OpenHuman) whose `doctor`/`configure` diagnostic reports FAIL — see `references/desktop-tool-config-repair.md`.

## 1. Shell and encoding

### PowerShell selection policy

Hermes `terminal` uses **Git-Bash/MSYS** by default; use POSIX syntax there. When PowerShell is required, prefer **PowerShell 7** via `pwsh` (`powershell.exe` only for legacy/Desktop-only cases).
- **Git-Bash expands `$name` before `pwsh` sees it.** Wrap PowerShell source in Bash single quotes (short commands) or write an ASCII/UTF-8 `.ps1` under `.hermes/task-runtime/` and run `pwsh -NoProfile -File ...` (multi-line / state-changing). Do not rely on `--%` or scattered `\$` escapes.
- Prefer ASCII-only `.ps1`; PowerShell 5.1 misparses CJK in UTF-8 from Git-Bash. CJK *text* → code-point escapes; full recipe in `references/validated-cases.md`.
- Check touched text files before upload: `git diff --check` + a UTF-8/CRLF probe.

## 2. Executable and subprocess resolution

- **PATH shadowing:** Hermes may bundle a Node while another appears earlier in `PATH`. Verify before changing code: `command -v node`, `node --version`, `python -c "import sys; print(sys.executable)"`. Use the project interpreter. Do not assume `python` and `python3` resolve to the same interpreter. Hermes workflow scripts use `python`.
- **`.cmd` launchers** can't be spawned directly by `CreateProcess` (Node `spawn` / Python `subprocess`). Prefer a real `.exe`, else `cmd.exe /d /s /c "tool --version"`. From Git-Bash, `cmd //c ...` can print the banner and NOT run — use `cmd.exe /d /s /c` or PowerShell `& 'C:\path\tool.cmd'`.
- **GUI exe with spaces:** use PowerShell `Start-Process -FilePath '...' -WorkingDirectory '...'`, never `cmd start` (Git-Bash mangles the nested quotes into a spurious "找不到文件" dialog). Full recipe in `references/validated-cases.md`.

## 3. Paths, workdirs, and Git-Bash

- **Never pass MSYS paths (`$HOME`, `$(pwd)`, `/c/...`) to Windows-native programs** — use `C:/Users/...` forward-slash form; `cygpath -w` to convert. MSYS paths are for bash `cd` only.
- **`PYTHONPATH` on Windows is `;`-separated** even from Git-Bash: `PYTHONPATH='src;scripts;...'` (colon form is Linux-only).
- Quote paths with spaces; prefer forward slashes in Bash and JSON/YAML.
- Native Windows `git` cannot open MSYS `/tmp/...` paths — pass the Windows form (details in `references/validated-cases.md`). Avoid `>NUL` in Git-Bash (creates a literal `NUL` file); use `>/dev/null 2>&1`.
- **Commit messages with backticks:** write to a file and `git commit -F msg.txt` — backticks in `-m` are command substitution in Bash (details in `references/validated-cases.md`).

## 4. npm and lockfiles

| Symptom | Likely cause | First check |
|---|---|---|
| `spawn EINVAL` | `.cmd` launched without `cmd.exe` | executable path and launcher type |
| `Exit handler never called!` | registry or npm process failure | registry configuration and network status |
| `ETIMEDOUT` | lockfile points at an unavailable registry | lockfile URLs (without credentials) |
| wrong Node version | PATH shadowing | `command -v node`, `node --version` |

Lockfile regeneration is destructive: identify exact paths → save a diff → get explicit approval → remove only confirmed paths → regenerate (`npm install --ignore-scripts --no-audit --no-fund`). Never print `.npmrc`, tokens, or private registry credentials.

## 5. Local Windows servers

- After stopping a server, the port may stay in `TIME_WAIT`; verify the listener before restarting: `netstat -ano | grep ':PORT' | grep LISTEN`.
- **Stale uvicorn/FastAPI child:** killing the wrapper often leaves a detached uvicorn child alive, still serving OLD code (new routes return 422) and possibly holding the runtime/DB lock. Diagnose by PID: `netstat -ano | grep ':8000' | grep LISTEN` then `taskkill /F /PID <pid>` (never `taskkill //PID`). PowerShell one-liner to kill by port + full symptoms in `references/validated-cases.md`.
- Re-verify readiness with a health check + a request against a *newly added* route, never an old screenshot or remembered port.

## 6. Workflow-assistance deployment boundary

Use the repository's canonical synchronizer, not ad-hoc `cp`:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
HERMES_HOME="${HERMES_HOME:?Set HERMES_HOME to the intended Hermes Home}"
python scripts/workflow/sync_hermes_workflow_assets.py --repo "$REPO_ROOT" --home "$HERMES_HOME"   # dry-run
# authorized deployment adds --apply, then: hermes config check
```

The sync deploys only owned skill roots/binaries, never mixed-ownership config or provider/model/auth/MCP/plugin/session/memory state, and fails closed on drift. A drifted managed root may be a user customization — skip with a recorded reason or stop for approval. This skill does not enable plugins, change MCP, edit `AGENTS.md`, change provider routes, or copy credentials.

## Validated case studies

Detailed dated cases (with full command recipes) live in `references/validated-cases.md` — read on demand:

CRLF-normalized hashes · gh CLI dead credential helper · GitHub API rate limit · rebase+force-push `before` sha · stale exported env vars · `--source head` vs working tree · `utf-8-sig` BOM · sqlite-vec `vec0` fingerprint · `uv pip` wrong venv · bare `pip` pydantic-core drift · TESSDATA_PREFIX OCR skips · Bash wrapper `--` and `pwd` traps · GUI `Start-Process` · backticks in `-m`.

## Common pitfalls

1. Treating Git-Bash as PowerShell.
2. Launching a `.cmd` through Python/Node without `cmd.exe`.
3. Fixing PATH shadowing by editing global config instead of verifying the executable.
4. Regenerating a lockfile before preserving the exact diff.
5. Restarting a server before checking `TIME_WAIT` and listener ownership.
6. Using a stale localhost port or cached screenshot as proof of the current project.
7. Killing the wrapper but leaving a detached uvicorn child alive (still serves OLD code, may hold the lock).
8. Replacing a canonical deployment with direct copies.
9. Treating managed-root drift as permission to overwrite user customization.
10. Reading or printing credentials while diagnosing registry/OAuth/proxy/provider symptoms.
11. Staging `NUL`, `.env`, runtime databases, or task artifacts.

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
