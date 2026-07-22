# Workflow-assistance

[![workflow-governance](https://github.com/DTALEX66/Workflow-assistance/actions/workflows/governance.yml/badge.svg)](https://github.com/DTALEX66/Workflow-assistance/actions/workflows/governance.yml)

面向 Windows、Linux 与 macOS 的 **Hermes Agent + CC Switch + Codex 全局可迁移工作流增强包**：集中维护无密钥配置、模型切换、链路诊断、Context7 MCP、Agent Skills、任务契约、安全同步、治理测试和跨平台 CI。

## 项目定位

`Workflow-assistance` 不是另一个 Agent Runtime，也不是 Hermes、Codex 或 CC Switch 的安装包；它也不是只服务本仓库的项目内脚本集合。它是覆盖用户全局 Hermes Agent + CC Switch + Codex 日常工作的**可迁移控制与治理层**：本仓库只是这些全局增强资产的可审计源目录，live Hermes Home 才是运行时落点。

全局增强范围包括：所有项目里的 Hermes 会话习惯、模型/provider 切换、CC Switch 代理路径、Codex 执行与复审方式、MCP 默认策略、长任务持久化、项目数据边界、排错手册、任务票据、Agent 规则和验证门禁。任何新增能力都必须先判断它增强的是这条全局工作流，还是只对本仓库有用；只对本仓库有用的临时脚本不得被包装成默认全局能力。

```text
Global workflow surface
├─ Hermes Agent runtime usage     sessions, skills, tools, MCP, memory, cron/gateway
├─ CC Switch routing              local proxy/network path and provider preflight
├─ Codex execution                launcher, task tickets, review and worktree rules
├─ Project task containment       per-repo .hermes runtime/artifacts boundaries
└─ Workflow-assistance repo       portable source of truth, tests, docs and sync scripts
```

本仓库承载的全局增强资产包括：

```text
Workflow-assistance
├─ portable config        无密钥、可审查的 Hermes 基线
├─ safe deployment        repo → live 单向同步、备份、保留本机状态
├─ route operations       GPT OAuth / DeepSeek 切换与链路诊断
├─ coding-agent workflow  Codex launcher、任务票据、单写者与冻结复审
├─ MCP policy             默认只启用 Context7，其他能力按需开启
├─ reusable skills        Agent、测试、Windows、代码复审等知识资产
└─ governance             安全扫描、治理测试、Linux/Windows CI、吸收审计
```

它保存可以安全提交到 Git 的工作流资产；不会安装 Hermes、Codex 或 CC Switch 主体，也不会保存 OAuth 状态、API Key、会话数据库、日志、缓存、模型权重或用户数据。

## 功能总览

| 功能域 | 当前能力 | 主要入口 |
|---|---|---|
| Portable 配置 | 无密钥 Hermes 基线、中文 CLI、原生工具集、Context7、低风险插件默认值 | `config/config.yaml` |
| 安全部署 | Windows / Bash 安装入口、自动备份、单向同步、保留 live Provider 与自定义能力 | `setup.ps1`、`setup.sh` |
| 模型切换 | GPT OAuth 与 DeepSeek 官方 Provider 状态检查和安全切换 | `scripts/workflow/switch_model.py` |
| 全链路诊断 | Hermes、认证、MCP、代理端口、Node、Codex 版本和可选真实执行 smoke | `scripts/workflow/hermes_workflow_doctor.py` |
| Codex 执行 | 跨平台 launcher、非交互执行规则、只读审查、隔离 worktree | `bin/codex*`、`skills/autonomous-ai-agents/codex/` |
| 睡眠模式 | 项目级持久 cron 队列、单 writer、依赖顺序、账本恢复与高风险阻断 | `skills/software-development/sleep-mode/` |
| Gateway/Cron 投递 | 区分 Gateway 运行、消息平台配置、TUI 本地输出和 sleep-mode 项目账本 | `docs/workflow/gateway-cron-delivery.md` |
| 项目数据边界 | fail-closed Git-ignore 检查，将任务临时文件、缓存、日志、测试环境和产物锁进本地项目 | `bin/hermes-project-data.py`、`skills/software-development/project-data-boundary/` |
| MCP | 默认固定 Context7；记录隐私、版本和新增 MCP 候选审计门禁 | `docs/mcp/workflow-mcp-stack.md`、`docs/mcp/mcp-catalog-governance.md`、`scripts/workflow/mcp_candidate_audit.py` |
| Agent 治理 | TDD、单写者、Task Ticket、结构化状态、fail-closed 契约、exact-tree 复审、CI 闭环 | `agent-workflow-fortress` |
| Context Pack | repomix/gitingest 风格的安全上下文包，输出到项目 `.hermes/task-artifacts/`，用于新会话与 Codex handoff | `scripts/workflow/build_context_pack.py`、`docs/workflow/context-pack.md` |
| Agent 行为评估 | promptfoo 风格声明式 smoke cases，评估工作流边界回答；不默认安装 runner/provider | `docs/workflow/agent-evaluation.md`、`templates/evals/agent-behavior-smoke.yaml` |
| UI/Skin 系统 | Catppuccin、shadcn/ui、assistant-ui 风格吸收，提供主题 token、Agent UI patterns 和 Windows Terminal scheme；不默认安装 UI runtime | `docs/workflow/ui-skin-system.md`、`templates/ui/`、`templates/windows-terminal/` |
| 本地质量门禁 | 跨平台 canonical gate runner，统一治理测试、语法、安全扫描、Context Pack、MCP 候选审计、Shell/PowerShell 解析 | `scripts/workflow/run_quality_gate.py`、`Justfile`、`docs/workflow/local-quality-gates.md` |
| 安全扫描 | Prompt/规则隐藏字符、注入特征和疑似硬编码秘密扫描 | `scripts/security/scan_agent_rules.py` |
| 模板库 | AGENTS/CODEX/DESIGN/SECURITY 规则模板及多类任务票据 | `templates/` |
| 审计与证据 | 开源能力吸收记录、固定上游 SHA、机器可读清单、明确排除项 | `docs/audit/` |
| 跨平台验证 | Python 治理测试、语法检查、Shell/PowerShell 解析、Linux/Windows Actions | `.github/workflows/governance.yml` |

## Portable 部署与安全同步

### 新机器部署

先通过官方方式独立安装 Hermes Agent，再克隆本仓库：

```bash
git clone git@github.com:DTALEX66/Workflow-assistance.git
cd Workflow-assistance

# Linux / macOS / Git Bash
./setup.sh

# Windows PowerShell
.\setup.ps1
```

两个 setup 入口都会调用：

```bash
python scripts/workflow/sync_hermes_workflow_assets.py --apply
```

### 单向同步模型

同步脚本只执行 **repo → live Hermes Home**：

```bash
# 预览，不写入
python scripts/workflow/sync_hermes_workflow_assets.py

# 备份后应用
python scripts/workflow/sync_hermes_workflow_assets.py --apply
```

实际行为：

- 在 Hermes Home 下创建时间戳备份；
- 部署 `skills/`、`bin/` 和无密钥 `.env.template`；
- 合并 portable MCP 与插件基线；
- 保留 live Provider、模型、本机凭据、自定义 MCP 和非退役插件；
- `public-apis` / `sequential-thinking` 等退役 managed MCP 每次同步都会移除；
- 一次性迁移状态只保护退役插件：首次迁移会清除旧包管理插件，之后用户重新启用的插件不再被同步脚本删除；
- 只删除有明确路径登记的退役 skill 资产；
- 输出 repo/live 目录哈希和文件数用于核验；
- 使用 `config/managed-config-schema.yaml` 声明哪些非秘密体验字段由包管理、哪些本机路由/认证字段必须保留；
- 绝不把 live skills、`.env`、认证、会话或日志反向复制到仓库。

### 可复制性与兼容性验证

每次发布前，质量门禁都会在一个空的、隔离 Hermes Home 中执行 portable sync：

```bash
python scripts/workflow/verify_portable_install.py
```

它不调用模型、不读取现有 Hermes Home、不读取认证文件；只验证 portable config、skills、bin、Context7、模型 lanes 与快捷命令可被部署。兼容性承诺和功能清单位于 `workflow-manifest.yaml`。

新项目应先忽略 `.hermes/`，再使用最小项目初始化器：

```bash
python scripts/workflow/bootstrap_project.py D:/All-projects/NewProject --dry-run
python scripts/workflow/bootstrap_project.py D:/All-projects/NewProject
```

该入口只写目标项目的 Git-ignored `.hermes/` 运行时说明和 bootstrap manifest，绝不复制 OAuth、API key、provider route、会话或用户数据。

### Portable Hermes 基线

`config/config.yaml` 当前定义：

- Hermes CLI 中文界面；
- 忙时输入默认排队：`display.busy_input_mode = queue`，避免新输入隐式打断当前 turn；
- 本地 terminal backend；
- `hermes-cli` toolset；
- 原生 `browser`、`clarify`、`code_execution`、`computer_use`、`cronjob`、`delegation`、`file`、`image_gen`、`memory`、`session_search`、`skills`、`terminal`、`todo`、`vision`、`web` 工具集；
- 默认 MCP 仅 Context7；
- 默认插件为 `security-guidance` 与 `web/ddgs`；
- Provider 与模型字段仅作为 portable 初始基线，部署到既有环境时保留 live 选择；
- API Key 字段保持为空，真实秘密只存在于 live 环境。

`config/SOUL.md` 保存可迁移的 Agent 行为风格；`config/.env.template` 只列环境变量名称，不含真实值。

## 模型切换与路由诊断

### 安全切换

`skills/model-switch/SKILL.md` 与切换脚本共同定义这条路线的操作边界。

KIMI 线路把稳定性与速度选择明确分开：`kimi` 使用 K3；`kimi-fast`
使用 K2.7 Code；`kimi-turbo` 使用官方 K2.7 Code HighSpeed。以下命令只在
用户明确决定切换时执行；不会自动更改当前会话，切换后必须新建会话或执行
`/reset`。

```bash
python scripts/workflow/switch_model.py status
python scripts/workflow/switch_model.py kimi       # Kimi K3
python scripts/workflow/switch_model.py kimi-fast  # Kimi K2.7 Code
python scripts/workflow/switch_model.py kimi-turbo # Kimi K2.7 Code HighSpeed
python scripts/workflow/switch_model.py gpt
python scripts/workflow/switch_model.py deepseek
```

支持能力：

- `status`：显示脱敏后的 Hermes Provider/模型配置、认证清单和关键端口状态；
- `gpt`：切换到 Hermes 官方 `openai-codex` OAuth 路线；
- `deepseek` / `dp`：切换到 DeepSeek 官方 Provider；
- 切换前检查所需代理端口或环境变量；
- 通过 `hermes config set` 官方入口写配置，不直接改认证文件；
- 支持环境变量覆盖 live 模型名，避免把易变名称复制到多处；
- 所有输出经过 token、Key、JWT、GitHub/npm/Slack 等常见秘密模式脱敏；
- `--no-verify` 只用于明确需要跳过前置检查的场景。

切换后需新建会话或执行 `/reset`，让 Provider 变更进入新的 Hermes Session。

### Workflow Doctor

结构诊断：

```bash
python scripts/workflow/hermes_workflow_doctor.py
```

它会检查：

1. Hermes 版本、配置、认证 inventory 和 MCP inventory；
2. CC Switch 网络代理与 Codex Router 端口；
3. DeepSeek 与 ChatGPT 的 HTTP 传输可达性；
4. Node 版本和已配置的 Context7 MCP；
5. Codex desktop/plugin/PATH 候选二进制与版本漂移；
6. Codex 配置中的选定字段，并对输出统一脱敏。

真实执行 smoke：

```bash
python scripts/workflow/hermes_workflow_doctor.py --live
```

`--live` 会实际调用 GPT、DeepSeek 和 Codex，并要求输出独立 marker。普通端口、HTTP 状态和结构检查不等于真实模型执行；只有 live marker 通过才能证明当前执行链路可用。`--live` 可能产生网络请求或模型用量，因此不会默认运行。必须从 Git 项目根目录运行：Codex smoke 的临时 Git 仓库默认只会创建在当前项目 `.hermes/task-runtime/`，运行后自动清除；如需指定其父目录，传入同一项目范围内的 `--codex-workdir .hermes/task-runtime/<name>`，项目外路径会被拒绝。

### Provider / 模型健康库存

默认只生成不含秘密、不会发起请求的模型库存：

```bash
python scripts/workflow/provider_health.py \
  --config config/config.yaml \
  --output .hermes/task-artifacts/provider-health.json
```

默认状态为 `UNVERIFIED`，表示模型被配置到 lane 中但尚未做真实调用；只有明确传入 `--live` 才逐一执行 marker 请求并消耗额度。报告不包含 token、OAuth 内容、cookie、API key、base URL 或凭据文件内容。

## Codex 编码执行器

仓库不捆绑 Codex，可通过 launcher 定位本机已安装版本：

- `bin/codex`：Bash/Git Bash launcher；
- `bin/codex.cmd`：Windows launcher；
- 优先使用更新的 desktop/plugin Codex 二进制，避免 PATH 中旧版本遮蔽。

`skills/autonomous-ai-agents/codex/SKILL.md` 定义：

- `codex exec` / `codex review` 使用非交互模式；
- 交互 TUI 才使用 PTY；
- 只读复审使用 read-only sandbox；
- 写任务必须在独立 Git worktree 或 clone 中执行；
- 一个 checkout 只能有一个 writer；
- 不自动绕过 sandbox；
- Codex 不得在未授权时提交、推送、合并或创建 PR；
- 复审绑定 exact staged tree，任何修改都会使 verdict 失效。

## MCP 与 Hermes 原生工具

### 默认 MCP：Context7

Context7 用于查询公开软件库的当前文档，降低使用过期 API 的风险：

```bash
hermes mcp test context7
```

通过 `bin/hermes-npx*` 优先调用 Hermes bundled Node，减少系统 Node/PATH 漂移。

> Context7 查询会外发数据。不得发送私有代码、密钥、客户资料或内部项目名称。

### 为什么其他 MCP 不默认启用

| MCP/能力 | 不默认启用原因 | 当前替代 |
|---|---|---|
| sequential-thinking | 与模型推理和 plan/debug/TDD skills 重叠 | 原生推理 + 专门 skill |
| public-apis | 使用频率低，可直接搜索 | `web_search` / GitHub 公共目录 |
| Playwright MCP | 与 Hermes browser/computer_use 重叠且扩大权限面 | Hermes 原生浏览器工具 |
| filesystem MCP | 与 Hermes file tools 重叠 | Hermes 原生文件工具 |
| memory MCP | 与 Hermes memory 重叠 | Hermes 原生记忆工具 |

新增默认 MCP 必须固定版本、核验来源/许可证、真实运行 `hermes mcp test`、说明数据外发与权限，并测量工具 schema 对 Prompt 大小的影响。

新增候选先走审计器，不直接写默认配置：

```bash
python scripts/workflow/mcp_candidate_audit.py --write-template .hermes/task-artifacts/mcp-candidate.yaml
python scripts/workflow/mcp_candidate_audit.py .hermes/task-artifacts/mcp-candidate.yaml
```

`MCP_CANDIDATE_AUDIT_PASS` 只表示候选元数据完整，不等于 server 已配置、已运行、已安全或已默认启用。候选治理细则见 `docs/mcp/mcp-catalog-governance.md`。

## Agent 工作流治理

`skills/software-development/agent-workflow-fortress/` 是本仓库的统一工作流治理入口，覆盖：

- 证据优先的缺口扫描；
- TDD 的 RED → GREEN → REFACTOR；
- 单写者和隔离 worktree；
- 快速并行侦察与串行集成；
- Task Ticket 的允许路径、禁止路径、输入资料、验证命令和输出契约；
- 后台任务的结构化状态、进程句柄和单调终态；
- 完成信号、有界恢复和“无真实证据不算完成”；
- 对 prompt、plan mode、hook、路径声明与 worktree 的非安全边界说明；
- 外部 sandbox/tool deny/OS 支持与负控证据要求；
- `git write-tree` exact-tree 冻结复审；
- 异步旧 verdict 的对象绑定和 superseding-tree 复核；
- commit、push 和 exact-SHA CI 闭环；
- 开源能力“吸收方法、不盲目 vendor”的治理；
- repomix/gitingest 风格 Context Pack，用项目内忽略产物承载新会话和 Codex handoff 摘要；
- MCP candidate audit，用 fail-closed 元数据检查约束新增 MCP 的版本、许可证、权限、数据外发、原生工具重叠和 smoke 证据；
- promptfoo 风格 Agent 行为评估模板，用声明式 cases 检查边界回答但不默认引入外部 runner；
- Catppuccin / shadcn-ui / assistant-ui 风格 UI/Skin 吸收，用 token 和 patterns 统一工作流可视状态但不默认安装前端 runtime；
- 本地质量门禁统一入口，用 Python runner 作为 canonical command，`Justfile` 仅作可选快捷方式；
- 上下文/token 卫生、可持续后台队列和真实任务计数。

### 项目任务数据锁定

所有会生成临时文件、缓存、测试环境、日志、下载物或 review 产物的任务都必须先使用：

```bash
python "$HERMES_HOME/bin/hermes-project-data.py" --project . check
python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- python -m pytest
python "$HERMES_HOME/bin/hermes-project-data.py" --project . kanban -- boards list
```

该执行器以 Git 根为边界，要求 `.hermes/` 已被 Git 忽略，并把 `TMP`、`TEMP`、`TMPDIR`、XDG/pip/uv/npm/yarn/Playwright/Rust/Ruff/mypy/pre-commit cache 与 Python bytecode 指向 `<project>/.hermes/task-runtime/`。它同时将原生 Kanban 的 `HERMES_KANBAN_HOME` 固定在 `<project>/.hermes/kanban/`；禁止直接创建全局项目 board。显式项目外输出路径必须拒绝；它不是 OS sandbox，不能替代路径审查。项目证据归档到同项目 `.hermes/task-artifacts/`；认证、会话库、全局 config/skills 和 cron scheduler 元数据仍属于 Hermes 全局运行时，禁止误迁移。同步器仅保留最近两份自身生成的 workflow backup，避免每次部署重复膨胀全局 backup 目录。

### 模型/API 中立任务契约

`templates/task-tickets/model-neutral-agent-task.md` 提供不绑定特定模型或收费 API 的任务票据：

- Completion Contract；
- Run State Contract；
- Allowed/Forbidden Paths；
- 读、写、执行与网络权限；
- 外部执行机制和 Tool deny list；
- OS sandbox 支持验证；
- Shell 写入、链式命令与子 Agent 写入负控；
- 缺少执行证据时必须 `blocked`；
- 测试、产物、tree identity、回滚与日志输出契约。

它是治理契约，不是运行时 sandbox。相关 Grok Build 方法吸收已固定上游 SHA，并登记在 `docs/audit/model-neutral-agent-harness-absorption-2026-07.yaml`；本轮没有引入模型、Provider、付费 API、外部二进制或运行时资产。

## Skills 能力库

| Skill | 功能 |
|---|---|
| `codex` | 调用 Codex 进行有边界的实现或只读审查，规范 PTY、sandbox 和 worktree |
| `model-switch` | GPT OAuth / DeepSeek 安全切换、代理与 Provider 真实 marker 诊断 |
| `agent-workflow-fortress` | 多 Agent 编排、TDD、单写者、冻结复审、发布和开源吸收治理 |
| `sleep-mode` | 项目级持久自动推进：cron 调度、单 writer、状态账本、恢复与安全阻断 |
| `project-data-boundary` | 项目任务数据 containment：Git-ignore fail-closed、受控临时目录、缓存、日志和产物路径 |
| `python-testing` | unittest/pytest 模式、测试隔离、fixture 和常见陷阱 |
| `requesting-code-review` | 代码复审兼容入口，统一转入 fortress 的 exact-tree 流程 |
| `windows-development-environment` | PowerShell 编码、PATH 遮蔽、spawn/lockfile、便携工具链和 Windows 环境问题 |
| `screenlingua` | 本地截图翻译应用的项目知识：React + Tauri + FastAPI、本地 OCR 与翻译；不随本仓库安装应用主体 |

同步脚本会把仓库中的 skills 作为 portable 单一事实源部署到 Hermes Home，但不会反向吸收 live 私有 skill 或运行数据。

## 安全与隐私

### 永不提交

- `.env` 和真实环境变量值；
- `auth.json`、OAuth Token、Bearer Token、API Key；
- SSH 私钥、cookies、浏览器状态；
- Hermes `state.db`、会话、日志、缓存；
- Codex 会话和认证文件；
- 模型权重、安装器、大型二进制或真实用户数据。

### Agent 规则扫描

```bash
python scripts/security/scan_agent_rules.py templates skills docs scripts
```

扫描内容包括：

- Zero-width/BOM 隐藏字符；
- 常见 prompt-injection 特征；
- 管道执行 Shell 的危险文本模式；
- 疑似硬编码 secret/token/password。

运行期输出由 switcher 和 doctor 的脱敏器再次处理。`security-guidance` 提供非阻断提示，治理测试和 CI 才是仓库阻断门禁。

## 模板、文档与审计

### Agent 规则模板

`templates/agent-rules/`：

- `AGENTS.md`：跨 Agent 项目规则；
- `CODEX.md`：Codex 专用规则；
- `DESIGN.md`：设计约束与结构说明；
- `SECURITY.md`：项目安全边界。

### Task Ticket 模板

`templates/task-tickets/`：

- `cc-switch-agent-task.md`：通用编码 Agent 任务；
- `model-neutral-agent-task.md`：模型/API 中立、证据驱动的执行契约；
- `public-workflow-audit-ticket.md`：公开工作流审计任务。

### Agent 行为评估模板

`templates/evals/`：

- `agent-behavior-smoke.yaml`：promptfoo 风格、模型/provider 中立的 Agent 行为 smoke cases，用于检查 repo/live/session、Gateway delivery、持久任务、interrupted delegation、PowerShell 选择和验证诚实等全局工作流边界；模板不包含真实 provider、密钥、trace 或运行时依赖。

### UI / Skin 模板

`templates/ui/` 与 `templates/windows-terminal/`：

- `templates/ui/skin-presets.yaml`：Catppuccin Mocha/Frappe、Nord、Dracula 的 portable 主题 token 和状态语义；
- `templates/ui/agent-chat-ui-patterns.md`：assistant-ui / shadcn-ui 风格的 Agent thread、tool call timeline、status rail 和 command palette 信息架构；
- `templates/ui/terminal-theme-checklist.md`：终端/Hermes skin 应用边界、证据要求和可访问性检查；
- `templates/windows-terminal/catppuccin-mocha.json`：Windows Terminal scheme 示例；模板可复制，但不会自动改用户 settings。

### 文档和审计

- `docs/workflow/project-definition.md`：项目定义与职责边界；
- `docs/workflow/agent-evaluation.md`：Agent 行为评估边界、promptfoo 方法吸收和默认不安装策略；
- `docs/workflow/context-pack.md`：安全 Context Pack 生成器、输出边界和 handoff 使用方式；
- `docs/workflow/local-quality-gates.md`：本地 canonical quality gate runner、Justfile 快捷入口和 CI 对齐方式；
- `docs/workflow/ui-skin-system.md`：UI/Skin 分层、主题 token、Agent UI 状态表达与 runtime-neutral 边界；
- `docs/workflow/project-data-boundary.md`：项目任务数据归属、迁移、保留与 fail-closed 执行器；
- `docs/workflow/hermes-runtime-layout.md`：Hermes 全局运行目录分层、可恢复迁移、升级验证与清理边界；
- `docs/workflow/gateway-cron-delivery.md`：Gateway、cron、sleep-mode、TUI 与外部消息平台的投递边界；
- `docs/workflow/gpt-deepseek-ccswitch-codex-upgrade.md`：全链路工作流和路由矩阵；
- `docs/workflow/error-fixes-2026-07-04.md`：Windows/Git/Python/GitHub CLI 实际故障记录；
- `docs/mcp/workflow-mcp-stack.md`：MCP 默认策略；
- `docs/mcp/mcp-catalog-governance.md`：MCP 候选审计 schema、阻断规则和默认启用边界；
- `docs/absorption/open-source-workflow-absorption.md`：开源工作流吸收清单；
- `docs/audit/workflow-absorption-audit-2026-07.md`：总体吸收审计；
- `docs/audit/hermes-workflow-recovery-2026-07-22.md`：Hermes Desktop、CC Switch、Codex、GitHub 全链路故障、执行错误、恢复过程和数据保护证据；
- `docs/audit/model-neutral-agent-harness-absorption-2026-07.md`：模型/API 中立 Agent Harness 审计；
- `docs/audit/model-neutral-agent-harness-absorption-2026-07.yaml`：固定来源和本地落点的机器可读证据；
- `TROUBLESHOOTING.md`：常见部署、代理、认证和工具链问题。

## 测试与持续集成

### 本地门禁

```bash
python scripts/workflow/run_quality_gate.py verify
```

可选快捷方式（如果本机已安装 `just`）：

```bash
just verify
```

`just` 不是默认依赖；缺少时直接使用 Python runner。`verify` 依次运行 governance、compile、security、context-pack、mcp-audit、shell 和 powershell gate。PowerShell gate 优先 `pwsh`，仅在缺少时回退 `powershell.exe`，并且只用 AST parser 解析 `setup.ps1`，不执行安装动作。Shell/PowerShell 工具不可用时对应 gate 会显式 skip。

治理测试覆盖：

- portable config 默认 MCP/插件边界；
- 同步时保留 live Provider 与自定义能力；
- 退役资产的一次性安全迁移；
- 缺少 live config 时的基线初始化；
- setup 不默认开启高权限可选能力；
- doctor 结构检查与 live marker 区分；
- secret redaction；
- Context Pack 输出路径、Git-ignore fail-closed、秘密脱敏和项目内 artifact 边界；
- MCP 候选审计器的 pinned version、许可证、权限、native overlap、default-enable 阻断和输出 marker；
- 本地 quality gate runner 命令顺序、fail-fast 语义、Justfile 可选性和 CI 对齐；
- UI/Skin token JSON/YAML 解析、开源吸收来源、runtime-neutral 边界和“不自动应用用户 UI 设置”；
- skills 引用完整性；
- Codex 非交互和单写者边界；
- model routing 单一可执行事实源；
- 模型/API 中立任务模板的完整安全语义；
- promptfoo 风格 Agent 行为评估模板的 provider/model/secret/runtime 中立边界；
- 固定上游 SHA/SOURCE_REV、local artifact 范围和空 runtime assets。

### GitHub Actions

`.github/workflows/governance.yml` 在每次 push 和 pull request 上运行：

- Ubuntu / Windows：调用同一个 `python scripts/workflow/run_quality_gate.py verify`；
- 平台工具缺失时 shell / powershell 子 gate 显式 skip，而不是伪装通过；
- CI verdict 绑定提交 SHA，不能用旧 run 证明新提交。

## 仓库结构

```text
.github/workflows/   Linux/Windows 治理 CI
bin/                 Hermes Node 与 Codex 定位 wrapper
config/              无密钥 Hermes 基线、环境变量模板、SOUL
scripts/workflow/    安全同步、模型切换、全链路 doctor
scripts/security/    Agent 规则与秘密扫描
skills/              Portable Hermes Skills 单一仓库源
templates/           Agent 规则和 Task Ticket 模板
docs/                工作流、MCP、吸收记录和审计证据
tests/               仓库治理回归测试
setup.sh / setup.ps1 跨平台部署入口
TROUBLESHOOTING.md   故障排查
```

## 常用操作

```bash
# 查看当前 Provider、认证和代理前置条件
python scripts/workflow/switch_model.py status

# 切换 Provider（仅在用户明确决定后；切换后新建会话或执行 /reset）
python scripts/workflow/switch_model.py kimi       # Kimi K3
python scripts/workflow/switch_model.py kimi-fast  # Kimi K2.7 Code
python scripts/workflow/switch_model.py kimi-turbo # Kimi K2.7 Code HighSpeed
python scripts/workflow/switch_model.py gpt
python scripts/workflow/switch_model.py deepseek

# 结构诊断；不产生模型调用
python scripts/workflow/hermes_workflow_doctor.py

# 真实执行诊断；可能产生网络/模型用量
python scripts/workflow/hermes_workflow_doctor.py --live

# 检查默认 MCP
hermes mcp test context7

# 预览 / 应用 portable 同步
python scripts/workflow/sync_hermes_workflow_assets.py
python scripts/workflow/sync_hermes_workflow_assets.py --apply

# 生成新会话 / Codex handoff 上下文包；输出到 .hermes/task-artifacts/context-pack.md
python scripts/workflow/build_context_pack.py

# 生成 / 审计 MCP 候选；只写项目内忽略产物，不默认启用
python scripts/workflow/mcp_candidate_audit.py --write-template .hermes/task-artifacts/mcp-candidate.yaml
python scripts/workflow/mcp_candidate_audit.py .hermes/task-artifacts/mcp-candidate.yaml

# 仓库完整门禁
python scripts/workflow/run_quality_gate.py verify
just verify  # optional; only if just is installed
```

## 使用边界

- 本仓库不会安装或升级 Hermes、Codex、CC Switch、Screenlingua 或其他应用主体；
- 不会把 live Provider、凭据、会话和用户自定义配置反向上传；
- 默认配置不会启用与 Hermes 原生工具重复或权限面更大的 MCP；
- 普通 doctor 只证明结构与传输可达，结构检查不等于真实模型执行；
- `--live`、Provider 切换和外部 MCP 可能产生网络请求，应由用户明确执行；
- Task Ticket、plan mode、hook、路径声明和 worktree 都不是安全 sandbox；
- 模型/API 中立吸收只保留通用方法，不引入模型、收费服务或外部执行器；
- README 负责解释功能，机器可读事实仍以 `config/`、脚本、skills、manifest 和治理测试为准。
