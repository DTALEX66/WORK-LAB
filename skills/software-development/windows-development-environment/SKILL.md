---
name: windows-development-environment
description: "Windows-specific quirks and fixes for development: PowerShell encoding, PATH shadowing, spawn EINVAL, lockfile registry portability, and environment setup."
tags: [windows, nodejs, nextjs, powershell, spawn, npm-ci, path, cross-platform]
---

# Windows Development Environment

## When to load

- Any task that involves **Node.js scripts**, **Next.js builds**, or **npm operations on Windows**.
- Any task where `child_process.spawn` or `npm ci` fails with obscure errors (`EINVAL`, `Exit handler never called!`, `ETIMEDOUT`).
- Any task where the wrong Node.js version is active and Hermes bundles Node v22.
- Any task running **PowerShell `.ps1` scripts from git-bash/MSYS** — especially scripts with CJK/non-ASCII content.
- Any task cloning or moving Git repositories on Windows paths with spaces, especially from Hermes Git-Bash/MSYS into `D:\All projects\...`.

## Key patterns

### 0. PowerShell selection policy

Hermes `terminal` runs through Git-Bash/MSYS by default on this Windows host, so
plain terminal commands should use POSIX shell syntax. When a task specifically
requires PowerShell, prefer **PowerShell 7** via `pwsh`:

```bash
pwsh -NoProfile -Command '...'
```

Use Windows PowerShell 5.1 (`powershell.exe`) only when a legacy Windows module,
Desktop-only COM integration, or other compatibility requirement fails under
PowerShell 7:

```bash
powershell.exe -NoProfile -Command '...'
```

Do not imply that Hermes terminal's default shell is PowerShell; it is Git-Bash
unless `pwsh` or `powershell.exe` is invoked explicitly.

### 1. PowerShell `.ps1` with CJK characters fails from git-bash

When a `.ps1` script containing Chinese, Japanese, Korean, or other non-ASCII
characters is run via `powershell.exe -File` from git-bash/MSYS, it can fail
with encoding-related parser errors:

```
MissingEndParenthesisInFunctionParameterList
Missing closing '}' in statement block
```

**Root cause**: git-bash writes UTF-8 without BOM, but PowerShell's default
parser expects UTF-16 LE or UTF-8 with BOM for scripts containing non-ASCII
characters.

**Workaround**: execute the script's steps manually in bash instead, or
re-save the file as UTF-8 with BOM:

```bash
# Convert to UTF-8 with BOM and retry
powershell.exe -Command "
  \$content = Get-Content -Path 'script.ps1' -Raw -Encoding UTF8
  [System.IO.File]::WriteAllText('script.ps1', \$content, [System.Text.UTF8Encoding]::new(\$true))
"
```

### 1a. Deployment scripts: use the canonical sync path

Do not translate a failed deployment wrapper into ad-hoc `cp` commands. Direct config copies overwrite live provider/model, skill overlays leave deleted files active, and remembered tool enables violate the current minimal baseline.

Invoke the repository's canonical sync entry directly:

```bash
REPO_ROOT="D:/All projects/Workflow-assistance"
HERMES_HOME="${LOCALAPPDATA:-$HOME/AppData/Local}/hermes"
python "$REPO_ROOT/scripts/workflow/sync_hermes_workflow_assets.py" \
  --repo "$REPO_ROOT" --home "$HERMES_HOME" --apply
hermes config check
```

If another deployment repository has no canonical merge/sync entry, stop and inspect its preservation, backup, retirement and minimal-plugin contracts. Never overwrite a live config or overlay skills as a fallback.

### 2. Node.js PATH shadowing

Hermes bundles Node v22 at `AppData/Local/hermes/node/node.exe`, but other tools may appear earlier in `$PATH`.

**Check:** `which node && node --version`

**Fix:** Prepend Hermes Node to PATH:
```bash
export PATH="$HERMES_HOME/node:$PATH"
```

