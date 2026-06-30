# Hermes Agent 部署包

> 一键部署 Hermes Agent 配置/技能/插件，支持三种路由方案

## 📦 目录结构

```
hermes-pack/
├── config/
│   ├── config.yaml            ← 完整配置（GPT + CC Switch 代理）
│   ├── SOUL.md                ← Agent 人格设定
│   ├── .env.template          ← 环境变量（含代理配置）
│   └── auth.json.template     ← 凭证模板
├── skills/software-development/
│   ├── screenlingua/          ← 截图翻译项目技能
│   ├── python-testing/        ← Python 测试约定
│   └── windows-development/   ← Windows 开发排坑
├── tools/
│   ├── CC-Switch-v3.16.4-Windows.msi  ← CC Switch 安装包
│   └── cc-switch-config.json          ← CC Switch 配置导出
├── memories/MEMORY.md         ← 跨会话记忆参考
├── setup.ps1                  ← Windows 一键部署脚本
├── setup.sh                   ← Linux/macOS 一键部署脚本
└── README.md                  ← 本文件
```

## 🚀 快速部署

```powershell
# Windows（管理员 PowerShell）
git clone git@github.com:DTALEX66/hermes.git
cd hermes
.\setup.ps1
```

```bash
# Linux / macOS
git clone git@github.com:DTALEX66/hermes.git
cd hermes
chmod +x setup.sh && ./setup.sh
```

脚本自动完成：安装 Hermes → 写入配置 → 安装 3 个本地技能 → 安装依赖 → 启用 5 个插件 + 3 个工具集。

---

## 🧭 三种路由方案（官方 Provider 路线）

根据当前机器的网络环境，选择最适合的方案。官方建议用 `hermes model` 或 `hermes setup` 交互式配置，下面给出 CLI 等效命令。

---

### 方案A：Codex++ 本地代理中转

> **适用场景**：本机有 Codex++ 运行时（端口 57322），所有请求统一经过本地代理  
> **不通过 `hermes setup` 选择**，需手动配置 custom provider

```
Hermes ──→ Codex++ 代理 (127.0.0.1:57322) ──→ DeepSeek
```

```bash
# 从 Codex 的 auth.json 读取 API Key
python3 -c "import json;key=json.load(open(r'~/.codex/auth.json'))['OPENAI_API_KEY'];__import__('subprocess').run(['hermes','config','set','model.api_key',key])"

# 配置 custom provider
hermes config set model.provider custom
hermes config set model.base_url http://127.0.0.1:57322/v1
hermes config set model.default deepseek-v4-flash
```

---

### 方案B：DeepSeek 直连（官方 Provider）

> **适用场景**：任意能访问 `api.deepseek.com` 的机器，零依赖  
> **官方文档**：[Hermes AI Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers) → DeepSeek  
> **配置方式**：`DEEPSEEK_API_KEY` in `~/.hermes/.env` (provider: deepseek)

```
Hermes ──→ DeepSeek API (api.deepseek.com)
```

**交互式配置（推荐）：**
```bash
hermes setup
# 选择 DeepSeek，填入 API Key、Base URL、模型
```

**或 CLI 等效：**
```bash
# 1. 在 .env 中写入密钥
echo 'DEEPSEEK_API_KEY=你的密钥' >> "$HERMES_HOME/.env"

# 2. 配置 Provider
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.default deepseek-v4-flash
```

---

### 方案C：OpenAI Codex / ChatGPT OAuth（官方 Provider）

> **适用场景**：网络无限制（能访问 `chatgpt.com`），有 ChatGPT 订阅  
> **官方文档**：[Hermes AI Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers) → OpenAI Codex  
> **配置方式**：`hermes model (ChatGPT OAuth, uses Codex models)`

```
Hermes ──→ ChatGPT Codex API (chatgpt.com/backend-api/codex) ──→ GPT-4o
```

**交互式配置（推荐）：**
```bash
hermes model
# 选择 7. OpenAI → Codex CLI / ChatGPT OAuth
# 完成设备码 OAuth 登录
```

**或 CLI 等效：**
```bash
# 1. OAuth 认证（首次只需一次）
hermes auth add openai-codex
# 浏览器打开 https://auth.openai.com/codex/device，输入验证码

# 2. 切换 Provider
hermes config set model.provider openai-codex
hermes config set model.default gpt-4o
```

> 插件内置 base_url 为 `https://chatgpt.com/backend-api/codex`，无需手动设置

---

### 方案D：CC Switch 代理 + GPT（本机专用）

> **适用场景**：网络被墙的环境，通过 CC Switch 代理翻墙访问 OpenAI  
> **路由**：`Hermes → CC Switch 代理(:7890) → ChatGPT OAuth → GPT-5.5`

**前提：** CC Switch 已安装并运行（代理端口 7890）

```bash
# CC Switch 安装包在 tools/ 目录下
# 运行 CC-Switch-v3.16.4-Windows.msi 安装后启动即可

# .env 中自动配置代理
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890

# OAuth 认证（首次只需一次）
hermes auth add openai-codex
# 浏览器打开 https://auth.openai.com/codex/device，输入验证码

# 切换 Provider
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5
```

---

## 🔄 快速切换方案

`config.yaml` 中已预置三种方案的注释模板，直接编辑切换：

```yaml
# 切换方案A（Codex++ 代理）
model:
  default: deepseek-v4-flash
  provider: custom
  base_url: http://127.0.0.1:57322/v1
  api_key: sk-...

# 切换方案B（DeepSeek 直连）
model:
  default: deepseek-v4-flash
  provider: deepseek
  base_url: https://api.deepseek.com/v1
  api_key: ''

# 切换方案C（GPT OAuth）
model:
  default: gpt-4o
  provider: openai-codex
  base_url: ''
  api_key: ''
```

> ⚠️ 切换方案后需 `/reset` 或重启 Hermes 生效

---

## 🔑 部署后手动配置

### 1. API Key

编辑 `%LOCALAPPDATA%\hermes\.env`：

```env
# 方案B 需要
DEEPSEEK_API_KEY=你的DeepSeek密钥

# 方案C 不需要（OAuth 无密钥）
# 方案A 用到的是 Codex 已有的 Key，自动读取
```

### 2. 加载项目技能

```bash
hermes -s screenlingua
skill_view(name='screenlingua')
```

### 3. 插件生效

插件和工具集需新会话生效：`/reset` 或重启 Hermes。

## 🛠️ 常用命令

```bash
hermes config               # 查看完整配置
hermes config edit          # 编辑配置
hermes model                # 交互式切换模型
hermes skills list          # 查看已安装技能
hermes plugins list         # 查看已安装插件
hermes tools list           # 查看已启用工具集
hermes doctor               # 环境健康检查
hermes auth list            # 查看 OAuth 凭证
```

## ❌ 不包含的内容（需手动配置）

- API 密钥（`.env`）
- OAuth 令牌（`auth.json`）
- 会话历史（`state.db`）
- cron 运行时数据
- 缓存文件和日志

## 📝 备注

- 内置 62 个技能由 Hermes 自动安装
- 部署包仅包含 3 个本地自定义技能（screenlingua/python-testing/windows-dev）
- 建议部署后运行 `hermes doctor` 做全面检查
- 如果 Codex++ 被删除，切到方案B 即可
- 遇到问题请查阅 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 排坑手册
- 包含模型切换技能：说"切换DP"/"切换GPT"一键切换
