# Workflow MCP Stack

当前 Hermes 部署包的 MCP 目标不是“越多越好”，而是：少量、稳定、可验证、不会扩大危险权限面。

## 默认启用

### public-apis

- 包：`public-apis-mcp@0.0.10`
- 作用：查询公共 API 目录，用于项目选型、数据源发现、原型调研。
- 状态：已在 `config/config.yaml` 中启用。

### sequential-thinking

- 包：`@modelcontextprotocol/server-sequential-thinking@2025.12.18`
- 作用：复杂任务拆解、反思、逐步推理。
- 实测：Hermes bundled Node v22.23.1 下可启动。
- 状态：已在 `config/config.yaml` 中启用。

### Context7

- 包：`@upstash/context7-mcp@3.2.2`
- 价值：实时读取库文档，减少过期 API 用法。
- 实测：Hermes bundled Node v22.23.1 下 `--help` 通过。
- 状态：已在 `config/config.yaml` 中启用，通过 `hermes-npx` wrapper 避免系统 Node v16。
- 信任边界：Context7 会把库名/文档查询发送到其服务；不要把私有代码、密钥、客户数据当查询词发送。默认只用于公开库文档。

## 候选但不默认启用

### Playwright MCP

- 包：`@playwright/mcp`（候选项，启用前必须固定版本并单独 smoke test）
- 价值：浏览器自动化和网页 QA。
- 实测：Hermes bundled Node v22.23.1 下 `--help` 通过。
- 不默认原因：权限面大，且 Hermes 原生 `browser` / `computer_use` 已覆盖多数网页自动化。
- 启用条件：明确需要 Playwright MCP 与外部 Agent 共享浏览器自动化能力。

### Memory / Filesystem MCP

不默认启用。Hermes 已有原生 `memory` / `file` 工具，重复 MCP 会增加上下文噪声和权限面。

## 验证命令

```bash
node --version
npm --version
bin/hermes-npx -y @modelcontextprotocol/server-sequential-thinking@2025.12.18 --help
bin/hermes-npx -y public-apis-mcp@0.0.10 --help
bin/hermes-npx -y @upstash/context7-mcp@3.2.2 --help
```

如新增 MCP，先固定版本、运行 smoke test，再写入默认配置；不要默认使用浮动 latest 版本。