### 3. `child_process.spawn` / Python `subprocess` launcher issues on Windows

On Windows under Git Bash, `.cmd` files are not directly spawnable by APIs that call Win32 `CreateProcess` without a shell. This affects Node `child_process.spawn` and Python `subprocess.run(['tool'])`: Git-Bash may resolve `tool` to a shell wrapper or `.cmd`, while Python/Node may fail with `WinError 2`, `EINVAL`, or silently pick a later `.exe` in PATH.

**Fix for Node:** Use `cmd.exe` as the command when launching `.cmd` tools:
```js
const child = spawn(
  process.platform === 'win32'
    ? process.env.COMSPEC || 'cmd.exe'
    : 'npx',
  process.platform === 'win32'
    ? ['/d', '/s', '/c', 'npx next build']
    : ['next', 'build'],
  { stdio: 'inherit', env, shell: false },
);
```

**Fix for Python/subprocess or agent toolchains:** prefer a real `.exe` earlier in PATH, or call the `.cmd` through `cmd.exe /d /s /c`. For portable wrappers that must work from both Git-Bash and Python subprocesses, ship a bash/`.cmd` wrapper in the repo and, on the local machine only, put the real executable or a trusted `.exe` shim in `~/bin` before stale tool directories.

Example verification:
```bash
command -v tool && tool --version
python - <<'PY'
import shutil, subprocess
print(shutil.which('tool'))
print(subprocess.run(['tool','--version'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)
PY
```

### 4. `package-lock.json` registry lock-in

When a lockfile hardcodes internal registry URLs, `npm ci` times out.

**Fix:** Regenerate:
```bash
rm -rf node_modules package-lock.json
npm install --ignore-scripts --no-audit --no-fund
```

### 5. Common Windows npm failures

| Error | Likely cause | Fix |
|---|---|---|
| `Exit handler never called!` | Registry unreachable | Regenerate lockfile |
| `spawn EINVAL` | `.cmd` without shell | Use `cmd.exe /d /s /c` |
| `ETIMEDOUT` | Internal registry URLs | Regenerate lockfile |
| Wrong Node version | PATH shadowing | Prepend Hermes Node |

### 6. Hermes + CC Switch / provider routing boundary

Provider switching, proxy/router diagnosis, OAuth state and live GPT/DeepSeek/Codex smokes belong exclusively to the `model-switch` skill and Hermes official auth/config commands. Do not duplicate model names, ports or credential procedures in this Windows skill.

Windows-only pitfall: an OAuth device page may require the user’s normal proxy-configured browser to pass an interactive challenge. Never read or parse `.env`, `auth.json`, Windows Credential Store, browser cookies or bearer tokens as a workaround; report the prompt and let the user complete the supported login flow.

### 7. `python3` shadowed by Microsoft Store stub

On Windows, typing `python3` usually opens the Microsoft Store instead of
running a real Python interpreter. The actual Python is named `python`:

```bash
# Wrong:
python3 -c "print('hello')"  # → Microsoft Store popup or "not found"

# Right:
python -c "print('hello')"
```

The Hermes venv also uses `python.exe`, not `python3.exe`.

**Verification:**
```bash
which python && python --version
# If python3 is needed, check:
ls "$LOCALAPPDATA/Microsoft/WindowsApps/python3.exe" 2>/dev/null && echo "STUB DETECTED"
```

### 8. Git identity for fresh sub-repos and inline workaround

When `git init` creates a new repo inside a parent project (monorepo sub-repos), Windows git-bash/MSYS often fails to auto-detect user identity. Commands fail with:

```
Author identity unknown
fatal: unable to auto-detect email address (got 'admin@DESKTOP-FSE02M9.(none)')
```

**Fix for fresh sub-repos:** set config per-repo before committing:

```bash
cd sub-repo-dir
git config user.email "DTALEX66@users.noreply.github.com"
git config user.name "DTALEX66"
```

