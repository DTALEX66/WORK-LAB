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

### 1a. Fallback: manual step-by-step when .ps1 fails

When a deployment `.ps1` can't run due to encoding (or any other reason),
execute its steps manually in bash instead. Common Hermes deployment steps:

```bash
HERMES_HOME="$HOME/AppData/Local/hermes"

# 1. Verify Hermes installation
which hermes && hermes --version

# 2. Copy config files (backup existing first)
cp "$HERMES_HOME/config.yaml" "$HERMES_HOME/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
cp config/config.yaml "$HERMES_HOME/config.yaml"
cp config/SOUL.md "$HERMES_HOME/SOUL.md"
[ ! -f "$HERMES_HOME/.env" ] && cp config/.env.template "$HERMES_HOME/.env"

# 3. Copy skills
mkdir -p "$HERMES_HOME/skills"
cp -r skills/* "$HERMES_HOME/skills/"

# 4. Install extra deps (find Hermes venv pip)
"$HERMES_HOME/hermes-agent/venv/Scripts/pip.exe" install ddgs

# 5. Enable toolsets + plugins
hermes tools enable x_search
hermes plugins enable web/ddgs
# ... etc

# 6. Verify
hermes doctor
hermes skills list
```

This pattern applies to any PowerShell script blocked by encoding issues —
read the script, understand each step, then run the equivalent bash commands.

#### 1b. Deployment repo path mismatch

Some older Hermes deployment repos assumed a nested pack directory in `setup.ps1`,
but this project keeps config/, skills/, scripts/, templates/, and bin/ at the repo root. When `$PackDir` doesn't exist, the script copies nothing. Fix:

```powershell
# Before (broken):
$PackDir = Join-Path $RepoRoot "Workflow-assistance"

# After (fixed):
$PackDir = $RepoRoot
```

Then run the script or manually execute its steps in bash if encoding also blocks.

### 2. Node.js PATH shadowing

Hermes bundles Node v22 at `AppData/Local/hermes/node/node.exe`, but other tools may appear earlier in `$PATH`.

**Check:** `which node && node --version`

**Fix:** Prepend Hermes Node to PATH:
```bash
export PATH="$HERMES_HOME/node:$PATH"
```

### 3. `child_process.spawn` EINVAL on Windows

On Windows under Git Bash, `.cmd` files are not directly spawnable.

**Fix:** Use `cmd.exe` as the command:
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

### 6. Hermes + CC Switch proxy & OAuth setup

**CC Switch identity:** On this user's machine, CC Switch is **FlyintPro** (commercial GUI)
which wraps the open-source **FlClashCore** kernel. The process running on port 7890 is
`C:\Program Files\FlyintPro\FlClashCore.exe` (PID can be found via `netstat -ano | findstr :7890`).
The GUI frontend is `FlyintPro.exe` and its version is the one that matters (FlClashCore.exe
has no embedded file version). To check the installed CC Switch version:

```bash
python -c "import subprocess; r=subprocess.run(['powershell','-Command',
'(Get-Item \"C:\\Program Files\\FlyintPro\\FlyintPro.exe\").VersionInfo.FileVersion'],
capture_output=True,text=True,timeout=10); print(r.stdout.strip())"
```

The underlying FlClash kernel has independent GitHub releases at
`https://github.com/chen08209/FlClash` — check that separately for kernel-level fixes.

When Hermes runs behind CC Switch proxy (port 7890) for accessing
blocked endpoints like `auth.openai.com` or `chatgpt.com`:

1. **Proxy must be in `.env`** — `HTTPS_PROXY=http://127.0.0.1:7890` AND
   `HTTP_PROXY=http://127.0.0.1:7890`. Without this, Hermes cannot reach
   OAuth endpoints.
2. **Proxy must be exported in the shell** before `hermes auth add openai-codex`:
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
   hermes auth add openai-codex
   ```
3. **OAuth device codes expire** — if the user doesn't complete the
   browser flow quickly, kill the process and re-run.
4. **Verify proxy connectivity** before starting OAuth:
   ```bash
   curl -x http://127.0.0.1:7890 -sI https://auth.openai.com 2>&1 | head -5
   # Look for "200 Connection established"
   ```
5. After OAuth completes, switch provider:
   ```bash
   hermes config set model.provider openai-codex
   hermes config set model.default gpt-5.5
   ```
   Then `/reset` or restart Hermes.

**Pitfall:** setting proxy only in `.env` is not enough for `hermes auth`
— the auth command runs before Hermes reads `.env` for proxy settings,
so you must also `export` the vars in the shell session.

**Pitfall:** `hermes auth add openai-codex` in foreground mode can hit the
default 180s timeout waiting for the user to complete the browser flow.
Use background mode instead:

```bash
terminal(command="export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 && hermes auth add openai-codex", background=true, notify_on_complete=true)
# Then poll for the device code:
process(action="poll", session_id="...")
```

**Pitfall:** Even with CC Switch proxy, `auth.openai.com/codex/device` may
show a Cloudflare "正在进行安全验证" challenge in the agent's headless
browser. The user must open the URL in their own proxy-configured browser
and manually pass the Cloudflare check before entering the device code.

**Pitfall:** `~/.hermes/.env` is a credential store that the `read_file`
tool cannot access directly (defense-in-depth). Use the terminal tool
instead: `grep KEY "$HOME/AppData/Local/hermes/.env"`.

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

### 15. Model/provider switching requires `/reset`

Model and provider changes via `hermes config set` do NOT take effect
in the current session — they are locked at session startup. After
changing provider/model, type `/reset` to start a fresh session with
the new settings.

Quick switch recipes:

```bash
# To GPT via openai-codex (requires OAuth + CC Switch proxy)
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5
# → then /reset

# To DeepSeek (requires DEEPSEEK_API_KEY in .env)
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.default deepseek-v4-flash
# → then /reset
```

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

### 23. Git clone into Windows paths with spaces from Git-Bash/MSYS

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
