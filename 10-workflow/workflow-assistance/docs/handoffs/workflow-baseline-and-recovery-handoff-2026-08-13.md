# 2026-08-13 工作流基线与恢复交接

> 范围：本机只读审计、已授权的最小受管修复，以及仓库 `main`/远端一致性回读。
> 证据等级：除明确标为“本机实测”的项目外，不将单机观察外推为其它电脑或未来版本的事实。

## 结论

WORK-LAB 是官方软件之上的工作流配置、治理与恢复层，不是日常软件更新器。

- 日常 Hermes、Codex、CC Switch、Open Design 或 OpenHuman 软件升级由用户决定，或等待官方稳定版推送；仓库只可只读报告版本、入口和兼容性。
- 如用户自行升级后破坏工作流，WORK-LAB 可在**明确授权**下恢复它声明拥有的规则、Skills、受管字段和已声明的 Hermes 文件映射；恢复前必须先计划，恢复后必须回读。
- 该恢复能力不能取代官方安装器或 runtime，不能接管 Provider、模型、认证、Token、会话、私有记忆、Desktop 内部状态、CC Switch 路由或 Open Design 的设计能力配置。

## 今日已验证和已处理事项

### 仓库与交付

- GitHub `main`、本地 `main` 和 `origin/main` 都解析为 `772847a49beffd3233183ff709460f20ecc098a3`；两端 tree 都是 `c3db4576e18f148cd241ff769e0ad88a6699c8c5`。
- PR #78 的分支 CI 和合并后 `main` CI 已通过。此文件是后续文档修正的交接，不将此前 CI 误称为本文件未来 commit 的 CI。
- 本轮基线合同验证通过：`CONFIG_OWNERSHIP_PASS layers=8 modes=4 fields=50 forbidden=5`、`STANDARD_VALIDATORS_PASS`、`PRODUCTION_EVIDENCE_PASS`。
- 机器身份回归测试为 13/13 通过；用户画像回归测试为 3/3 通过。

### Codex overlay

- 曾发现唯一的受管 Skill 漂移：`workflow-assistance-self-improvement`。
- 经用户明确授权使用 `sync_codex_global_assets.py apply` 对齐后，`verify` 返回 `PASS` 且 `issues=[]`；后续 `plan` 返回 `write_set_count=0`。
- 该同步仅处理 14 个明确声明的 Codex overlay Skill 及缺失时的三个受管字段；用户已有 `approval_policy`、`sandbox_mode`、`project_doc_max_bytes` 被保留。Provider、模型、base URL、认证、MCP、插件、会话和 Desktop 状态均不在写入集。

### Hermes overlay 和诊断

- `hermes hooks doctor` 通过；已配置 hook 均存在、可信且可运行。
- Hermes 受管 overlay 的计划显示 live `config.yaml` 为 mixed ownership，操作为 `skip_mixed_ownership`；模型、Provider、认证、MCP 用户项、会话和记忆不由 portable sync 提升或覆盖。
- `sync_hermes_workflow_assets.py` 的默认行为是 ActionPlan/预览：实际写入需要同时传入 `--apply --approved`。计划输出中的 `copy tree` / `copy file` 是计划步骤，不是成功发布证明。
- 本次对该输出的错误解读已纠正；后续审计必须以 `--apply`、`ACTION_PLAN_READBACK_PASS` 和变更后哈希为写入证据，不能仅凭计划文本认定已同步。

### 入口与运行时

- 本机平台发现将 Hermes 和 Codex CLI 识别为 `UNIQUE`，未发现重复 runtime。
- 经用户直接明确授权，Open Design 桌面代理快捷方式曾被替换为唯一官方入口：`Open Design.lnk` 直达官方 `Open Design.exe`；创建后先验证目标存在，再删除旧代理快捷方式。此为一次性用户桌面修复，不是 WORK-LAB 当前声明的受管恢复能力或同步器写入面。
- Hermes、CC Switch、Open Design 的当前桌面入口均经目标存在性回读。OpenHuman 本机未安装；记为不适用，不得虚构为已验收。
- Open Design 的设计能力、模型/工具选择、生成参数、设计资产和设计规范仍属于 `DESIGN-LAB`，WORK-LAB 不管理或恢复。

## 尚未构成项目缺陷的事项

- Hermes 检测到可用上游更新，只是版本提示：不是 WORK-LAB 的日常修复任务。只有用户决定更新后发生工作流损坏，才进入“授权恢复”路径。
- 运行时模型/Provider 和推理强度是用户/官方配置面。WORK-LAB 可以依据所有权合同报告不兼容或违反明确的安全规则，但不以“日常调参”名义自动覆写。
- Open Design 与 OpenHuman 的完整运行时/设计能力验证必须在各自的官方或独立项目边界内完成；本机单次入口检查不等于设计能力、认证或模型链路验收。

## 恢复操作标准

发生升级后或用户报告故障时：

1. 只读发现官方 runtime 身份、版本、唯一入口、受管资产状态与所有权合同；不读取秘密或私有正文。
2. 将差异归类为：官方 runtime/安装问题、WORK-LAB 受管 overlay 漂移、用户 overlay、未知/隔离字段，或外部项目问题。
3. 仅对 WORK-LAB 明确拥有的路径生成无密 ActionPlan；未知、重复、symlink/reparse、越界或混合所有权冲突必须 fail-closed。
4. 用户批准后，使用目标客户端的稳定官方接口或受审查同步器进行最小 apply/rollback；保留用户配置。
5. 执行 verify、幂等 plan、入口/运行时回读；Git 变更另走 PR、exact-SHA CI、合并和远端回读。

## Windows shell 互操作规则

本机 `terminal` 经 Git-Bash/MSYS 调用。把 PowerShell 脚本置于 Bash 双引号时，Bash 会先展开 `$variable`，导致 PowerShell 接收到损坏脚本。

- 简短 PowerShell：使用 Bash 单引号包裹 `pwsh -NoProfile -Command '...'`，PowerShell 内用双引号。
- 多行或有副作用的 PowerShell：在项目 `.hermes/task-runtime/` 生成可审查 `.ps1`，再以 `pwsh -NoProfile -File` 运行。
- 不将 PowerShell 的 `--%` 当作解决方案：它发生在 PowerShell 启动后，无法阻止 Bash 预先展开。

## 下一次任务起点

1. 不因发现官方软件更新而主动更新软件。
2. 若用户报告升级后损坏，先按本文件的只读分类和 ActionPlan 路径恢复受管 overlay。
3. 若修改本仓库文档/合同/同步器，重新执行质量门禁并通过新 PR 的 exact-SHA CI；此前 #78 仅证明其自身合并 SHA。
