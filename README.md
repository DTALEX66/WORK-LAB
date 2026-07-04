# HERMES + CC Switch + Codex 工作流增强项目

> `Workflow-assistance` 是 DTALEX66 的 HERMES + CC Switch + Codex 工作流增强项目：沉淀 Hermes 配置、CC Switch 代理路径、Codex/GPT OAuth 协作、MCP、技能、脚本、模板和排错手册。
>
> 本仓库只保存可迁移的工作流增强资产；不保存 Hermes、CC Switch、Codex CLI 安装主体，也不保存 `.env`、OAuth `auth.json`、API Key、Token、会话数据库、缓存或日志。

## 🎯 项目定义

- **GitHub 云端项目**：`DTALEX66/Workflow-assistance`，作为跨电脑同步的 HERMES + CC Switch + Codex 工作流增强资产库。
- **本地项目**：`D:\All projects\Workflow-assistance`，作为可编辑、可验证、可提交、可部署的工作流增强源目录。
- **核心目标**：让 Hermes 负责 Agent 执行与配置，CC Switch 负责本地代理/网络通道，Codex/OpenAI OAuth 负责 GPT 订阅模型路径，并把三者的最佳实践固化为脚本、技能、模板和文档。

详见：[docs/workflow/project-definition.md](docs/workflow/project-definition.md)。

## 📦 目录结构

```
Workflow-assistance/
├── config/
│   ├── config.yaml            ← 完整配置（GPT + CC Switch 代理 + workflow MCP）
├── bin/                       ← hermes-npx wrapper（固定 Hermes Node v22）
│   ├── SOUL.md                ← Agent 人格设定
│   ├── .env.template          ← 环境变量（含代理配置）
├── skills/software-development/
│   ├── screenlingua/          ← 截图翻译项目技能
│   ├── python-testing/        ← Python 测试约定
│   └── windows-development/   ← Windows 开发排坑
├── docs/                     ← 工作流/MCP/吸收清单文档
├── templates/                ← Agent 规则、任务单模板
├── scripts/                  ← 安全扫描等辅助脚本
├── setup.ps1                  ← Windows 一键部署脚本
├── setup.sh                   ← Linux/macOS 一键部署脚本
└── README.md                  ← 本文件
```


## 🗂️ 分类说明（上传仓库时保持这个结构）

本仓库按 Hermes 可迁移资源分类，其他电脑 clone 后脚本会按同样分类复制到 Hermes 本地目录：

| 仓库目录 | 部署目标 | 作用 |
|---|---|---|
| `config/` | `%LOCALAPPDATA%\hermes` 或 `~/.hermes` | Hermes 主配置、人格、环境变量模板 |
| `skills/model-switch/` | `skills/model-switch/` | 模型切换技能，例如“切换DP / 切换GPT” |
| `skills/software-development/` | `skills/software-development/` | 开发相关技能：截图翻译、Python 测试、Windows 排坑 |
| `docs/` | 仓库文档 | 工作流吸收清单、MCP 栈、排错和部署说明 |
| `templates/` | 手动复制/项目初始化 | Agent 规则模板、CC Switch 任务单模板 |
| `scripts/` | 手动运行 | 安全扫描、规则检查、模型切换、工作流 doctor |
| `bin/` | `$HERMES_HOME/bin` | MCP Node wrapper，优先使用 Hermes bundled Node |

> 注意：真实 `.env`、OAuth `auth.json`、API Key、Token、会话数据库、Hermes 安装主体、CC Switch 安装主体都不会上传。新电脑必须先自行安装 Hermes/CC Switch，再填写 API Key 并重新执行 OAuth 登录。

## 🖥️ 新电脑完整部署流程

### Windows 推荐流程

```powershell
git clone git@github.com:DTALEX66/Workflow-assistance.git
cd Workflow-assistance
# 先确保本机已经安装 Hermes Agent 主体；本仓库不包含 Hermes 安装器
# 如果 PowerShell 遇到中文编码问题，改用 Git Bash 执行 ./setup.sh
.\setup.ps1
```

如果使用 Git Bash：

```bash
git clone git@github.com:DTALEX66/Workflow-assistance.git
cd Workflow-assistance
# 先确保本机已经安装 Hermes Agent 主体；本仓库不包含 Hermes 安装器
chmod +x setup.sh
./setup.sh
```

部署后必须做三件事：

1. 自行安装 Hermes Agent 主体和（可选）CC Switch 主体；本仓库只提供部署配置和技能插件。
2. 编辑 Hermes 的 `.env`，填入新电脑自己的 `DEEPSEEK_API_KEY`，如需 GPT 订阅访问则确认 CC Switch 代理为 `127.0.0.1:7890`。
3. 如果用 GPT 订阅：运行 `hermes auth add openai-codex`，在浏览器完成 ChatGPT/Codex OAuth。
4. 切换模型后执行 `/reset` 或重启 Hermes，使 provider/model 生效；如需立即加载 MCP，执行 `/reload-mcp`。

