# Provider Network Troubleshooting on Windows

## Symptom: OAuth succeeds, API calls timeout

The OAuth device-code flow uses `auth.openai.com` (or `auth.anthropic.com`, etc.), while model-inference API calls use separate API endpoints. Network firewalls, corporate proxies, or GFW may block the API endpoint while allowing the auth endpoint.

### API endpoint locations (from plugin source code)

| Provider | API Endpoint | Auth Endpoint |
|----------|-------------|---------------|
| OpenAI direct | `api.openai.com` | — |
| OpenAI Codex (Hermes provider) | `chatgpt.com/backend-api/codex` | `auth.openai.com` |
| Anthropic | `api.anthropic.com` | `auth.anthropic.com` |
| DeepSeek | `api.deepseek.com` | — (API key) |
| OpenRouter | `openrouter.ai` | — (API key) |

> **Key insight:** The `openai-codex` Hermes provider (`plugins/model-providers/openai-codex/__init__.py`) uses `chatgpt.com/backend-api/codex` as its base URL — NOT `api.openai.com`. Both may be blocked by the same firewall rule.

### Check pattern

```bash
echo "=== api.openai.com ===" && curl -sI --max-time 5 https://api.openai.com 2>&1 | head -3
echo "=== chatgpt.com ===" && curl -sI --max-time 5 https://chatgpt.com 2>&1 | head -3
echo "=== auth.openai.com ===" && curl -sI --max-time 5 https://auth.openai.com 2>&1 | head -3
echo "=== api.deepseek.com ===" && curl -sI --max-time 5 https://api.deepseek.com 2>&1 | head -3
echo "=== openrouter.ai ===" && curl -sI --max-time 5 https://openrouter.ai 2>&1 | head -3

# Expected results:
# 200/401 = reachable
# 403 = rate-limited or blocked by WAF
# Connection timed out = network firewall
```

> `auth.openai.com` can change from `200` → `403` after reinstalling Codex (WAF or CDN-level block, different from TCP firewall).

### Finding local proxy ports with netstat

Codex, Codex++, and other desktop apps create local HTTP proxies on dynamic ports:

```bash
# List all local listening ports
netstat -ano | grep LISTEN | grep "127.0.0.1" | sort -t: -k2 -n

# Common Codex ports: 57320-57322
# Codex++ process: codex-plus-plus.exe
# Codex process: Codex.exe / codex.exe (OpenAI dir)
```

Test if a local port accepts OpenAI-compatible requests:
```bash
curl -s --max-time 10 http://127.0.0.1:<PORT>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}]}'
```

Expected outcomes:
- `{"choices":[...]}` = working proxy
- connection refused = wrong port
- `"当前中转未启用 Chat Completions 协议代理"` = proxy exists but only supports Responses API

### Finding provider plugin source code

When the Hermes provider's API endpoint is unclear, check the plugin source directly:

```bash
cat "$HERMES_HOME/hermes-agent/plugins/model-providers/<provider-name>/__init__.py"
```

The `ProviderProfile` object has `base_url` and `auth_type` fields that reveal the actual endpoint.

### Common blocked providers on Chinese networks

| Provider | API endpoint | Status |
|----------|-------------|--------|
| OpenAI | `api.openai.com` | Often blocked |
| ChatGPT backend | `chatgpt.com` | Often blocked |
| Google/Gemini | `generativelanguage.googleapis.com` | Often blocked |
| Anthropic | `api.anthropic.com` | Sometimes blocked |
| DeepSeek | `api.deepseek.com` | Usually reachable |
| OpenRouter | `openrouter.ai` | Usually reachable |

### What works when API is blocked

- **OAuth can still succeed** — `auth.openai.com` may be on a different CDN/IP range
- **API calls fail** even with valid OAuth credentials
- **The OAuth credential is saved** and will work on another machine
- **Workaround 1:** Use a reachable provider (DeepSeek, OpenRouter)
- **Workaround 2:** Route through a local proxy (Codex++ at 57322, see `references/codex++-proxy-routing.md`)
- **Workaround 3:** Route through a third-party proxy via `HTTPS_PROXY` env var (CC Switch etc., see `references/third-party-proxy-setup.md`). This is the only way to use GPT when OpenAI domains are blocked.

## Dual-track architecture (Hermes + Codex parallel)

```text
┌──────────────┐     ┌───────────┐     ┌───────────┐
│  Hermes      │ ──→ │ DeepSeek  │ ──→ │ DeepSeek  │
│  (direct)    │     │ API直连   │     │ API       │
├──────────────┤     └───────────┘     └───────────┘
│  Hermes      │ ──→ │ Codex     │ ──→ │ GPT       │
│  (OAuth)     │     │ OAuth     │     │ (需无墙网)│
├──────────────┤     └───────────┘     └───────────┘
│  Codex CLI   │ ──→ │ Codex++   │ ──→ │ DeepSeek  │
│  (不动)      │     │ (路由层)  │     │ (当前)    │
└──────────────┘     └───────────┘     └───────────┘
```

**Rules:**
1. Never modify `~/.codex/config.toml`
2. Each track can switch independently
3. Codex sessions persist at `~/.codex/sessions/`

## DeepSeek Pro model through Codex++ proxy

Both DeepSeek V4 models work at full capacity:

| Feature | deepseek-v4-flash | deepseek-v4-pro |
|---------|:-----------------:|:---------------:|
| Reasoning content | ✅ | ✅ |
| Full context | ✅ | ✅ |
| Completion finish | `stop` | `stop` |

> Pro model's `reasoning_content` field consumes token budget. Set `max_tokens=1000+`.

## Codex Desktop credential states

Codex Desktop's `~/.codex/auth.json` has two distinct states:

**API key mode** (Codex++ or direct API key):
```json
{
  "OPENAI_API_KEY": "sk-..."
}
```

**ChatGPT OAuth mode** (re-login with ChatGPT account):
```json
{
  "auth_mode": "chatgpt",
  "OPENAI_API_KEY": null,
  "tokens": {
    "id_token": "eyJ...",
    "access_token": "eyJ...",
    "refresh_token": "rt.1..."
  }
}
```

To reuse the API key in Hermes:
```python
import json, subprocess
with open(r'C:\Users\<USER>\.codex\auth.json') as f:
    key = json.load(f)['OPENAI_API_KEY']
subprocess.run(['hermes', 'config', 'set', 'model.api_key', key])
```

> For ChatGPT OAuth mode, use `hermes auth add openai-codex` directly — no key to extract.
