# 模型/API 中立 Agent Harness 吸收审计（2026-07）

## 来源

- 上游参考：https://github.com/xai-org/grok-build
- 吸收类别：工作流方法、任务契约和安全负控
- 吸收方式：文档、模板、治理测试

本轮只吸收不依赖特定模型、付费接口或外部运行时的通用机制。Hermes 继续是唯一编排器；本仓库不增加新的模型路线、Provider、凭据或网络服务。

## 已吸收

| 方法 | 落地位置 | 验收方式 |
|---|---|---|
| 完成信号与有界恢复 | `templates/task-tickets/model-neutral-agent-task.md` | 没有真实证据时只能失败或阻塞，不能假完成 |
| 结构化运行状态 | 同上 | 状态、时间、进程句柄、树身份、命令与退出码字段齐全 |
| 终态单调性 | 同上 | 迟到进程不得覆盖失败、阻塞或取消状态 |
| 单写者与隔离工作树 | 模板 + `agent-workflow-fortress` reference | 写任务必须独立 worktree/clone |
| 失败关闭安全边界 | 模板 + reference | 检查器错误、超时或无法解析时拒绝执行 |
| Exact-tree 证据 | 模板 + reference | 复审绑定 `git write-tree`，树变化后 verdict 失效 |
| 安全负控 | reference | 覆盖链式命令、shell 写入、子 Agent 越权、伪只读 sandbox 和上传风险 |

## 明确排除

- 任何模型名称、模型目录、模型路由或模型专用提示；
- 任何订阅、计量服务、付费接口或托管推理端点；
- 外部认证、凭据文件、云存储、遥测、trace/session 上传；
- 上游二进制、安装器、自动更新器和大型源码 vendoring；
- 与 Hermes 重复的 memory、MCP、skills、cron、session store 和 TUI；
- 在 Windows 上把未验证的模式名称当作内核隔离证明。

## 当前状态

**未安装外部执行器，未发起模型请求，未配置网络 API。**

本轮产物完全由本地 Markdown、现有 Python 治理测试和仓库门禁构成，可随 Workflow-assistance 正常同步，不引入运行时依赖或费用。

## 验证

```bash
python tests/test_workflow_governance.py -v
python scripts/security/scan_agent_rules.py templates skills docs scripts
python -m py_compile scripts/workflow/*.py scripts/security/*.py
```
