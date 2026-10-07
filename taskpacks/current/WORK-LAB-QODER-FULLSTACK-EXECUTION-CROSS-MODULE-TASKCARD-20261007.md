# WORK-LAB 前后端完整执行 — 从属跨模块任务卡（2026-10-07）

**Card ID:** `WORK-LAB-QODER-FULLSTACK-EXECUTION-CROSS-MODULE-TASKCARD-20261007`
**Card class:** subordinate cross-module execution task card（承载 `AGENTS.md` 要求的"一张明确的跨模块任务卡"，并登记本轮 owner 授权的仓内范围）
**Parent authority:** `WORK-LAB-AUTHORITY.md` → `.project/governance/project-authority-index.json` →
`WORK-LAB-UNIFIED-PRODUCT-CONVERGENCE-TASKPACK-20260918`（唯一 CURRENT）→ 本卡。
**Single live register:** `taskpacks/current/OPEN-TASK-REGISTER.md`（本卡不建立平行账本，进展只回写唯一 register）。

> 本卡**不自立为新 Authority**，也不新增状态枚举。它的执行权限完全来自 owner 2026-10-07 的日期化指令
> （来源钉住见 §1，优先级"最新明确用户决定 > 一切"）。卡本身**不授予**任何交付动作。

## 1. 来源钉住（授权材料身份，按 SHA 而非记忆）

| 项 | 值 |
|---|---|
| 文件 | `.project-local/artifacts/qoder-handoff-20261007/QODER_新规划前后端完整后续任务提示词.txt` |
| 字节 | 29,230 B |
| SHA-256 | `17e064354c0b7c2d3a1db2524b1db1b9150bd78cdd650a21ff1ca08ee50109c2` |
| mtime (UTC) | `2026-10-07T15:06:10+00:00` |
| 落点 | 该文件位于被忽略的运行根 `.project-local/artifacts` 内，不作仓库真值，不改变权威顺序 |

## 2. 本轮范围（批次 A—F，全部仓内）

批次 A 基线/门禁/工程债 · B 读投影与主工作面 · C 独立 Control 后端与薄壳 · D 薄入口/Launcher/handoff/恢复 ·
E UI 全量产品化与真实桌面验证 · F 后台能力与实际消费验收。章节号即提示词的第五至第十节，
逐条落地状态只写进唯一 register 对应行。

## 3. 跨模块写权清单（本卡承载的具体对象）

`AGENTS.md`：跨模块改动需一张明确跨模块任务卡；`.project/governance/module-ownership.json` 记
`crossModuleWrites: explicit-cross-task-only`。本卡授权触碰的**非本会话默认归属**对象，逐项列出：

| 路径 | 所属 | 本卡内的动作 | 边界 |
|---|---|---|---|
| `packages/client-neutral-core/bin/hermes-project-terminal-guard.py`、`scripts/artifact_flow_policy.py`、`scripts/platform_collector.py`、`scripts/verify_gate_runtime_convergence.py`、`bin/hermes-project-data.py` | workflow 模块（owner=workflow） | 修真实缺陷：临时目录留在 project-local、扫描器对 list 裸字符串漏检 | 只修已登记缺陷，不扩功能，不改 Hermes 原生状态 |
| `services/**`（活动支撑面，非 module root） | workflow/控制平面 | Control 合同与服务、handoff 消费接线、影响分析接线 | 复用既有进程服务与唯一账本，禁第二 backend |
| `apps/observer/**` | observer 模块（owner=observer） | 读投影补齐、UI 产品化、状态矩阵、几何门 | **永久严格只读**（§5 硬边界 2） |
| `apps/control-surface/**`（本轮按需新建的最小薄壳） | 由本卡声明、待 owner 确认落 module-ownership | 只承载写动作薄壳，复用 tokens/components/types | 不整树复制 Observer，不建第二 Ledger |
| `config/config-ownership.json`、`.project/governance/**` | root-owned | 声明补齐、覆盖矩阵可变源更新 | 投影 Markdown 只用生成器写 |

