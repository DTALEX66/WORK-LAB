# Codex 性能诊断与配置审计（2026-08-10）

## 结论

Codex 跑任务慢的主因**不在项目配置、也不在全局配置**，而在第三层：
`~/.codex/config.toml`（Codex 客户端用户配置）的运行参数。两层配置均为轻量且节流设计。

## 分层证据

### L1 项目配置（如 Cognitive-Loop-OS）— 节流，非拖慢源

- `AGENTS.md` 6.5KB：安全/git/网络规则，轻量
- `docs/VERIFICATION_POLICY.md`：分级验证
  - 纯文档/机械格式 → 本地 checkpoint，不跑全量 pytest
  - 低风险垂直切片 → 只跑受影响测试 + changed-file Ruff
  - TaskPack checkpoint → 不重复全量套件、不逐个 push/CI
  - 仅高风险（安全/权限/DB/架构/依赖）→ 全量门禁 + exact-SHA CI

### L2 全局配置（WORK-LAB 增强模块）— 轻量，非拖慢源

- `codex-assets/global-guidance.md` 7.8KB + `rules/workflow-assistance.rules` 4.3KB
- 纪律要求仅 2 条：scan 结论须本地核验；新行为 RED→GREEN→定向→项目 gate
- 部署形态：`~/.codex/AGENTS.md` 受管块 9KB（BEGIN/END 标记完整）+ 10 skills
- 每次会话注入 ~12KB 上下文 → 首 token 略慢，可忽略

### L3 Codex 客户端用户配置 `~/.codex/config.toml` — 主因

| 字段 | 现值 | 每任务代价 |
|---|---|---|
| `[windows] sandbox = elevated` | 提升权限沙箱 | 每条命令提升权限启动，Windows 最慢档 |
| `approval_policy = on-request` | 按请求询问 | 每次写/网络操作停等批准 |
| `base_url = http://127.0.0.1:15721/v1` | 本地代理中转 | 每请求经中转 |
| `supports_websockets = False` | 非流式 | 长回复传输低效 |
| `model_reasoning_effort = medium` | 中档推理 | token 生成折损 |
| `[mcp_servers.node_repl] startup_timeout_sec = 120` | Computer-Use 节点运行时 | 会话拉起慢启动兜底 |
| WORK-LAB 不在 `[projects]` trusted | 仅 CLO 被信任 | 本项目内任务走 untrusted 沙箱 |

### L4 工作流纪律（本会话实测）

- 每次改动 → 全量门禁重跑（470 测试 ≈ 41s + 21 gates ≈ 2-3min/轮）
- exact-tree 证据原则：旧树 PASS 不能转移 → 迭代放大
- CI 串行等待：PR ~5 jobs + aggregate；squash merge 后等 main CI
- Windows 进程启动：每次 git/gh/python/powershell 100-500ms
- 多 writer 环境：每次操作前后一致性核对

## 配置审计状态（同步进行，只读脱敏）

- 一致性：**PASS 无漂移**（sync verify、受管块标记、rules hash、10/10 skills、state v3 applied、preserved_user_config_fields=[]）
- 项目层：干净（AGENTS.md 2KB、无项目 .codex、1 项目 skill）

## 解决方案

### P0 已执行（无授权需求）
- 本文档沉淀 + README 入口（跨机器可带走）
- 测量基线：见下方计时样本

### P1 待用户确认（各含收益与回滚）
1. WORK-LAB 加入 `[projects]` trust（收益：去 untrusted 包裹；回滚：删一行）
2. `[windows] sandbox = elevated` 移除/降级（收益：每命令提速；回滚：恢复原行；⚠️ 需确认 Desktop 是否依赖）
3. `supports_websockets = True`（若本地代理支持；回滚：改回 False）
4. `model_reasoning_effort = low` 按任务降档（回滚：改回 medium）
5. `node_repl` MCP 在不用浏览器/Computer-Use 时禁用（回滚：恢复配置块）
6. `approval_policy` 自主批任务时放宽（安全边界，最小化使用）

### P2 长期工程
- 门禁定向化推广（`run_quality_gate.py <gate>`）到 CLO 工作流
- CI 并行 watch 多 PR；本地先跑 gate 再推
- 合并 bash 批次减少进程启动
- 固定单 writer 时段

## 测量基线（2026-08-10，Windows，git-bash）

| 样本 | 耗时 |
|---|---|
| `git status --short` | 42ms |
| `python -c pass` | 77ms |
| `powershell.exe -NoProfile -Command exit` | **593ms** |
| 治理子集 355 tests | 12.1s（历史） |
| 全量 governance 470 tests | 41.3s |
| 全量门禁 21 gates | ~2-3min/轮 |
