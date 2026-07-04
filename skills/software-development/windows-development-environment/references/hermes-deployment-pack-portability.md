# Hermes deployment pack portability checklist

Use this when packaging a Hermes repo so another Windows machine can clone it and run the same setup.

## Repository shape

- `config/` — `config.yaml`, `SOUL.md`, `.env.template`, `auth.json.template`.
- `skills/<category>/<skill>/SKILL.md` — preserve categories such as `software-development/` and `model-switch/`.
- `tools/` — installers and exported tool configs; installers are binary.
- `memories/` — reference only unless the user explicitly wants to overwrite memory on a target machine.
- `README.md` / `TROUBLESHOOTING.md` — post-clone manual steps and known pitfalls.

## Script portability

A setup script in the repo root should treat the script directory as the pack root:

```bash
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
PACK_DIR="$REPO_ROOT"
```

```powershell
$RepoRoot = $PSScriptRoot
$PackDir = $RepoRoot
```

Avoid `dirname "$0"/..` or `Split-Path -Parent $PSScriptRoot` unless the script intentionally lives inside a subdirectory.

## Secrets and OAuth

- Do not commit live `.env`, `auth.json`, API keys, OAuth tokens, session DBs, logs, or caches.
- Commit templates with blank values, e.g. `DEEPSEEK_API_KEY=`.
- ChatGPT/Codex OAuth must be repeated on each new machine with `hermes auth add openai-codex`; do not copy the real token file.
- Explain that provider/model changes need `/reset` or a Hermes restart.

## Encoding and line endings

Add `.gitattributes`:

```gitattributes
* text=auto eol=lf
*.sh text eol=lf
*.ps1 text eol=lf
*.md text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
*.json text eol=lf
*.template text eol=lf
*.msi binary
*.exe binary
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.zip binary
```

Normalize important text files to UTF-8 + LF before committing.

## Verification commands

```bash
# Text decode + binary detection
python - <<'PY'
from pathlib import Path
bad=[]; nul=[]
for p in Path('.').rglob('*'):
    if '.git' in p.parts or not p.is_file():
        continue
    data=p.read_bytes()
    if b'\x00' in data[:4096]:
        nul.append(str(p)); continue
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        bad.append(str(p))
print('non_utf8', bad)
print('binary_or_nul', nul)
PY

bash -n setup.sh
git diff --check
```

If PyYAML is available, also parse `config/config.yaml`.

After push, verify the remote raw files decode as UTF-8 and have LF-only line endings when encoding matters.
