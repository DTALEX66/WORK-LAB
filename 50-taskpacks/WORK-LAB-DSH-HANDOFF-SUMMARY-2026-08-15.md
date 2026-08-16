# WORK-LAB 交接摘要 · 给 DeepSeek Harness（2026-08-15）

> 完整交接见 `50-taskpacks/WORK-LAB-DSH-HANDOFF-2026-08-15.md`（权威）。本文件是快速上手摘要。

## 接手什么

`D:/All projects/WORK-LAB`（GitHub `DTALEX66/WORK-LAB`）—— 客户端中立工作流控制面，管理 6 个 AI 客户端（Hermes / Codex / CC Switch / GitHub / OpenHuman / Open Design）+ 未来 AI 软件的 USER_GLOBAL 期望态。两活动模块：`10-workflow/workflow-assistance`（唯一 Writer）、`30-observer`（只读投影）。

## 当前状态（3 行）

1. `main` = `de29e583`（三项任务收口 PR #117 已 merge：skill 精简 + 全局配置 14→13 Skills + 模型满血字段）。
2. 当前分支 `feat/wl-dsh-001`（**未 push**），含 5 个 DSH adapter 交付物**未 commit**（adapter/schema/registry 条目/测试/文档，测试已 10/10 全绿）。
3. DSH 已隔离安装并运行：**`http://127.0.0.1:3080`**（loopback，pin `47f94385`，遥测禁用，DSH_HOME 在 `.hermes/task-runtime/deepseek-harness/`）。

## 下一步（按优先级）

1. **体积膨胀 WL3-810（最优先 FAIL）**：tracked 599 文件/4.95MiB vs 基线 438/2.65MiB（+86.8%）；来源=三份 `90-archive-manifests` 清单 + 254 个 .py。**需用户批准才能清理**。
2. **review DSH adapter 交付物**（§6 的 5 个文件）→ 申请 commit/push/PR。
3. **WL3-100/110 收编**（能力矩阵 + 身份模型子代理产出）。
4. **DSH-040 付费 smoke**：默认 `LOCAL_SMOKE_ONLY`，用户填 key + 批准后切真实调用。
5. **其余 WL3 任务**（120/210/220/300-330/400-420/500/510-520/610/620/720/820）。

## 不可违反的边界

- **E:\ 盘**：无逐路径逐操作授权禁止访问。
- **秘密/凭据**：不读不打印不复制不提交（含 DSH key，用户在 UI 填，Agent 不读）。
- **防外溢**：一切运行数据只在 `.hermes/task-runtime/`。
- **不 commit/push/PR/merge/release** 除非用户逐动作批准；禁止 destructive reset/clean/force-push。
- **Observer 只读**；**DSH 不是 Hermes 替代品**、不接管真实客户端配置、不写 Task Ledger 状态。

## 必读文件

- `AGENTS.md`（执行规则）→ `50-taskpacks/TASKPACK_SUMMARY.md` → `WORK-LAB-MASTER-2.0-APPROVAL-PACKAGE.md` → 本摘要所指的完整交接文档。

## 关键工具命令

- 测试铁律：`env -u PYTHONPATH uv run --frozen --group ci --group ci-adapters pytest`
- 质量门：`python 10-workflow/workflow-assistance/scripts/workflow/run_quality_gate.py verify`
- terminal 必须经 `hermes-project-data.py --project . run -- <单命令>`（禁 chaining/重定向/外部路径）。
- pnpm 逐次 pin：`node .hermes/task-runtime/run-pnpm.js <cwd> <args>`（`corepack pnpm@11.7.0`，不改全局）。
- DSH CLI：`node .hermes/task-runtime/run-dsh.js <source> <dsh-home> <dsh命令>`（`web` / `--profile headless "任务"` / `--dump-config --profile web`）。

## 建议执行顺序

读 AGENTS.md + 交接文档 → 处理体积膨胀（等批准）→ review DSH 交付物 → 申请 commit → WL3-100/110 → DSH-040（批准后）→ 其余 WL3。每步外部变更前列出精确动作等批准，不自我授权。
