# Hermes Ecosystem Update Check

Quick checklist for checking all three tools (Hermes Agent, Codex CLI, CC Switch)
for available updates.

## 1. Hermes Agent

```bash
# Installed version
hermes --version
# → Hermes Agent v0.17.0 (2026.6.19) · upstream 3a55f666
#   "Update available: N commits behind" means main branch is ahead of installed tag

# Latest release tag (requires proxy on this machine)
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
curl -s --max-time 15 "https://api.github.com/repos/NousResearch/hermes-agent/releases/latest" \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'{d.get(\"tag_name\")} ({d.get(\"published_at\",\"\")[:10]})')"

# Latest main-branch commits (5 most recent)
curl -s --max-time 15 "https://api.github.com/repos/NousResearch/hermes-agent/commits?per_page=5" \
  | python -c "
import sys,json
for c in json.load(sys.stdin)[:5]:
    print(f'{c[\"sha\"][:8]} ({c[\"commit\"][\"committer\"][\"date\"][:10]}) {c[\"commit\"][\"message\"].split(chr(10))[0]}')
"

# Update
hermes update
```

## 2. Codex CLI

```bash
# Installed version (Codex lives in WindowsApps, not on git-bash PATH)
cmd.exe //c "codex --version"
# → codex-cli 0.142.4

# Latest npm version
npm view @openai/codex version
# or via proxy if needed:
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
npm view @openai/codex version

# Latest release changelog
curl -s --max-time 15 "https://api.github.com/repos/openai/codex/releases?per_page=3" \
  | python -c "
import sys,json
for r in json.load(sys.stdin)[:3]:
    print(f'{r.get(\"tag_name\",\"?\")} ({r.get(\"published_at\",\"?\")[:10]})')
"

# Get changelog for a specific version
curl -s --max-time 15 "https://api.github.com/repos/openai/codex/releases/tags/rust-v0.142.5" \
  | python -c "import sys,json; print(json.load(sys.stdin).get('body','')[:600])"

# Update
# Prefer Codex Desktop's updater. A global npm update changes user-wide state
# and requires explicit approval, version/source review, and a rollback plan.
```

## 3. CC Switch desktop app

```bash
# CC Switch is a separate desktop app. Do not infer it from a proxy port or
# from FlyintPro/FlClash processes.
# Get the installed executable version (adjust only if the user chose a custom install path):
python -c "
import subprocess
r = subprocess.run(['powershell', '-Command',
    '(Get-Item \"$env:LOCALAPPDATA\\Programs\\CC Switch\\cc-switch.exe\").VersionInfo.FileVersion'],
    capture_output=True, text=True, timeout=10)
print('CC Switch version:', r.stdout.strip())
"

# Use CC Switch's About/update UI or its documented official release channel.
# A local proxy's port (for example 7890) is only a network-route diagnostic.
```

## 4. DTALEX66/hermes Deployment Repo

When checking the user's deployment pack repo (separate from Hermes upstream):

```bash
cd /c/Users/admin/hermes

# Check for upstream commits
git fetch origin
git log --oneline HEAD..origin/main

# Diff summary
git diff --stat origin/main

# List files only in deployed (not upstream) vs only upstream (not deployed)
comm -23 <(git ls-tree -r HEAD --name-only | sort) <(git ls-tree -r origin/main --name-only | sort)
comm -13 <(git ls-tree -r HEAD --name-only | sort) <(git ls-tree -r origin/main --name-only | sort)

# Pull to update
git pull origin main
```
