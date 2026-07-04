# Aether-Radar Next.js Build Fix on Windows

## Context

Aether-Radar v3.1, branch `codex/consolidate-warehouse-projects`. Next.js 16.2.9. Hermes desktop app running on Windows 10, Git Bash shell.

## Manifest

| Symptom | Error | Root cause | Fix |
|---|---|---|---|
| `npm ci` and `npm install` hang then fail | `Exit handler never called!` + `ETIMEDOUT` on every package | `package-lock.json` hardcoded OpenAI internal Artifactory URLs (`packages.applied-caas-gateway1.internal.api.openai.org`) | `rm -rf node_modules package-lock.json && npm install --ignore-scripts --no-audit --no-fund` |
| `npm run build:ci` fails | `spawn EINVAL` at `build-ci.mjs:9` | `child_process.spawn('npx.cmd')` not supported in Git Bash | Patch `scripts/build-ci.mjs` to use `cmd.exe /d /s /c 'npx next build'` on Windows |
| `node --version` shows old version | Another Node (WeChat Dev Tools) higher in $PATH | Shadowed Hermes v22 | `export PATH="$HERMES_HOME/node:$PATH"` |

## Exact fix applied to build-ci.mjs

```js
// Before (line 9 of scripts/build-ci.mjs):
const child = spawn(process.platform === 'win32' ? 'npx.cmd' : 'npx', ['next', 'build'], {
  stdio: 'inherit',
  env,
});

// After:
const child = spawn(
  process.platform === 'win32'
    ? process.env.COMSPEC || 'cmd.exe'
    : 'npx',
  process.platform === 'win32' ? ['/d', '/s', '/c', 'npx next build'] : ['next', 'build'],
  { stdio: 'inherit', env, shell: false },
);
```

## Git commit

```
b591e90 v3.1: restore full Node pipeline verification
```

## Files changed

- `next-app/package-lock.json` — regenerated (npmmirror registry)
- `next-app/scripts/build-ci.mjs` — Windows spawn fix
- `release_artifacts/v3_1_release_manifest.{json,md}` — updated for 227 files
- `.gitignore` — added `*.tsbuildinfo`
