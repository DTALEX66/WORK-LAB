# CC Switch + Hermes + Codex 订阅排查笔记

## 核心认识

用户的 GPT 通道是 ChatGPT/Codex 订阅 OAuth（`openai-codex` provider，device-code 登录），不是 OpenAI API Key。不要把 `OPENAI_API_KEY` 当成前提。

典型状态：

- GPT：`openai-codex` OAuth，可用模型如 `gpt-5.5`。
- DeepSeek：`.env` 里的 `DEEPSEEK_API_KEY`。
- CC Switch：可能只在 `127.0.0.1:7890` 做网络代理，也可能额外启用 API Router 接管模型路由。

## 两种 CC Switch 角色

### 1. 网络代理层

链路：

```text
Hermes / Codex
  -> HTTP_PROXY / HTTPS_PROXY = http://127.0.0.1:7890
  -> CC Switch / 本地代理
  -> ChatGPT/Codex 官方后端
```

这只解决出海和连接问题，不代表 CC Switch 已经统一调度模型。

检查：

```bash
echo "HTTPS_PROXY=$HTTPS_PROXY"
echo "HTTP_PROXY=$HTTP_PROXY"
curl --proxy http://127.0.0.1:7890 -I https://chatgpt.com/ --max-time 10
```

### 2. API Router / 模型中转层

目标链路：

```text
Hermes / Codex
  -> CC Switch API Router，本地端口如 15721 / 5101 / 7575
  -> GPT 订阅 OAuth / DeepSeek API / Claude / Gemini
```

只有本地 API Router 端口实际监听、并且对应 app_type 的 proxy/enabled 开关打开时，才算 CC Switch 接管模型路由。

检查：

```bash
for port in 15721 5101 7575; do
  echo "port $port"
  curl --noproxy '*' -sS --max-time 3 "http://127.0.0.1:$port/" || true
done
```

如果这些端口都不通，但 7890 通，则当前 CC Switch 只是网络代理。

## Hermes 通道验证

```bash
# GPT 订阅 OAuth 是否通
hermes auth list openai-codex
hermes chat -Q --provider openai-codex -m gpt-5.5 -q '只回复 OK_GPT_SUBSCRIPTION'

# DeepSeek API 是否通
hermes auth list deepseek
hermes chat -Q --provider deepseek -m deepseek-v4-flash -q '只回复 OK_DEEPSEEK_API'
```

成功返回 `OK_GPT_SUBSCRIPTION` 表示 GPT 订阅链路可用；成功返回 `OK_DEEPSEEK_API` 表示 DeepSeek API 链路可用。

## CC Switch 本地状态检查

可读这些状态，不要打印 token 明文：

- `C:\Users\admin\.cc-switch\cc-switch.db`
- `C:\Users\admin\.cc-switch\logs\cc-switch.log`
- `C:\Users\admin\hermes\tools\cc-switch-config.json`（如果存在）

SQLite 表常见含义：

- `proxy_config`: 每个 app_type 的 API proxy 开关、监听端口、重试配置。
- `providers`: Codex/Claude/Gemini/Hermes provider 配置，可能包含 OAuth token，输出时必须脱敏。
- `mcp_servers`: MCP 是否启用于 codex/hermes/claude 等。
- `prompts`: 从 Codex/Hermes 等导入的全局提示词。

关键判断：

```text
proxy_config.codex.enabled = 0 且 proxy_enabled = 0
```

表示 Codex API Router 未启用。

## 配置方向

稳妥版：

- Hermes 保持自己切 GPT/DeepSeek。
- CC Switch 只作为 7890 网络代理与 Codex 配置/日志管理。

完整联动版：

- 在 CC Switch UI 中启用 Codex/Hermes API Proxy。
- 添加/确认 GPT 订阅 OAuth provider 与 DeepSeek provider。
- 确认 API Router 端口监听。
- 再将 Hermes/Codex 的 base_url 指向 CC Switch 本地 API Router。

不要在 API Router 未监听前贸然把 Hermes 的 `model.base_url` 改到 CC Switch，否则会导致 Hermes 无法对话。

## 用户沟通注意

用户强调“GPT 没有 API，只有订阅”时，回答应围绕 OAuth 订阅链路和 CC Switch 如何接管订阅登录态展开，不要要求 OpenAI API Key。