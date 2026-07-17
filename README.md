# Workflow-assistance

`DTALEX66/Workflow-assistance` 是 Hermes + CC Switch + Codex 的**可迁移工作流资产库**。它保存无密钥配置、技能、wrapper、诊断脚本和项目模板；不保存 Hermes/Codex/CC Switch 安装主体、OAuth 状态、API key、会话数据库、日志或缓存。

## 职责边界

| 层 | 唯一职责 | 唯一入口 |
|---|---|---|
| Hermes | 对话编排、工具、skills、OAuth/provider 调用 | 官方文档、`hermes-agent` skill |
| CC Switch | 本机网络代理；Router 端口仅在现场监听且真实 smoke 后才视为模型路由 | `scripts/workflow/hermes_workflow_doctor.py` |
| Codex | 独立编码执行器；写任务使用隔离 worktree 和单写者 | Hermes bundled `codex` skill、`bin/codex*` |
| Provider 切换 | GPT OAuth / DeepSeek 的切换与诊断 | `skills/model-switch/SKILL.md` |
| 多代理发布流程 | task ticket、单写者、冻结复审、commit/push/CI | `skills/software-development/agent-workflow-fortress/SKILL.md` |
| 模型/API 中立执行契约 | 完成信号、结构化状态、失败关闭、隔离写者、exact-tree 证据 | `templates/task-tickets/model-neutral-agent-task.md` |
| MCP 默认集 | 只定义默认与按需启用边界 | `docs/mcp/workflow-mcp-stack.md` |

不要在 README、部署脚本或同步脚本里复制 skill 正文、模型名称或端口判断逻辑。

## Portable 目录

```text
config/config.yaml          最小无密钥基线；不覆盖 live 凭据
config/.env.template        环境变量名称模板，不含真实值
skills/                     portable skills 的唯一仓库源
bin/hermes-npx*             优先 Hermes bundled Node 的 MCP wrapper
bin/codex*                  定位已安装 Codex 的 launcher
scripts/workflow/           model switch、doctor、单向 repo→live sync
templates/                  跨 agent 规则与 task ticket；含模型/API 中立执行契约
```

## 默认能力

默认 MCP 只有 **Context7**，用于公开库文档查询。以下能力不默认启用：

- `sequential-thinking`：与模型原生推理和 plan/debug/TDD skills 重复；
- `public-apis`：低频目录查询可由 web 搜索替代；
- Playwright/filesystem/memory MCP：与 Hermes 原生 browser/file/memory 重叠；
- Spotify、X、video、TTS、meeting/disk-cleanup：有明确任务时通过 `hermes tools` / `hermes plugins` 启用。

`security-guidance` 是写入后的非阻断提示；项目 CI/secret scanner 是阻断门禁，两者不重复。

## 新机器部署

先独立安装 Hermes Agent；本仓库不安装主体。

```bash
git clone git@github.com:DTALEX66/Workflow-assistance.git
cd Workflow-assistance
./setup.sh                 # Linux/macOS/Git Bash
# 或 Windows PowerShell: .\setup.ps1
```

随后：

1. 在本机 Hermes `.env` 设置需要的 provider key；不要提交该文件。
2. GPT 订阅使用 `hermes auth add openai-codex`；不要从 Codex/Hermes `auth.json` 提取或复制 token。
3. 运行 `hermes model`，或使用 `python scripts/workflow/switch_model.py status|gpt|deepseek`。
4. 重启或 `/reset` 让工具、skill、provider 改动生效。
5. 运行结构诊断：

```bash
python scripts/workflow/hermes_workflow_doctor.py
```

结构诊断中的端口和 HTTP 状态只证明链路/配置，不等于 provider 可用。需要真实请求时使用 doctor 的 live smoke（见 `--help`）或 model-switch 中的显式 provider smoke。

## 安全同步

`sync_hermes_workflow_assets.py` 是**单向 repo → live**：

```bash
python scripts/workflow/sync_hermes_workflow_assets.py          # dry run
python scripts/workflow/sync_hermes_workflow_assets.py --apply  # 备份后应用
```

它会：

- 保留 live provider/model、凭据和自定义 MCP；
- 删除由本包管理但已退役的 `public-apis` / `sequential-thinking`；
- 部署 repo 中的 skills、wrapper、Context7 配置；
- 绝不把 live skills、`.env`、auth、session、logs 反向写回仓库。

## 验证

```bash
python tests/test_workflow_governance.py -v
python -m py_compile scripts/workflow/*.py
python scripts/workflow/sync_hermes_workflow_assets.py
python scripts/workflow/hermes_workflow_doctor.py
```

部署或修改 live 配置后，再运行：

```bash
hermes config check
hermes doctor
hermes mcp test context7
hermes prompt-size --json
```

## 隐私红线

永不提交或输出：`.env`、`auth.json`、Codex bearer token、API key、SSH 私钥、cookies、真实个人路径、`state.db`、会话、日志和缓存。Provider 切换只使用 Hermes 官方认证与配置入口。
