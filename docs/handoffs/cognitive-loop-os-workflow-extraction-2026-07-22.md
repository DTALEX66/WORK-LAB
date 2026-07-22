# Cognitive-Loop-OS 全局工作流资产迁移交接

日期：2026-07-22
来源仓库：`D:/All projects/Cognitive-Loop-OS`
目标仓库：`D:/All projects/Workflow-assistance`

## 决策

Hermes Agent、CC Switch、Codex 的跨项目工作流能力由 `Workflow-assistance` 独占维护。`Cognitive-Loop-OS` 只保留其自身的运行环境、桌面工具链、项目状态、项目证据、项目规则与项目专属技能。

这不是把 OS 的运行时数据迁出；认证、会话、缓存、数据库、日志和项目任务现场仍不进入全局工作流仓库。

## 已迁入的全局资产

| Workflow-assistance 路径 | 作用 |
| --- | --- |
| `scripts/workflow/run_taskpack_agent.py` | 单 writer TaskPack 执行器；高风险冻结树复审，低/高风险 exact-SHA 发布闭环。 |
| `tests/test_taskpack_agent_runner.py` | runner 的 writer lineage、冻结审查、release ref、默认技能边界回归测试。 |

该 runner 的默认技能是跨项目可复用集合：

```text
project-data-boundary,
agent-workflow-fortress,
test-driven-development,
systematic-debugging,
github-pr-workflow
```

它不默认加载任何具体项目技能。项目调用时必须通过 `--skills` 显式补充，例如 Cognitive-Loop-OS 使用 `cognitive-loop-os`。

## 使用边界

以目标项目根为运行目录，明确传入目标仓库和其实际发布远端。不得假设所有项目发布到 `origin/main`。

```bash
python D:/All-projects/Workflow-assistance/scripts/workflow/run_taskpack_agent.py \
  --repo D:/All-projects/Cognitive-Loop-OS \
  --remote-ref origin/feat/runtime-evaluation-sleep-leases \
  --skills cognitive-loop-os,project-data-boundary,agent-workflow-fortress,test-driven-development,systematic-debugging,github-pr-workflow \
  --mission-file <approved-project-relative-taskpack.md> \
  --risk high
```

- `--risk high`：writer 只能冻结候选树；同步只读 reviewer 给出 exact-tree `GO` 后才允许发布。
- `--risk low`：只能用于已批准的低风险 release train；runner 会验证本地 HEAD 与给定 `--remote-ref` 相同，并等待该提交的 CI。
- 任务命令产生的缓存、日志、测试状态和临时产物必须通过全局 `hermes-project-data.py` 约束在**目标项目自己的** Git-ignored `.hermes/` 内。
- 一个 checkout 同一时间只能有一个 writer；禁止将此 runner 与睡眠模式、cron 或人工写者并发使用。

## OS 保留范围

Cognitive-Loop-OS 应保留：

- `AGENTS.md`、项目配置、架构/验证政策、项目专属 `.codex.example/`；
- `.hermes/toolchains/`、`.hermes/desktop-runtime-v1/`、`.hermes/manual-workspace-demo/`；
- `.hermes/sleep-mode/`、项目任务队列、项目 handoff、evidence、task artifacts；
- `cognitive-loop-os` 等项目专属技能和项目代码/测试。

Cognitive-Loop-OS 不再托管或维护：

- 通用 TaskPack runner 及其回归测试；
- 已部署到项目 `.hermes/bin/` 的全局 `hermes-project-data.py` 副本；
- 已部署到项目 `.hermes/` 的通用 `TASK_DATA_POLICY.md` 副本。

全局 `hermes-project-data.py` 的单一事实源为本仓库 `bin/hermes-project-data.py`，通过 Workflow-assistance 的安全同步部署到 Hermes Home。

## 验证记录

迁移后在 `Workflow-assistance` 实际执行：

```text
python -m unittest discover -s tests -p 'test_taskpack_agent_runner.py' -v
6 tests passed

python scripts/workflow/run_quality_gate.py verify
QUALITY_GATE_PASS
```

完整质量门禁覆盖 58 个治理/边界测试、Python 编译、安全扫描、Context Pack、
portable install、provider inventory、MCP audit、Bash 与 PowerShell 解析。runner
测试已使用该仓库的标准 `unittest` discovery，因此会被常规质量门禁执行。

全局 helper 与 live Hermes Home helper 的 SHA-256 已比对一致。OS 项目中的
`task-runtime`、Cargo `target` 与项目缓存也已在无活动 writer 的前提下，作为
已确认可再生产物单独清理；工具链、运行时、证据、handoff、数据、日志和虚拟
环境均已保留。

未运行发布、未推送、未触碰任何认证、会话、个人数据或 OS 运行时数据库。

## 后续

1. 每个项目的规则中只保留“调用全局 runner 时必须显式传入项目技能、目标远端和项目根”的项目适配说明。
2. 后续 OS 工作从其实际项目队列和路线图选择未阻塞任务；不得因本迁移重新创建项目内通用 runner/helper 副本。
