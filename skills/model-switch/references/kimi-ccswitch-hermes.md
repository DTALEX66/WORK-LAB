# Kimi / CC Switch → Hermes 接入与验证

## 适用场景

用户已在 CC Switch 配好 Kimi/Moonshot provider，希望 Hermes 复用同一 API-key/provider，并确认模型是否真实路由到指定 Kimi 模型（例如 `kimi-k3`）。

## 安全边界

- 只读解析 `~/.cc-switch/cc-switch.db` 的 provider metadata；不要打印、复制到聊天或记录原始 API key。
- 可把 key 写入 Hermes `$HERMES_HOME/.env`，但输出中一律 `[REDACTED]`。
- 不读取/输出 `auth.json`、OAuth token、浏览器 cookie、Windows Credential Store。

## 接入步骤

1. 在 CC Switch SQLite DB 中定位 Kimi provider：
   - `providers.name` 或 `settings_config` 包含 `Kimi` / `moonshot`。
   - `settings_config.options.baseURL` 通常为 `https://api.moonshot.cn/v1`。
   - `settings_config.options.apiKey` 是要复制到 Hermes `.env` 的密钥，禁止打印。
   - `settings_config.models` 是 CC Switch 侧模型列表；可能比 Hermes picker 新。
2. 写入 Hermes `.env`：
   - `KIMI_API_KEY=[REDACTED]`
   - `KIMI_CN_API_KEY=[REDACTED]`（如果使用 `api.moonshot.cn/v1`，便于 Hermes 的 CN provider/status 路径识别）
   - `KIMI_BASE_URL=https://api.moonshot.cn/v1`
3. 写入 Hermes config：
   - `model.provider=kimi-coding`
   - `model.default=<目标模型，如 kimi-k3>`
   - `model.base_url=https://api.moonshot.cn/v1`
4. `/reset` 或新会话后生效；当前已启动的会话模型/provider 已冻结。

## 当前三条推荐切换线

```bash
python scripts/workflow/switch_model.py kimi      # Kimi K3
python scripts/workflow/switch_model.py deepseek  # DeepSeek V4
python scripts/workflow/switch_model.py gpt       # ChatGPT 5.6
```

每次切换后用 `hermes chat -q` marker 验证真实推理，再提示 `/reset` 或新会话。

## 重要陷阱：模型列表 ≠ 实际可用模型全集

Hermes 的 `/model` / picker 使用内置 curated list，不会自动读取 CC Switch DB 的 `settings_config.models`。因此 CC Switch 中已有的新模型（如 `kimi-k3`）可能不出现在 Hermes 模型列表里，但仍可通过配置或 `-m kimi-k3` 调用。

判断标准不是“列表里有没有”，而是 API / Hermes live marker 是否真实成功。

## Kimi K3 真实性验证模式

不要问模型“你是谁”。应直接验证服务端响应：

1. 直接请求 Moonshot OpenAI-compatible endpoint：
   - `POST {KIMI_BASE_URL}/chat/completions`
   - body 中 `model: "kimi-k3"`
2. 对 K3 使用 `temperature: 1`。该模型会拒绝 `temperature: 0`，错误为 `invalid temperature: only 1 is allowed for this model`；这反而说明服务端识别到了 `kimi-k3` 且有模型专属参数约束。
3. 验证返回中：
   - HTTP 200
   - `response_model == "kimi-k3"`
   - `object == "chat.completion"`
   - `usage.completion_tokens_details.reasoning_tokens` 可作为推理路径证据（若出现）
4. 再请求一个不存在模型名（如 `kimi-definitely-not-a-real-model`），应返回 404 `resource_not_found_error`。这证明不是任意 model string 都被静默映射。

可确认的结论：`Hermes → Moonshot/Kimi API → request model kimi-k3 → response model kimi-k3`。不要夸大为“外部可证明后端内部权重等级”；外部只能证明 API 暴露并服务端确认的模型 ID 与路由。

## 推荐汇报格式

- CC Switch 侧模型名列表：只列模型名，不输出 key。
- Hermes config：provider/model/base_url。
- Live marker：`hermes chat --provider kimi-coding -m kimi-k3 ...` 或默认模型 marker。
- Direct API proof：request_model、response_model、HTTP status、usage keys；key 前缀最多脱敏显示，不显示完整值。
