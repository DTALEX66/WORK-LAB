---
name: workflow-assistance-windows-development
description: "Use for Windows development failures involving PowerShell, Git Bash, paths, quoting, Node, Python, ports, processes, encoding, or desktop runtimes."
---

# Windows development

- Identify the active shell and executable with real commands. Do not mix cmd.exe, PowerShell, Git Bash (MSYS), WSL, and native Windows syntax in one command string.
- Use native `C:\...` paths for Windows Python `Path` code; MSYS `/c/...` paths are shell conveniences and may resolve incorrectly in native programs.
- Verify interpreter and package-manager pairing before installs (`python --version`, `python3 --version`, `py -0`, launcher path, and environment).
- Quote paths containing spaces and pass argument lists instead of shell strings in scripts.
- Inspect live ports and processes before starting or stopping services. Do not kill shared proxy, browser, desktop, or authentication processes for a diagnostic shortcut.
- Keep generated runtime state inside the target Git project and verify restart/readback for desktop or service claims.

## Shell dialect table

| Dialect | String quoting | Escape char | Interpolation | Notes |
|---|---|---|---|---|
| PowerShell | double = expandable, single = verbatim | backtick | `$var`, `$()` in double quotes | unquoted `@` `{...}` token is a hashtable literal; `--%` stops parsing |
| cmd.exe | `"..."` only | `^` | `%var%` (batch), `%PATH%` | `& \| < > ( ) !` are special; `!var!` needs delayed expansion |
| Git Bash / MSYS | double/single, single = verbatim | `\` | `$var`, `$(...)` in double quotes | MSYS auto path conversion |
| WSL | POSIX | `\` | `$var`, `$(...)` | Linux paths; Windows drives under `/mnt/` |

Rule of thumb: when an argument contains `$`, `@`, backticks, `%`, or spaces,
single-quote it in PowerShell and bash, and in PowerShell prefer `--%` or
argument arrays for anything complex.

## Git revision shorthand vs PowerShell

- PowerShell parses an unquoted `@`-brace token as a hashtable literal, so git
  revision shorthand must be quoted: `git rev-parse '@{upstream}'` is safe; the
  unquoted form fails with "hashtable not terminated" before git runs. Git Bash
  treats the same text as literal.
- Prefer explicit refs (`git rev-parse origin/main`, `git rev-parse HEAD`).
- The shorthand family: `'@{u}'`, `'@{push}'`, `'@{<n>}'` (reflog, e.g.
  `'@{1}'`), `'@{-<n>}'` (previous checkout), and dated forms like
  `'HEAD@{5 minutes ago}'`. All of them are the same quoting hazard; quote
  them or use explicit refs.
- An unquoted `$(` subexpression concatenates into the argument
  (`HEAD$(git ...)` becomes `HEAD<sha>`); never embed command substitution
  into a PowerShell argument.
- After `git fetch`, re-resolve refs explicitly; do not reuse a pre-fetch
  expansion in a later command string.
- Classify these as quoting issues, not repository problems: "hashtable not
  terminated", "Missing '=' after key", "ambiguous argument" with a
  concatenated value.

## MSYS / Git Bash path conversion

- Arguments that look like Unix paths are auto-converted to Windows paths:
  `/foo` can become `C:/Program Files/Git/foo`. Environment-variable paths are
  converted too.
- Fixes for literal arguments: `MSYS2_ARG_CONV_EXCL=*` (MSYS2),
  `MSYS_NO_PATHCONV=1` (Git Bash), a leading `//`, or native `C:\...` paths.
- Pass `C:\...` or forward-slash `C:/...` to Windows programs; keep `/c/...`
  only inside Git Bash itself. Use `cygpath -w` / `cygpath -u` for explicit
  conversions when mixing dialects.

## Line endings and encoding

- `core.autocrlf` + `.gitattributes` decide LF vs CRLF. A `.sh` file checked
  out with CRLF fails with "bad interpreter: ...". Keep shell scripts LF and
  declare the tree in `.gitattributes`; normalize with `git add --renormalize`.
- PowerShell 5.1 `>` redirect writes UTF-16 by default; use
  `Out-File -Encoding utf8` / `Set-Content -Encoding utf8`. On Chinese
  Windows use UTF-8 (`chcp 65001`) and `git config core.quotepath false` so
  Unicode paths are readable.
- When `read_file`/tools report a text file as "binary", decode
  `utf-8-sig`/`utf-16` explicitly instead of concluding it is unreadable.

## Windows filesystem hazards

- Long paths: MAX_PATH is 260 by default; `git config core.longpaths true`
  for deep trees; `\\?\` prefixes only where proven safe (never to bypass
  ACLs or follow reparse points).
- Case: Windows filesystems are case-insensitive; renaming only the case of a
  file needs `core.ignorecase` awareness.
- File locks: open files block `git gc`, renames, and installs ("file in
  use"). Retry after the owning process exits; never kill shared processes
  for a shortcut. Record `BLOCKED_PROCESS_LOCK` when a path cannot move.
- Reparse points: treat symlinks, junctions, and reparse points as
  untrusted boundaries in scripts; do not follow them during cleanup or
  recovery.
- A PowerShell non-terminating error can leave exit code 0. For exact project
  runtime cleanup, prefer `hermes-project-data.py --project . cleanup-path
  <relative-name>`. If PowerShell is required, set
  `$ErrorActionPreference = 'Stop'`, use `Remove-Item -LiteralPath $target
  -Recurse -Force -ErrorAction Stop`, and fail when `Test-Path -LiteralPath
  $target` remains true. A zero exit code alone is not cleanup proof.
- On `Access denied`, do not immediately elevate or recurse again. Inspect the
  exact path's reparse state, read-only attributes and ACL, then identify the
  owning process when tooling is available. Use a bounded timeout and report
  `BLOCKED_RUNTIME_CLEANUP`; never kill a shared process or bypass an ACL.
- Junction verification (native truth over scanner labels): `fsutil
  reparsepoint query "<path>"` returns a tag for junctions/symlinks and error
  4390 for real directories; `Get-Item -LiteralPath "<path>" | Select
  Attributes, LinkType, Target` shows the reparse bit. Never delete or "fix" a
  path because an external scanner called it a junction or duplicate —
  verify the exact path with these native reads first (2026-08-10: OpenHuman
  reported two non-existent junctions; the paths were the real WORK-LAB repo
  and the OS configuration toolchain project).

## Failure classification

When a command fails on Windows, classify before retrying:

1. Quoting/parsing: "hashtable not terminated", "Missing '=' after key",
   ambiguous argument with a concatenated value → re-issue single-quoted or
   with explicit refs.
2. Path mangling: a `/...` argument became `C:/Program Files/Git/...` →
   `MSYS_NO_PATHCONV=1` / `MSYS2_ARG_CONV_EXCL=*` / native path.
3. Encoding: garbage text, mojibake, UTF-16 artifacts → UTF-8 pipe/redirection,
   `chcp 65001`, `core.quotepath false`.
4. Line endings: "bad interpreter", `\r` in output → LF + `.gitattributes` +
   renormalize.
5. Lock: "file in use" / "device or resource busy" → wait for the owning
   process, record `BLOCKED_PROCESS_LOCK`, never force-kill shared processes.
6. PowerShell non-terminating error: stderr reports failure but the process
   returns 0 → add `-ErrorAction Stop` and verify the filesystem postcondition.
7. ANSI output: escape bytes such as colour prefixes → strip control sequences
   before parsing; do not diagnose repository text as corrupt.

Never retry the identical string; re-issue the dialect-correct form and
record the failure class.
