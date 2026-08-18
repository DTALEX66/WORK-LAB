# WORK-LAB 交接摘要 · 给 DeepSeek Harness（2026-08-18）

> 完整交接见 `50-taskpacks/WORK-LAB-DSH-HANDOFF-2026-08-18.md`（**最新权威**，含 DSH 迁移 + 桌面版修复）。
> 历史基线：`WORK-LAB-DSH-HANDOFF-2026-08-15.md`。本文件是快速上手摘要。

## 接手什么

`D:/All projects/WORK-LAB`（GitHub `DTALEX66/WORK-LAB`）—— 客户端中立工作流控制面，管理 6 个 AI 客户端（Hermes / Codex / CC Switch / GitHub / OpenHuman / Open Design）+ 未来 AI 软件的 USER_GLOBAL 期望态。两活动模块：`10-workflow/workflow-assistance`（唯一 Writer）、`30-observer`（只读投影）。

## 当前状态（3 行）

1. `main` = `de29e583`（PR #117 已 merge：skill 精简 + 全局配置 14→13 Skills + 模型满血字段）。
2. **DSH 已完整迁移至 `D:\All projects\DSH`**（2026-08-18）：`deepseek-harness\`（source `47f94385` + dsh-home 全量：29 sessions、28 插件、junction 195/195）+ `dsh-desktop\`（Tauri 壳 + NSIS setup）；桌面入口 = **dsh-desktop.exe 唯一方案**（VBS 废弃），内置后端自启动，桌面快捷方式已指向新 exe。
3. **桌面版两个问题已修复**：① 插件弹窗颜色冲突（dsh-update-checker 硬编码白字 vs 深色主题品牌色反转 → node_modules 两处 CSS 补丁，插件更新会覆盖）；② 图标全套对应（根因=原图标纯白空壳 → 官方 favicon.svg 重新生成品牌图标 + 重构建 exe，exe/窗口/任务栏/快捷方式/setup 全部验证通过）。

## 下一步（按优先级）

1. **提交本次交接文档**：08-18 交接文档（新）+ SUMMARY 更新（共 2 个文件）→ 申请 commit/push（每动作需批准）。注：5 件 DSH adapter 交付物 + 08-15 交接已通过 **#118（6d675ca）** merge 进 main（含 model control plane + WL3-810 归档）。
2. **核对 main 现状**（HEAD `ad10333` control-plane 系列）与交接文档一致性。
3. **WL3-100/110 收编**（能力矩阵 + 身份模型子代理产出）。
4. **DSH-040 付费 smoke**：默认 `LOCAL_SMOKE_ONLY`，用户填 key + 批准后切真实调用。
5. **其余 WL3 任务**（120/210/220/300-330/400-420/500/510-520/610/620/720/820）。

## 不可违反的边界

- **E:\ 盘**：无逐路径逐操作授权禁止访问。
- **秘密/凭据**：不读不打印不复制不提交（含 DSH key，用户在 UI 填，Agent 不读）。
- **防外溢**：一切运行数据只在 `.hermes/task-runtime/`。
- **不 commit/push/PR/merge/release** 除非用户逐动作批准；禁止 destructive reset/clean/force-push。
- **Observer 只读**；**DSH 不是 Hermes 替代品**、不接管真实客户端配置、不写 Task Ledger 状态。
- **旧位置 DSH（`.hermes/task-runtime/deepseek-harness/`）保留不删**（回滚/对照基线）。

## 必读文件

- `AGENTS.md`（执行规则）→ `50-taskpacks/TASKPACK_SUMMARY.md` → `WORK-LAB-MASTER-2.0-APPROVAL-PACKAGE.md` → 完整交接文档（08-18 版权威）。

## 关键工具命令

- 测试铁律：`env -u PYTHONPATH uv run --frozen --group ci --group ci-adapters pytest`
- 质量门：`python 10-workflow/workflow-assistance/scripts/workflow/run_quality_gate.py verify`
- terminal 必须经 `hermes-project-data.py --project . run -- <单命令>`（禁 chaining/重定向/外部路径）。
- pnpm 逐次 pin：`node .hermes/task-runtime/run-pnpm.js <cwd> <args>`。
- DSH CLI（新位置）：`node .hermes/task-runtime/run-dsh.js "D:\All projects\DSH\deepseek-harness\source" "D:\All projects\DSH\deepseek-harness\dsh-home" <dsh命令>`。
- DSH 桌面构建：`powershell -File "D:\All projects\DSH\dsh-desktop\build-x.ps1"`（前置：SUBST `X:` → `D:\All projects\DSH\dsh-desktop` + rust GNU toolchain；`~/.cargo/config.toml` 已修转义，**不得再写未转义反斜杠**）。

## 建议执行顺序

读 AGENTS.md + 交接文档 → review DSH 交付物 → 申请 commit → 体积膨胀（等批准）→ WL3-100/110 → DSH-040（批准后）→ 其余 WL3。每步外部变更前列出精确动作等批准，不自我授权。