This is REQUIRED for any `git init` in a new directory — don't assume global config propagates on Windows.

**If GitHub CLI is authenticated, prefer the exact noreply identity from GitHub:**

```bash
GH_LOGIN=$(gh api user --jq '.login')
GH_ID=$(gh api user --jq '.id')
git config user.name "$GH_LOGIN"
git config user.email "${GH_ID}+${GH_LOGIN}@users.noreply.github.com"
```

This avoids exposing a real email address and matches GitHub's verified noreply format.

**Fix for inline identity** (single commit, no config change):

```bash
git -c user.name="YourName" -c user.email="your@email.com" commit -m "..."
```

### 9. Unicode path / `workdir` fallback in Hermes terminal

On Windows, project paths may contain Chinese or other non-ASCII characters.
If a terminal call rejects `workdir` with a message like `workdir contains disallowed character`, do not give up or rename the project. Leave `workdir` unset and `cd` inside the bash command instead:

```bash
cd '/c/Users/admin/Documents/脑力宫殿/brain-palace' && npm run check
```

This keeps execution in the intended project while avoiding tool-side `workdir` validation issues.

### 10. Git dubious ownership on copied/sandboxed Windows repos

Old or sandbox-created repos may fail Git commands with:

```text
detected dubious ownership in repository
```

Inspecting `.git/config` is still safe for remote/context, but status/log/diff may be blocked. If the user wants to operate on that repo, suggest adding a safe-directory exception:

```bash
git config --global --add safe.directory 'C:/path/to/project'
```

Do not make this global config change silently; it affects future Git trust decisions.

### 11. Windows port recycling (TIME_WAIT after taskkill)

After `taskkill //PID <n> //F` on a server process (python http.server, node, etc.),
the port enters TIME_WAIT state. Restarting the server immediately can fail with
"Address already in use" or silently bind to a broken socket.

**Symptom checklist:**
- `netstat -ano | grep ':PORT'` shows TIME_WAIT entries even after killing the listener
- New server starts but returns 502 or ERR_EMPTY_RESPONSE
- Browser navigates to `http://127.0.0.1:PORT` and gets nothing

**Fix:** Wait 2-3 seconds after `taskkill` before restarting:

```bash
taskkill.exe //PID <pid> //F 2>/dev/null
sleep 2
netstat -ano | grep ':PORT' | grep LISTEN || echo "PORT_CLEAR"
# Only then start the new server
```

**Prevention:** Bind python http.server explicitly to 127.0.0.1 (not 0.0.0.0 or ::):

```bash
python -m http.server 5173 --bind 127.0.0.1
```

This avoids dual-stack IPv4/IPv6 binding which doubles cleanup overhead on Windows.

### 12. CC Switch proxy poisons localhost connections

When `HTTP_PROXY=http://127.0.0.1:7890` and `HTTPS_PROXY=http://127.0.0.1:7890`
are set in `.env`, tools that respect these env vars (curl, some Node.js HTTP
clients, Python `requests`) will route **localhost** traffic through the proxy
too, causing 502 errors:

```bash
# This goes through the proxy → 502
curl http://127.0.0.1:5173/
```

**Fix for ad-hoc curl:** use `--noproxy` or unset the env for that command:

```bash
curl --noproxy '*' http://127.0.0.1:5173/
# or:
HTTP_PROXY= HTTPS_PROXY= curl http://127.0.0.1:5173/
```

**Fix for browser tools:** Hermes browser tools (Browserbase) access `127.0.0.1`
through cloud bridge — they are NOT affected by local proxy env vars. `browser_click`
failures on overlays are a coordinate/rendering issue, not proxy-related.

### 13. Portable deployment repos: encoding, escaping, and installers

When creating a repository that should let another Windows machine reproduce a Hermes/tool setup, package **deployment assets**, not application bodies. See `references/deployment-packaging-checklist.md` for a copyable checklist and baseline `.gitignore`/`.gitattributes` patterns:

