# Third-Party Proxy Setup (CC Switch) for Network-Restricted Environments

## Problem

Network firewalls block all OpenAI-related domains:
- `api.openai.com` — TCP timeout (firewall)
- `chatgpt.com` — TCP timeout (firewall)
- `auth.openai.com` — may be reachable initially, then switch to 403 (WAF block)

Even though `hermes auth add openai-codex` OAuth succeeds (via a different CDN IP range), the actual API calls to `chatgpt.com/backend-api/codex` fail because the inference endpoint uses a different IP range that IS blocked.

The OAuth credential is saved correctly and works on unrestricted networks — the credential itself is not the problem.

## Solution: Route ALL Hermes traffic through a third-party proxy

Use a proxy tool (CC Switch, Clash, V2Ray, etc.) that bypasses the DNS/network block. The proxy runs locally on a fixed port (e.g. 7890 for CC Switch) and forwards traffic to the actual API endpoints.

## Architecture

```
Hermes ──→ CC Switch (:7890) ──→ ChatGPT OAuth ──→ GPT-5.5
```

Two separate mechanisms work together:
1. **`HTTPS_PROXY` env var** — routes all outbound HTTPS through the proxy
2. **`hermes auth add openai-codex`** — provides OAuth credentials for ChatGPT

## Setup Steps

### 1. Install and start CC Switch

Download and install CC Switch (v3.16.4+). After starting, verify the proxy is listening:
```bash
netstat -ano | grep LISTEN | grep 7890
```

### 2. Configure proxy in Hermes .env

```env
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890
```

Write via:
```bash
echo 'HTTPS_PROXY=http://127.0.0.1:7890' >> "$HERMES_HOME/.env"
echo 'HTTP_PROXY=http://127.0.0.1:7890' >> "$HERMES_HOME/.env"
```

### 3. OAuth authentication (first time only)

```bash
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
hermes auth add openai-codex
# Browser opens → log into ChatGPT account
# Required: ChatGPT Plus or Pro subscription
```

### 4. Switch to OpenAI Codex provider

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5
# Fully restart Hermes (.env vars read at startup)
```

## Verification

```bash
# 1. Check proxy is running
curl -sI --max-time 5 --proxy http://127.0.0.1:7890 https://chatgpt.com
# → HTTP/1.1 200 Connection established

# 2. Test Hermes with GPT
hermes chat -q "What model are you? Reply model name only." --quiet
# → gpt-5.5
```

## Model Compatibility

Tested working with ChatGPT Plus subscription:

| Model | Status |
|-------|--------|
| `gpt-5.5` | ✅ Works |
| `gpt-4.1` | ❌ Not supported with ChatGPT account |
| `gpt-4o` | ❌ Not supported with ChatGPT account |
| `gpt-4o-mini` | ❌ Not supported |
| `o3` | ❌ Not supported |
| `o4-mini` | ❌ Not supported |

> The `openai-codex` provider routes to a different model set than the raw OpenAI API. ChatGPT subscriptions get access to `gpt-5.5` through this endpoint. Other model names return 400 errors.

## CC Switch vs. Codex++ Proxy — Comparison

| Aspect | Codex++ Proxy | CC Switch Proxy |
|--------|:-------------:|:---------------:|
| Config mechanism | `custom` provider → `base_url` | `HTTPS_PROXY` env var |
| Provider used | `custom` | `openai-codex` |
| Models available | DeepSeek only | GPT-5.5 (via OAuth) |
| Dependencies | Codex++ must be running | CC Switch must be running |
| Port | 57322 | 7890 |
| Can access OpenAI? | No (Codex++ only routes DeepSeek) | Yes (proxy bypasses firewall) |
| Persistence | Config in config.yaml | Env vars in .env |

## Duplicate provider detection

When `.env` contains BOTH `OPENAI_API_KEY` (from old Codex auth) AND the `openai-codex` OAuth credential, Hermes loads TWO providers:
- `openai-codex` (OAuth, 4 models: gpt-5.5 etc.)
- `openai-api` (API key, 10 models: gpt-5.5, gpt-5.4, gpt-4.1, gpt-4o, etc.)

Result: duplicate model entries in `hermes model` list. Fix by removing the API key:

```bash
hermes config set model.api_key ''
# Also remove OPENAI_API_KEY from .env
```

## Pitfalls

- **Do not confuse** `custom` provider (Codex++ proxy) with `openai-codex` provider (ChatGPT OAuth). They are different mechanisms with different auth.
- **Do not set both proxies** — `HTTPS_PROXY` affects ALL Hermes traffic. Only set it when CC Switch is running.
- **`auth.openai.com` returning 403 instead of timeout** means the CDN/WAF is blocking the request, not a network firewall. The auth endpoint may work early in a session but later return 403 after Codex is reinstalled — this is a WAF-level block, not a credential problem. Diagnostic:
  - 403 = WAF block (domain IS reachable, requests are rejected)
  - timeout = firewall (TCP cannot establish)
- **After switching between providers**, always `/reset` to clear cached credentials and refresh the configuration.
- **The .env proxy vars take effect at Hermes startup** — if you add them mid-session, `/reset` won't re-read .env. Restart Hermes completely.
- **Codex auth.json format can change** after re-authenticating: from `{"OPENAI_API_KEY": "sk-..."}` (API key, used by `custom` provider) to `{"auth_mode": "chatgpt", "tokens": {...}}` (OAuth tokens, used by `openai-codex` provider). The old format only works for `custom` provider; the new format only works for `openai-codex`.
