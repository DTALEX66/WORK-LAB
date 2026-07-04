# Node PATH migration on Windows Git Bash / Hermes

Use when `node`, `npm`, `npx`, or `corepack` resolve to different installations, especially when WeChat Developer Tools shadows Node via HKLM/system PATH.

## Symptom

```bash
command -v node && node --version && node -p "process.execPath"
command -v npm && npm --version
command -v npx && npx --version
command -v corepack && corepack --version
```

Bad mixed state example:

```text
node -> D:/Program Files (x86)/Tencent/微信web开发者工具/node  # old Node, e.g. v16
npm  -> C:/Users/<user>/AppData/Local/hermes/node/npm          # different distribution
npx  -> C:/Users/<user>/AppData/Local/hermes/node/npx
```

This can break Vite/Next/uni-app builds because the executable and package manager are from different Node distributions.

## Preferred fix without touching WeChat

1. Install an independent Node:

```bash
scoop install nodejs-lts
scoop reset nodejs-lts
```

2. Install/refresh Corepack from the same Node distribution if missing or shadowed:

```bash
export PATH="$HOME/scoop/apps/nodejs-lts/current:$HOME/scoop/persist/nodejs-lts/bin:$PATH"
npm install -g corepack@latest
```

3. Add durable wrappers. Use both `~/bin` (persists across Git upgrades) and Git Bash `usr/local/bin` (often first in Hermes/Git-Bash PATH). The wrapper must prepend the real Node directory before launching Node; otherwise Node's own `child_process` calls may still find a later `node.exe` such as Hermes bundled Node or WeChat Node.

```bash
for dir in "$HOME/bin" "$HOME/scoop/apps/git/current/usr/local/bin"; do
  mkdir -p "$dir"
  cat > "$dir/node" <<'SH'
#!/usr/bin/env bash
NODE_HOME="$HOME/scoop/apps/nodejs-lts/current"
NODE_GLOBAL="$HOME/scoop/persist/nodejs-lts/bin"
export PATH="$NODE_HOME:$NODE_GLOBAL:$PATH"
exec "$NODE_HOME/node.exe" "$@"
SH
  cat > "$dir/npm" <<'SH'
#!/usr/bin/env bash
NODE_HOME="$HOME/scoop/apps/nodejs-lts/current"
NODE_GLOBAL="$HOME/scoop/persist/nodejs-lts/bin"
export PATH="$NODE_HOME:$NODE_GLOBAL:$PATH"
exec "$NODE_HOME/npm.cmd" "$@"
SH
  cat > "$dir/npx" <<'SH'
#!/usr/bin/env bash
NODE_HOME="$HOME/scoop/apps/nodejs-lts/current"
NODE_GLOBAL="$HOME/scoop/persist/nodejs-lts/bin"
export PATH="$NODE_HOME:$NODE_GLOBAL:$PATH"
exec "$NODE_HOME/npx.cmd" "$@"
SH
  cat > "$dir/corepack" <<'SH'
#!/usr/bin/env bash
NODE_HOME="$HOME/scoop/apps/nodejs-lts/current"
NODE_GLOBAL="$HOME/scoop/persist/nodejs-lts/bin"
export PATH="$NODE_HOME:$NODE_GLOBAL:$PATH"
exec "$NODE_HOME/corepack.cmd" "$@"
SH
  chmod +x "$dir/node" "$dir/npm" "$dir/npx" "$dir/corepack"
done
hash -r 2>/dev/null || true
```

Optional: add `.cmd` wrappers in the same high-priority directory for tools that use `cmd.exe /c where`, but do not rely on `child_process.execFileSync('npm')` to run `.cmd` files directly. On Windows, Node should use `npm.cmd` explicitly or `shell: true`.

## Verification

```bash
# Put the real Scoop Node directory before any old node.exe. This matters for
# Windows Python subprocess/CreateProcess too: it may prefer node.exe found
# later in PATH over bash-only wrappers such as ~/bin/node or node.CMD.
export PATH="$HOME/scoop/apps/nodejs-lts/current:$HOME/scoop/persist/nodejs-lts/bin:$HOME/scoop/apps/git/current/usr/local/bin:$HOME/bin:$PATH"
command -v node && node --version && node -p "process.execPath"
command -v npm && npm --version
command -v npx && npx --version
command -v corepack && corepack --version
node -e "const cp=require('child_process'); console.log(cp.execSync('node --version && npm --version && npx --version && corepack --version',{encoding:'utf8'})); console.log(process.execPath, process.version)"
python - <<'PY'
import shutil, subprocess
print('python which node =', shutil.which('node'))
print(subprocess.run(['node','-p','process.execPath'], text=True, stdout=subprocess.PIPE).stdout.strip())
PY
node -p "process.execPath.includes('Tencent') || process.execPath.includes('微信')"
hermes doctor 2>/dev/null | sed -n '/◆ External Tools/,/◆ API Connectivity/p'
```

Expected:

```text
node/npm/npx/corepack resolve to the wrapper or Scoop nodejs-lts
process.execPath points to C:\Users\<user>\scoop\apps\nodejs-lts\current\node.exe
Tencent/微信 check returns false
Hermes doctor reports Node.js/browser tooling OK
```

## Project compatibility checks

Before declaring the migration complete, inspect important repos:

```bash
node --version
npm --version
python - <<'PY'
from pathlib import Path
import json
for root in [Path('C:/Users/ALEX/AppData/Local/hermes/hermes-agent'), Path('D:/All projects/MINIGAME')]:
    pkg=root/'package.json'
    print('\n##', root)
    if pkg.exists():
        data=json.loads(pkg.read_text(encoding='utf-8'))
        print({'name': data.get('name'), 'engines': data.get('engines'), 'packageManager': data.get('packageManager')})
PY
```

Run at least one real command per active Node project. If `npm audit` fails with `/-/npm/v1/security/* not implemented yet`, check `npm config get registry`: mirrors such as `https://registry.npmmirror.com` may not implement audit. Re-run audit with `--registry=https://registry.npmjs.org` before blaming Node.

## Pitfalls

- HKLM/system PATH edits require admin rights. If removing the WeChat path fails with `WinError 5`, use the wrapper method instead.
- Do not delete or modify `D:/Program Files (x86)/Tencent/微信web开发者工具`; only change PATH precedence or wrappers.
- User-level PATH may not beat HKLM/system PATH in native Windows shells. The wrapper method is specifically for Hermes/Git-Bash; native PowerShell/CMD may still need an elevated system PATH cleanup.
- After registry PATH changes, already-running shells keep their old PATH. Restart terminals for global changes.