- Do **not** commit installers or app binaries (`*.msi`, `*.exe`, `*.dmg`, `*.pkg`, `*.AppImage`, archives). Keep only config templates, skills/plugins, docs, small config exports, and setup scripts.
- Add `.gitignore` rules for installers, `.env`, `auth.json`, `state.db`, `*.db`, logs, caches, venvs, and `node_modules`.
- Add `.gitattributes` to keep text stable across Windows/macOS/Linux:
  ```gitattributes
  * text=auto eol=lf
  *.sh text eol=lf
  *.ps1 text eol=lf
  *.md text eol=lf
  *.yaml text eol=lf
  *.json text eol=lf
  *.template text eol=lf
  *.msi binary
  *.exe binary
  *.zip binary
  ```
- Normalize text to UTF-8 + LF before commit and run `git diff --check`. For normal app repos, prefer checking only files touched in the current change to avoid noisy historical CRLF churn; for deployment packs, check the whole repo. A deterministic check pattern:
  ```bash
  python - <<'PY'
  from pathlib import Path
  # Replace with the touched files for an app repo, or use Path('.').rglob('*') for deployment packs.
  files = [p for p in Path('.').rglob('*') if '.git' not in p.parts and p.is_file()]
  bad=[]; nul=[]; crlf=[]
  for p in files:
      data=p.read_bytes()
      if b'\x00' in data[:4096]: nul.append(str(p)); continue
      try: data.decode('utf-8')
      except UnicodeDecodeError: bad.append(str(p))
      if b'\r\n' in data: crlf.append(str(p))
  print('non_utf8', bad); print('binary_or_nul', nul); print('crlf', crlf)
  PY
  ```
- When a user explicitly calls out encoding concerns on a Windows repo, verify the latest/touched commit files with `decode('utf-8')` and absence of `\r\n`; if needed, add or tighten `.gitattributes` (`*.ts`, `*.vue`, `*.json`, `*.md`, `*.py`, `*.yml`, `.gitattributes` as `text eol=lf`) and commit that normalization separately.
- Avoid Chinese/emoji in `.ps1` files unless saved in a PowerShell-safe encoding. Prefer ASCII-only PowerShell scripts and put Chinese explanations in README files.
- In setup scripts for deployment packs, verify prerequisites (`hermes` installed, CC Switch running) and copy/enable assets; do not silently download/install the main app unless the user explicitly asked for a bootstrap installer.
- Use quoted POSIX paths in Git Bash and avoid hand-escaping Windows backslashes in JSON/YAML; prefer forward slashes or single-quoted MSYS paths in shell examples.

### 15. Model/provider changes require a new session

Hermes snapshots provider/model/tool availability at session start. After an authorized change made through `model-switch` or Hermes official configuration, use `/reset` or restart. This section defines only the Windows session-lifecycle pitfall; all switch recipes and route values live in `model-switch`.

### 14. Hermes ecosystem update check (Hermes + Codex + CC Switch)

When the user asks to check for updates, the three tools that matter are
Hermes Agent itself, OpenAI Codex CLI, and CC Switch. Run all three checks
in parallel where possible. See `references/ecosystem-update-check.md` for a
complete checklist with exact commands and version-capture patterns.

Quick-reference table (distilled from the reference):

| Tool | Version check | Latest check | Update command |
|------|--------------|-------------|----------------|
| Hermes | `hermes --version` | GitHub API `/repos/NousResearch/hermes-agent/releases/latest` | `hermes update` |
| Codex CLI | `codex --version` | `npm view @openai/codex version` | `npm i -g @openai/codex@latest` |
| CC Switch | PowerShell `FlyintPro.exe` FileVersion | GitHub `/repos/chen08209/FlClash/releases/latest` (kernel) | Manual via FlyintPro GUI |

