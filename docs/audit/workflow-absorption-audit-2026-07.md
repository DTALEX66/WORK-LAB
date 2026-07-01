# Workflow Absorption Audit — 2026-07

## 已全量吸收

| 类型 | 吸收资产 | 状态 |
|---|---|---|
| Provider 切换 | `scripts/workflow/switch_model.py` + `skills/model-switch` | 已落地 |
| 工作流体检 | `scripts/workflow/hermes_workflow_doctor.py` | 已落地 |
| MCP 稳定性 | `bin/hermes-npx*` + setup 自动改写 config | 已落地 |
| MCP 默认栈 | public-apis / sequential-thinking / Context7 | 已落地 |
| MCP 候选栈 | Playwright MCP | 文档候选，不默认启用 |
| 对公任务单 | `templates/task-tickets/cc-switch-agent-task.md` | 已落地 |
| Agent 规则 | AGENTS/CODEX/SECURITY/DESIGN 模板 | 已落地 |
| 安全审计 | `scripts/security/scan_agent_rules.py` | 已落地 |

## 本轮关键修正

以前判断 Context7 / Playwright MCP 受 Node v16 阻塞。新审计发现 Hermes 自带 Node v22.23.1，故不再把 Node v16 作为硬阻塞；改为通过 `hermes-npx` wrapper 固定优先使用 Hermes bundled Node。

## 默认启用判定

- Context7：默认启用。价值高、权限面低、Hermes Node v22 下 help smoke test 通过。
- Playwright MCP：不默认启用。虽然 Hermes Node v22 下可启动，但权限面大且与 Hermes 原生 browser/computer_use 重叠。

## 不吸收项

- 第三方源码 vendoring：不做，避免维护/许可证/供应链负担。
- memory/filesystem MCP：不做，Hermes 原生能力已覆盖。
- 真实 `.env` / `auth.json` / Codex bearer token：禁止吸收。
