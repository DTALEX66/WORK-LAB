# GitHub Credential Extraction on Windows

## Context

On Windows, `gh auth status` may fail with `not logged in` even though GitHub CLI already has a token in the Windows Credential Store (managed by GCM — Git Credential Manager). The GCM token often exists because another tool (GitHub Desktop, Codex, `git push`, Obsidian Git plugin) configured it.

Run these to find stored GitHub credentials:

```powershell
# List Windows credentials matching "github"
cmdkey /list | Select-String github
```

Expected output: `LegacyGeneric:target=GitHub - https://api.github.com/<USERNAME>`

## Extraction via pywin32

**Prerequisite:** `pip install pywin32`

```python
import win32cred

cred = win32cred.CredRead(
    'GitHub - https://api.github.com/<USERNAME>',
    win32cred.CRED_TYPE_GENERIC
)
token = cred['CredentialBlob'].decode('utf-8').rstrip('\x00').strip()
```

The blob is **UTF-8**, not UTF-16-LE. The result is a `gho_...` or `github_pat_...` string.

## Using Without `gh` CLI

The token from Windows Credential Store typically has `repo` scope but may lack `read:org`. This means:

- `gh auth login --with-token` → FAILS with `error validating token: missing required scope 'read:org'`
- Direct API calls via `curl -H "Authorization: token $TOKEN"` → WORKS fine
- `git push` via HTTPS → WORKS (GCM handles it transparently)
- PR creation via GitHub REST API → WORKS

Use the REST API directly when `gh` refuses the token:

```python
import urllib.request, json

data = json.dumps({'title': '...', 'head': 'branch', 'base': 'main', 'body': '...'}).encode()
req = urllib.request.Request(
    'https://api.github.com/repos/OWNER/REPO/pulls',
    data=data,
    headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'},
    method='POST'
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())  # result['html_url'] has the PR URL
```

## Where to Look First

When credentials aren't immediately obvious:

1. `~/.ssh/` — SSH keys
2. `~/.git-credentials` — plaintext stored tokens
3. `~/.codex/auth.json` — Codex API keys
4. `~/.codex/config.toml` — Codex config
5. **Windows Credential Store** — via `cmdkey /list` (GCM storage)
6. Existing project `.git/config` — remote URLs (HTTPS vs SSH tell you which auth method is used)
7. Project `.env`, `config/` dirs, or shell scripts — may reference tokens