**Pitfall:** `codex` may not be on `$PATH` in git-bash — it lives at
`C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\codex.cmd`.  Use
`cmd.exe //c "codex --version"` from bash, or invoke the `.cmd` directly.

**Pitfall:** FlClashCore.exe has no embedded version info (`FileVersion: 0.0.0.0`).
Use `FlyintPro.exe` path instead, or check `unins000.dat` for build metadata.

**Pitfall:** Git fetch of the Hermes upstream repo (`hermes-agent/`) times out
behind CC Switch on this machine. Use `export HTTPS_PROXY=http://127.0.0.1:7890`
before `git fetch` to route through the proxy.

### 16. Portable Hermes deployment packs for other Windows machines

When packaging a Hermes config/skills/tools repo for reuse on other computers,
make it clone-and-run portable rather than mirroring the current machine's live
state.

Checklist:

1. **Classify files by deployment target** — keep `config/`, `skills/<category>/`,
   `tools/`, `memories/` (reference only), and docs separate. Do not flatten all
   skills into one directory when the user asked for categories.
2. **Script root must be the script directory, not its parent** for a freshly
   cloned repo:
   ```bash
   # setup.sh
   REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
   PACK_DIR="$REPO_ROOT"
   ```
   ```powershell
   # setup.ps1
   $RepoRoot = $PSScriptRoot
   $PackDir = $RepoRoot
   ```
3. **Never upload live credentials** — include `.env.template` with blank values,
   `auth.json.template`, and instructions to rerun OAuth on each new machine.
   ChatGPT/Codex subscription OAuth is per-machine and must not be copied as a
   real token file.
4. **Normalize encoding/line endings** before committing. Add `.gitattributes`
   with LF for text and binary rules for installers/assets:
   ```gitattributes
   * text=auto eol=lf
   *.sh text eol=lf
   *.ps1 text eol=lf
   *.md text eol=lf
   *.yaml text eol=lf
   *.json text eol=lf
   *.template text eol=lf
   *.msi binary
   *.exe binary
   *.png binary
   *.zip binary
   ```
5. **Verify portability after edits** — UTF-8 decode all text files, run
   `bash -n setup.sh`, parse YAML if possible, `git diff --check`, and confirm
   the remote raw files decode as UTF-8 after push.
6. **Explain post-clone manual steps** — fill API keys, start CC Switch if used,
   rerun `hermes auth add openai-codex` for GPT subscription, then `/reset` or
   restart Hermes after provider/model changes.
7. **When renaming or redefining a deployment/workflow repo**, update both local
   docs and GitHub metadata in one closed loop:
   - Add or update a class-level project definition doc such as
     `docs/workflow/project-definition.md`.
   - Update `README.md`, troubleshooting docs, and any packaged skills/templates
     that still mention the old repo name or clone URL.
   - Search for stale identity strings before commit:
     ```bash
     grep -RInE 'old-owner/old-repo\.git|cd old-repo|old-pack-name|old project title' . --exclude-dir=.git
     ```
   - Run syntax/security checks, commit, push, then update GitHub description and
     topics with `gh repo edit ... --description ... --add-topic ...`.
   - If using Hermes Desktop/TUI, create or switch the local Project so the chat
     workspace is anchored to the new repo path.

See `references/hermes-deployment-pack-portability.md` for a concise reusable
verification checklist.

### 17. Multi-project localhost preview and screenshot hygiene

When several dev servers are running on nearby ports, never assume a remembered
port still belongs to the current repo. Before sending a browser preview or a
screenshot to the user:

```bash
for p in 5173 5174 5175 5176 5177 5178; do
  echo "---$p"
  curl --noproxy '*' -s --max-time 2 http://127.0.0.1:$p/ \
    | grep -oi '<title>[^<]*' | sed 's/<title>//i' || true
done
```

