# 开源工作流吸收清单（非 Obsidian 阶段）

> 目标：强化 Hermes / Codex / CC Switch 的日常工作流。当前阶段不吸收 Obsidian Vault 内容、不上传素材、不处理真实知识库，只吸收可迁移的开源工具、规则、MCP、Agent 工作法和安全模板。

## 已实测并吸收

| 来源 / 开源项目 | 吸收方式 | 状态 | 说明 |
|---|---|---:|---|
| public-apis-mcp | `config/config.yaml` 已配置 MCP | ✅ 已有 | 用于查询公共 API 目录，辅助项目选型/数据源发现。 |
| `@modelcontextprotocol/server-sequential-thinking` | 新增 `sequential-thinking` MCP | ✅ 已实测 | 当前 Node v16 下可启动，适合复杂任务分解、反思和多步推理。 |
| Hermes skill system | 新增 `agent-workflow-fortress` skill | ✅ 已吸收 | 把“证据优先、自循环、技能主动使用、验证闭环、开源吸收筛选”固化为工作流。 |
| Codex / AGENTS.md 规则思路 | 新增 `templates/agent-rules/AGENTS.md` / `CODEX.md` | ✅ 已吸收 | 作为每个项目可复制的 Agent 协作规则模板。 |
| 安全规则模板 | 新增 `templates/agent-rules/SECURITY.md` + 扫描脚本 | ✅ 已吸收 | 约束密钥、跨目录、第三方提示词、危险命令。 |
| DESIGN.md / design-token 思路 | 新增 `templates/agent-rules/DESIGN.md` | ✅ 已吸收 | 用于 UI/UX 项目，避免“只实现功能、不打磨体验”。 |
| CC Switch 执行票据 | 新增 `templates/task-tickets/cc-switch-agent-task.md` | ✅ 已吸收 | 把 Hermes 规划转成 Claude/Codex/OpenClaw 可执行任务单。 |
| Aether-Radar 项目方法 | 写入 workflow skill | ✅ 已吸收 | 吸收“选型/发现/对比/导出/验证”的雷达式工作法，不复制项目数据。 |
| MINIGAME 自循环经验 | 写入 workflow skill | ✅ 已吸收 | 吸收“技能先加载 → 真实缺口 → 实现 → npm verify → git 同步”的循环。 |
| Star-Trails-Log 开源对标经验 | 写入 workflow skill | ✅ 已吸收 | 吸收 RSSHub/FreshRSS/Karakeep 等“借鉴设计，不盲目引入依赖”的原则。 |
| `promptfoo/promptfoo` | 新增 `docs/workflow/agent-evaluation.md` 与 `templates/evals/agent-behavior-smoke.yaml` | ✅ 已吸收方法 | 吸收声明式 eval cases、assertions 和 CI-friendly 布局；不安装 runner、不配置 provider、不保存真实 trace。 |

## 已识别但暂不默认启用

| 来源 / 开源项目 | 当前结论 | 原因 / 后续条件 |
|---|---|---|
| `@upstash/context7-mcp` | 候选 | 当前 Node v16 实测报 `ReadableStream is not defined`；升级 Node 20+ 后再启用，用于实时拉取库文档。 |
| `@playwright/mcp` | 候选 | 当前 Node v16 实测报 `GlobalRequest` 相关错误；升级 Node 20+ 后再启用。Hermes 已有 browser/computer_use，非 P0。 |
| `@modelcontextprotocol/server-memory` | 不默认启用 | Hermes 已有原生 memory；避免双记忆源冲突。 |
| filesystem MCP | 不默认启用 | Hermes 已有 file 工具；额外文件系统 MCP 会扩大权限面。 |
| MarkItDown / OpenDataLoader | 后期处理 | 主要服务素材入库/知识库，不属于当前“非 OBS 工作流强化”阶段。 |
| Cognee / GBrain / Talos | 后期研究 | 更偏知识图谱/知识库 UI/长期记忆，不作为当前默认部署依赖。 |
| RSSHub / FreshRSS / Karakeep / linkding / Linkwarden / Memos / NewsBlur / Tube Archivist | 吸收设计原则，不引入依赖 | 它们主要是 Fan Memory OS 的产品对标，不应污染 Hermes 基础包。 |

## 后续升级条件

1. Context7 已默认启用；必须固定版本，并通过 `hermes-npx` 使用 Hermes bundled Node：

```yaml
mcp_servers:
  context7:
    command: hermes-npx
    args:
      - -y
      - '@upstash/context7-mcp@3.2.2'
    timeout: 120
    connect_timeout: 120
```

2. 如果需要网页自动化 MCP，而 Hermes browser/computer_use 工具不够用，再单独固定版本、审计后启用 Playwright MCP：

```yaml
mcp_servers:
  playwright:
    command: hermes-npx
    args:
      - -y
      - '@playwright/mcp@<pinned-version>'
    timeout: 120
    connect_timeout: 120
```

3. 不把第三方仓库源码直接 vendor 到本仓库，除非满足全部条件：
   - 许可证允许；
   - 体积小；
   - 不含密钥/遥测/危险脚本；
   - 本仓库确实需要修改源码而不是通过包管理器安装。
