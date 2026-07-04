# Codex++ 本地代理路由（Windows）

## 架构

```
Hermes ──→ Codex++ 本地代理 ──→ DeepSeek / GPT
               (127.0.0.1:57322/v1)
```

Codex++ 运行一个本地 HTTP 代理服务器，所有 API 请求先发到代理，由代理转发到实际提供商。Hermes 只需将 `base_url` 指向该代理，无需直连外部 API。

## 配置方法

### 1. 确认 Codex++ 代理在运行

```bash
# 检查端口
netstat -ano | findstr 57322

# 测试 API 连通性 (Chat Completions 格式)
curl -s --max-time 20 http://127.0.0.1:57322/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <从 ~/.codex/auth.json 取出的 Key>" \
  -d '{"model": "deepseek-v4-flash", "messages": [{"role": "user", "content": "hi"}]}'
```

### 2. 配置 Hermes

```bash
# 方式一：从 Codex Desktop 读取 API Key
python3 -c "
import json
with open(r'C:\Users\<USER>\.codex\auth.json') as f:
    key = json.load(f)['OPENAI_API_KEY']
import subprocess
subprocess.run(['hermes', 'config', 'set', 'model.api_key', key])
"

# 方式二：设置 provider
hermes config set model.provider custom
hermes config set model.base_url http://127.0.0.1:57322/v1
hermes config set model.default deepseek-v4-flash

# 重启会话
# /reset
```

### 3. 验证

```bash
hermes chat -q "Hello, what model are you? Reply in 5 words." --quiet
```

## Codex++ 代理特征

| 特性 | 支持情况 |
|------|---------|
| Chat Completions API | ✅ 支持 (`/v1/chat/completions`) |
| Responses API | ✅ 支持 (`/v1/responses`) |
| 认证方式 | Bearer token（`~/.codex/auth.json` 中的 `OPENAI_API_KEY`） |
| 当前可用模型 | `deepseek-v4-pro`, `deepseek-v4-flash` |
| 推理能力 | 两个模型均完整支持 `reasoning_content`（思维链） |
| Pro 注意事项 | 推理过程也消耗 max_tokens 预算，建议设 1000+ |
| 端口 | `57322`（固定，由 Codex++ 管理） |

> Codex++ 代理支持的模型由其内部路由决定，不一定是 OpenAI 兼容模型名。当前仅路由 DeepSeek。两个模型均满血运行。

## 安全风险评估

| 风险 | 等级 | 说明 | 缓解措施 |
|------|------|------|---------|
| 单点依赖 | 🔴 高 | Codex++ 崩溃则 Hermes 全断 | 启动 Hermes 前确认代理运行 |
| 端口冲突 | 🟡 中 | 57322 被占用则代理不可达 | 用 `netstat` 预先确认 |
| 性能损耗 | 🟢 低 | 多一次本地回路（微秒级） | 可忽略 |
| 配置不可移植 | 🟡 中 | 其他机器无 Codex++ 则此配置无效 | 保留直连配置作为备选 |
| 凭证泄露 | 🟢 低 | 使用已有 Codex Key，无新增暴露面 | 不做额外处理 |

## 双轨配置策略（推荐）

在部署包中同时保留两种配置，按目标环境切换：

### 方案 A：有 Codex++ 的机器（当前环境）

```yaml
model:
  default: deepseek-v4-flash
  provider: custom
  base_url: http://127.0.0.1:57322/v1
  api_key: <从 ~/.codex/auth.json 读取>
```

### 方案 B：无 Codex++ 的新机器

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1
  api_key: <从 .env 读取 DEEPSEEK_API_KEY>
```

### 切换命令

```bash
# 切换到代理路由
hermes config set model.provider custom
hermes config set model.base_url http://127.0.0.1:57322/v1

# 切换到直连
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
```

## 故障排除

**代理无响应：**
```bash
# 端口是否监听
netstat -ano | findstr 57322

# 进程是否存在
tasklist | findstr codex

# 杀死残留进程后重启 Codex++
taskkill /F /PID <pid>
```

**认证失败（401）：**
```bash
# 检查 Codex 认证文件是否存在
cat ~/.codex/auth.json

# Key 是否可读
python3 -c "import json; f=open(r'C:\Users\<USER>\.codex\auth.json'); print(json.load(f)['OPENAI_API_KEY'][:12])"
```

**模型不支持：**
响应体包含：`The supported API model names are deepseek-v4-pro or deepseek-v4-flash`
说明该代理没有 GPT 路由，只能换 DeepSeek 模型名。