Then navigate the browser to the verified `127.0.0.1:<port>` URL, not a stale
`localhost` tab. After `browser_vision`, use the screenshot path from the latest
screenshot result/list, not a cached path from a previous turn. If the user says
the preview is the wrong project, immediately re-audit port titles and resend a
fresh screenshot.

### 18. curl + Chinese/Unicode POST body in git-bash

When `curl -d` contains Chinese or other non-ASCII characters in git-bash/MSYS,
the body can be mangled before reaching the server, producing "error parsing body".

**Root cause**: MSYS shell encoding interacts poorly with `curl -d` inline JSON.

**Fix**: write the payload to a temp file and use `-d @file`:

```bash
# WRONG — Chinese chars may be garbled:
curl -s -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{"content":"请帮我生成一份B线MVP开发计划"}'

# RIGHT — write to file first:
echo '{"content":"请帮我生成一份B线MVP开发计划"}' > /tmp/payload.json
curl -s -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d @/tmp/payload.json
```

### 19. Python imports from hyphenated directories

Directories with hyphens (e.g. `Inspiration-Research/`, `Knowledge-Base/`)
cannot be used as Python module names. `from Inspiration-Research.api import app`
is a SyntaxError.

**Fix**: use `sys.path.insert` to add the directory, then import without the hyphen:

```python
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "Inspiration-Research"))

# Now import from the directory content directly:
from intake.generator import generate_intake_card
from contracts.generator import generate_contract
```

For uvicorn, run from project root with the module path using the hyphenated name:
```bash
python -m uvicorn Inspiration-Research.api:app --port 8001
```

The `sys.path.insert` inside api.py handles the rest at import time.

### 20. Empty `__init__.py` shows as "binary" in `file` command

When running `file -b --mime-encoding __init__.py` on empty files (0 bytes),
the result is "binary". This is NOT an encoding issue — empty files have no
encoding. Skip empty files when auditing encoding.

### 21. UTF-16LE detection and conversion

On Windows, some files may be saved as UTF-16LE (especially from PowerShell or
legacy tools). `git diff` may show "binary files differ" for these.

**Detect**: `file path/to/file.py` → "UTF-16, little-endian"
**Convert**: `iconv -f UTF-16LE -t UTF-8 input.py > output.py`

```bash
# Find all non-UTF-8 files in the repo:
git ls-files | while read f; do
  test -s "$f" || continue
  encoding=$(file -b --mime-encoding "$f" 2>/dev/null)
  case "$encoding" in
    *utf-8*|*us-ascii*) ;;
    *binary*) test -z "$(cat "$f")" && continue; echo "WARN: $f = $encoding";;
    *) echo "WARN: $f = $encoding";;
  esac
done
```

### 22. Uploading Windows repo changes with encoding hygiene

Before pushing code from Windows, especially files containing Chinese text or
new Vue/TS/JSON files, verify the exact files being uploaded are UTF-8 and have
stable LF line endings. Do not let local SQLite DBs, `__pycache__`, or browser
smoke-test state slip into commits.

```bash
# Worktree and whitespace
cd '<repo>' && git status --short && git diff --check

# Check only the files changed in the latest commit or current upload set
python - <<'PY'
from pathlib import Path
files = ['.gitattributes']  # replace/add touched text files
bad=[]; crlf=[]
for f in files:
    data=Path(f).read_bytes()
    try: data.decode('utf-8')
    except UnicodeDecodeError: bad.append(f)
    if b'\r\n' in data: crlf.append(f)
print('non_utf8=' + (','.join(bad) if bad else 'none'))
print('crlf=' + (','.join(crlf) if crlf else 'none'))
PY
```

If CRLF appears in touched text files, normalize only the touched files to
UTF-8 + LF, add/strengthen `.gitattributes` rules such as `*.vue text eol=lf`,
rerun tests/build, then commit the normalization separately when appropriate.

### 23. Git-Bash redirection to `NUL` creates a real reserved-name file