### 推荐运行模式

当前最稳的跨电脑模式：

```text
Hermes 管模型认证：
  GPT      = openai-codex OAuth / ChatGPT 订阅
  DeepSeek = DEEPSEEK_API_KEY

CC Switch 管网络与 Agent 生态：
  HTTP_PROXY / HTTPS_PROXY = http://127.0.0.1:7890
  Codex/Hermes 配置感知、MCP、Prompt、日志管理
```

不要把 ChatGPT 订阅当作 OpenAI API Key 上传或硬编码；订阅 OAuth 必须在每台新电脑上重新登录。


## 🧠 工作流强化吸收

本仓库作为 HERMES + CC Switch + Codex 工作流增强项目，持续吸收 Agent 工作流资产：

- `docs/absorption/open-source-workflow-absorption.md`：历史对比/开源项目的吸收清单。
- `docs/mcp/workflow-mcp-stack.md`：默认 MCP 与候选 MCP 的启用条件。
- `skills/software-development/agent-workflow-fortress/`：证据优先、自循环、开源吸收、验证闭环 Skill。
- `templates/agent-rules/`：`AGENTS.md` / `CODEX.md` / `SECURITY.md` / `DESIGN.md` 项目规则模板。
- `templates/task-tickets/cc-switch-agent-task.md`：给 Codex / Claude / OpenClaw / CC Switch 生态使用的任务单。
- `scripts/security/scan_agent_rules.py`：扫描第三方规则/Prompt 的零宽字符、注入语句和疑似密钥。
- `scripts/workflow/switch_model.py`：一键切换 GPT / DeepSeek 官方 Provider 路线。
- `scripts/workflow/hermes_workflow_doctor.py`：审计 Hermes、GPT/DeepSeek、CC Switch、Codex、MCP、Node 基线。
- `bin/hermes-npx*`：MCP wrapper，优先使用 Hermes 自带 Node v22，避免系统 PATH Node v16 造成 Context7/Playwright 兼容问题。
- `docs/workflow/gpt-deepseek-ccswitch-codex-upgrade.md`：三引擎全链路升级说明。

默认启用当前机器实测可运行且权限面低的 MCP：`public-apis`、`sequential-thinking`、`context7`。Playwright MCP 已用 Hermes Node v22 smoke test 可启动，但与 Hermes 原生 browser/computer_use 重叠，暂列候选不默认启用。

## 🚀 快速部署

```powershell
# Windows（管理员 PowerShell）
git clone git@github.com:DTALEX66/Workflow-assistance.git
cd Workflow-assistance
.\setup.ps1
```

```bash
# Linux / macOS；Windows 请优先用 setup.ps1，Git Bash 下 setup.sh 会写入 %LOCALAPPDATA%/hermes
git clone git@github.com:DTALEX66/Workflow-assistance.git
cd Workflow-assistance
chmod +x setup.sh && ./setup.sh
```

脚本自动完成：检查 Hermes → 写入配置（含 public-apis + sequential-thinking + context7 MCP）→ 安装 hermes-npx wrapper → 安装本地技能 → 安装依赖 → 启用插件和工具集。

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
Hermes ──→ ChatGPT Codex API (chatgpt.com/backend-api/codex) ──→ GPT-5.5
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
hermes config set model.default gpt-5.5
```

> 插件内置 base_url 为 `https://chatgpt.com/backend-api/codex`，无需手动设置

---

### 方案D：CC Switch 代理 + GPT（本机专用）

> **适用场景**：网络被墙的环境，通过 CC Switch 代理翻墙访问 OpenAI  
> **路由**：`Hermes → CC Switch 代理(:7890) → ChatGPT OAuth → GPT-5.5`

**前提：** CC Switch 已安装并运行（代理端口 7890）

```bash
# CC Switch 安装主体不保存在本仓库；请在新电脑自行安装并启动
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
  default: gpt-5.5
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
- 本仓库当前沉淀本地自定义技能、模型切换技能、Agent 工作流技能、MCP/代理/Codex 协作脚本与模板
- 建议部署后运行 `hermes doctor` 做全面检查
- 如果 Codex++ 或本地代理路线不可用，切到 DeepSeek 直连或 OpenAI Codex OAuth 官方 Provider 路线即可
- 遇到问题请查阅 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 排坑手册
- 包含模型切换技能：说"切换DP"/"切换GPT"一键切换
