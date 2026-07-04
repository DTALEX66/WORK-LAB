# OAuth 凭证同步与模型缓存刷新

## 场景

在同一台机器上同时使用 Codex CLI 和 Hermes + CC Switch 时，OAuth 凭证需要同步到多个位置才能正常工作。

## 凭证存储位置

| 工具 | 凭证文件 | 用途 |
|------|----------|------|
| Codex CLI | `~/.codex/auth.json` | Codex 自身认证 |
| CC Switch | `~/.cc-switch/codex_oauth_auth.json` | CC Switch 代理转发 |
| Hermes | `$HERMES_HOME/auth.json` (credential_pool) | Hermes Provider 调用 |

## 同步方法

Codex CLI 登录 ChatGPT 后，将 token 同步到 CC Switch：

```bash
python3 -c "
import json
with open(r'~/.codex/auth.json') as f:
    codex_auth = json.load(f)
with open(r'~/.cc-switch/codex_oauth_auth.json', 'w') as f:
    json.dump(codex_auth, f, indent=2)
"
```

## 模型缓存刷新

移除 `.env` 中的 API Key（如 `OPENAI_API_KEY`）后，`openai-api` 提供商的模型列表会残留。需清除缓存让 Hermes 重新加载：

```bash
rm "$HERMES_HOME/provider_models_cache.json"
rm "$HERMES_HOME/models_dev_cache.json"
# 新会话自动重建
```

## 删除凭证残留

`auth.json` 的 `credential_pool` 中可能残留已删除的 API Key 条目。它们不影响使用（provider 检查失败后会自动跳过），但会让模型选择列表变长。要彻底清除：

1. 从 `.env` 移除对应的 `*_API_KEY`
2. 清除模型缓存（见上）
3. 重启 Hermes

## 验证凭证有效

```bash
cat "$HERMES_HOME/auth.json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
pool = d.get('credential_pool', {})
for p, entries in pool.items():
    for e in entries:
        print(f'{p}: {e[\"label\"]} ({e[\"auth_type\"]}) last: {e.get(\"last_status\",\"unknown\")}')
"
```