On this Windows host, terminal commands run through Git-Bash/MSYS. A command or test that uses Windows-style redirection such as `>NUL` can create a real repository file named `NUL`. Git for Windows may then fail while staging with:

```text
fatal: mmap failed: Invalid argument
```

Diagnosis and repair:

```bash
git status --short       # look for `?? NUL`
stat -c '%n %s bytes' NUL
rm -f NUL
git add -A
git diff --cached --check
```

If `git add` still fails after removing `NUL`, the underlying issue may be filesystem-level (mmap failure on the drive partition). In that case, retry the command from a fresh shell or use `git add <specific-file>...` to stage files individually, isolating the problematic path.

Prevention: use POSIX redirection in Git-Bash (`>/dev/null 2>&1`), not `>NUL`. If a build script deliberately invokes `cmd.exe`, keep `NUL` only inside the quoted `cmd.exe /c` command.

### 25. 抖音开发者工具 CDP 交互（computer_use 返回空时的后备）

当 `computer_use(action='capture')` 对 抖音开发者工具 返回 0×0 空截图时，该工具的 Electron 进程自带 CDP 服务器（默认端口 `127.0.0.1:8935`），可以直接通过 HTTP POST 操作。

**发现端口上的所有页面：**
```bash
curl --noproxy '*' -s http://127.0.0.1:8935/json | python -c "import json,sys; [print(x.get('title'),x.get('type')) for x in json.load(sys.stdin)]"
```

**两个关键页面：**
- 工作台 → title 包含 `workbenchMode=workbench`
- 模拟器 Webview → title 包含 `MiniApp Webview`

**三种 CDP 操作：**

| 操作 | 脚本 | 参数 |
|---|---|---|
| 执行 JS | `node .tmp/cdp-eval.mjs '<title>' '<js>'` | title 子串 + JS 表达式 |
| 点击坐标 | `node .tmp/cdp-click.mjs '<title>' <x> <y>` | title 子串 + x y 坐标 |
| 截图保存 | `node .tmp/cdp-shot.mjs '<title>' '<output.png>'` | title 子串 + 输出路径 |

**查找工具栏按钮：** 抖音开发者工具的"上传/编译/预览"等按钮不是 `<button>` 标签，而是 `<div class="tila-toolbar-item-container">`。用 `textContent` 而非 `innerText` 查找，因为嵌套元素有 aria-hidden。

```js
const btn = [...document.querySelectorAll('div,span')]
  .find(e => e.textContent.trim() === '上传' && e.offsetWidth > 0);
const {x, y} = btn.getBoundingClientRect();
// 点击 (x+5, y+5)
```

**陷阱：** 截图命令可能因 Webview 加载中超时；编译后 Webview 短暂变白需等待 3-5 秒。

### 26. Git clone into Windows paths with spaces from Git-Bash/MSYS

When cloning into paths such as `D:\All projects\Repo` from Hermes on Windows,
Git-Bash/MSYS path conversion can be fragile after an interrupted clone or when
the destination contains spaces. A POSIX path like `/d/All projects/Repo` may be
visible to Python or `find`, while `git clone` still reports the destination as
non-empty or shell `cd` intermittently fails.

**Robust pattern:** convert the POSIX destination to a native Windows path for
`git clone`, then use the POSIX path for verification and follow-up commands:

```bash
TARGET_POSIX='/d/All projects/Repo'
TARGET_WIN=$(cygpath -w "$TARGET_POSIX")
mkdir -p "$(dirname "$TARGET_POSIX")"
GIT_TERMINAL_PROMPT=0 git clone https://github.com/owner/Repo.git "$TARGET_WIN"
cd "$TARGET_POSIX"
git branch --show-current
git rev-parse --short HEAD
git status --short
```

If a previous clone was interrupted, inspect the target first. If it contains
only a partial `.git`, retry safely; if it contains user/project files, do not
remove or overwrite it without explicit scope confirmation.
