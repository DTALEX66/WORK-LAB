# Workflow MCP Stack

当前 Hermes 部署包的 MCP 目标不是“越多越好”，而是：少量、稳定、可验证、不会扩大危险权限面。

## 默认启用

### public-apis

- 包：`public-apis-mcp@latest`
- 作用：查询公共 API 目录，用于项目选型、数据源发现、原型调研。
- 状态：已在 `config/config.yaml` 中启用。

### sequential-thinking

- 包：`@modelcontextprotocol/server-sequential-thinking@latest`
- 作用：复杂任务拆解、反思、逐步推理。
- 实测：当前机器 Node v16.13.1 下可启动。
- 状态：已在 `config/config.yaml` 中启用。

## 候选但不默认启用

### Context7

- 包：`@upstash/context7-mcp@latest`
- 价值：实时读取库文档，减少过期 API 用法。
- 当前问题：Node v16 下 `ReadableStream is not defined`。
- 启用条件：Node >= 20。

### Playwright MCP

- 包：`@playwright/mcp@latest`
- 价值：浏览器自动化和网页 QA。
- 当前问题：Node v16 下 `GlobalRequest` 兼容错误。
- 启用条件：Node >= 20，且 Hermes browser/computer_use 不够用。

### Memory / Filesystem MCP

不默认启用。Hermes 已有原生 `memory` / `file` 工具，重复 MCP 会增加上下文噪声和权限面。

## 验证命令

```bash
node --version
npm --version
npx -y @modelcontextprotocol/server-sequential-thinking --help
npx -y public-apis-mcp@latest --help
```

如新增 MCP，先运行 smoke test，再写入默认配置。