## 4. 授权与不授权（逐字保护边界）

授权：本仓范围内的前后端开发、合同补齐、缺陷修复、项目内构建与必要验证，含独立 Control Surface 的
loopback-only 后端与前端薄壳。

**不授权（本轮绝不执行，需按操作另行批准）**：commit、push、开 PR、merge、tag/release、安装到用户系统、
改全局配置、跨项目写真值、付费调用、跨 Provider 传输私人数据、访问 `E:\`/`F:\`、批量删除。
真缺外部授权的动作**只暂停该分支**，其余任务继续。

## 5. 硬边界（不可协商）

1. 本地个人使用：禁止新增登录、锁屏、密码、访问令牌、API key、JWT、OAuth、Vault、凭证管理、账号中心或企业鉴权层。
2. Observer 与它的 sidecar 永久严格只读：不执行、不批准/拒绝、不取消/重试、不 apply/rollback/install、
   不写 Task/Telemetry Ledger；POST/PUT/PATCH/DELETE 的 405 保持，不加隐藏写 deep-link。
3. 写操作只经独立 Control 服务调用现有 Python 控制平面；不新建第二 Task Ledger / Evidence Store /
   Config Authority / Context Authority / Agent Runtime / Usage-Cost 引擎 / CURRENT。
4. 保留 React+TS+Vite / Tauri2+Rust / Python / JSON Schema 职责划分；不全仓 Rust 重写，不自建 IDE/终端/Git 客户端/通用聊天产品。
5. `apps/observer/web` 已退役，不复活；不恢复手机端导航/底栏/第二静态生产 UI。
6. 不读、打印、复制、提交或上传 `.env`、密钥、Token、Cookie、认证库、私钥、私人 memory/session 数据、提示词或响应正文；
   UI 投影只用允许的元数据与产物引用，样本用项目内合成或明确获准公开材料。
7. 缓存/临时/日志/构建产物留 `.project-local/runs`，证据与交接留 `.project-local/artifacts`；
   环境配置只用进程级/任务级值，不改系统 PATH、注册表、ACL、服务或计划任务。
8. 不全局安装、不自动重装软件、不拉模型、不删除历史或旧权重；无具体能力缺口不加组件包。
9. 一个 checkout 一个 writer；先保护 dirty/untracked；不 `reset --hard`、不 `clean`、不批量 restore/checkout、不 force push、不改写历史。
10. `UNKNOWN≠0`、`STALE≠LIVE`、`HTTP 200≠完成`、`自报 completed≠Completion PASS`、`UI success≠原生副作用`、`estimated≠实付`。

## 6. 单写者与工作树

本会话独占主 checkout `D:\All projects\WORK-LAB`（分支 `task-decomposition/atlas-gap-archive-20261001`）。
接手时存在的 8 项未提交修改 + 2 项未跟踪文件（Reduced Motion 修复、抽屉真值文案、两项机器本地素材读取改为具名
skip、U03 登记更正、报告 §17）**由本卡承接收尾，不覆盖、不撤销**。
`.project-local/worktrees/ui-20261007` 是上一轮的隔离 worktree，本卡不写入。

## 7. 验证契约

命令、退出码、实际执行项、required skip/cancel/missing、工具链与工作树身份全部留痕；
FAIL 不写 PASS，合成不写 REAL，本地不写 exact-SHA CI，build 不写 installed，历史绿不写当前新树通过。
canonical 门：`python services/orchestration/run_quality_gate.py verify`（项目声明 Python
`.project-local/toolchains/wl-py311/Scripts/python.exe`）。

## 8. 回滚

本卡是加法文档记录：删除本卡 + `taskpack-authority-index.json` 的对应 `currentTaskCards[]` 条目 +
register 行即完全撤销本卡；代码改动按批次在 register 行内逐项给出回滚句柄。不依赖改写历史。
