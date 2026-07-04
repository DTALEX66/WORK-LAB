# Portable deployment repo checklist

Use this when packaging a repo that should reproduce a Hermes/tool setup on another Windows machine.

## Keep

- `config/`: `config.yaml`, `SOUL.md`, `.env.template`, `auth.json.template` with placeholders only.
- `skills/<category>/<skill>/SKILL.md`: categorized custom skills.
- `tools/`: small config exports only, e.g. `cc-switch-config.json`.
- `README.md`, `TROUBLESHOOTING.md`, setup scripts that copy/enable assets.

## Do not keep

- App bodies/installers: `*.msi`, `*.exe`, `*.dmg`, `*.pkg`, `*.AppImage`, archives.
- Secrets/auth/runtime: `.env`, `auth.json`, OAuth tokens, API keys, `state.db`, `*.db`, logs, cache, venvs, `node_modules`.

## `.gitattributes` baseline

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
*.zip binary
```

## `.gitignore` baseline

```gitignore
.env
*.env
!config/.env.template
auth.json
state.db
*.db
*.sqlite
*.sqlite3
logs/
cache/
.venv/
venv/
node_modules/
*.msi
*.exe
*.dmg
*.pkg
*.AppImage
*.zip
*.7z
*.rar
```

## Verification before push

```bash
git diff --check
python - <<'PY'
from pathlib import Path
bad=[]; nul=[]; crlf=[]
for p in Path('.').rglob('*'):
    if '.git' in p.parts or not p.is_file(): continue
    data=p.read_bytes()
    if b'\x00' in data[:4096]: nul.append(str(p)); continue
    try: data.decode('utf-8')
    except UnicodeDecodeError: bad.append(str(p))
    if b'\r\n' in data: crlf.append(str(p))
print('non_utf8', bad)
print('binary_or_nul', nul)
print('crlf', crlf)
PY
find . -type f \( -iname '*.msi' -o -iname '*.exe' -o -iname '*.zip' -o -iname '*.dmg' -o -iname '*.pkg' -o -iname '*.AppImage' \) -not -path './.git/*' -print
```

After push, compare local and remote branch SHAs and fetch raw README/setup files to verify UTF-8 and LF on GitHub.
