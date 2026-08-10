# WORK-LAB 当前错误、问题与交接

> 交接时间：2026-08-06 08:12 +0800

> 权威项目：`DTALEX66/WORK-LAB`

> 当前本地根：`D:\All projects\WORK-LAB`

## 1. 当前项目定位

WORK-LAB 是一个单根 monorepo，也是全局项目工作流的任务包控制面，不是第四个产品。

正式模块只有：

- `10-workflow/workflow-assistance`：客户端中立的 AI 工作流治理、执行增强与只读观测。

WORK-LAB 根目录负责任务包、治理、证据、所有权、数据边界、恢复和跨模块交付；实际产品/知识实现必须留在上述模块根内。

Hermes Home、Hermes 全局配置、认证、会话、cron、provider 路由、skills、plugins、缓存和官方 Hermes 源码均属于外部平台状态，不属于 WORK-LAB 代码，也不得被吸收到本仓库。

## 2. 发生过的主要错误与问题

### 2.1 旧 checkout 无法归档

三个旧本地 checkout 初始无法通过 Windows 原生重命名归档，表现为：

- Python `os.rename()` 返回 `errno=13` / Windows `WinError 32`；
- 含义是其他进程仍在使用目录或其内部文件；
- 根因不是 Git lock，也不是 Git Bash 的 `mv`；
- 根因是 Desktop Electron PTY 子进程长期把旧项目目录作为 CWD，并持有目录相关句柄。

修复方向是稳定 Desktop CWD 加显式项目 `cwd`，并通过 PTY 生命周期 graceful release 释放指定项目及其子目录的会话；不采用强杀进程或删除目录的方式绕过锁。

验证结果：

- `diagnose-lock` 能明确报告无管理员权限时句柄枚举不可用，而不是伪造结果；
- rename/delete-share probe 通过；
- `release-path` 在无活动锁时返回 `NO_ACTIVE_LOCK`；
- 三个旧 checkout 均通过 Python 原生 `os.rename()` 物理归档；
- 原始路径不存在，归档路径存在，归档 `.git` 保留。

Hermes 目录句柄修复保留在外部 Hermes 本地 checkout 中，未作为 Hermes 源码吸收到 WORK-LAB，也没有推送到官方 `NousResearch/hermes-agent`。

### 2.2 项目定位发生漂移

中途曾把“外部 Hermes 句柄修复”错误地当成 WORK-LAB 的发布对象，并讨论向官方 Hermes 仓库推送。这是错误定位。

纠正后的边界是：

- Hermes 修复是外部平台问题的本地诊断/修复资产；
- WORK-LAB 只记录项目治理、迁移、证据和外部边界；
- WORK-LAB 不吸收 Hermes 源码，也不向官方 Hermes 仓库推送；
- WORK-LAB 的云端发布目标只有 `DTALEX66/WORK-LAB`。

核查结论：官方 Hermes 远端没有本次修复 commit，因此不存在需要撤回的官方推送。

### 2.3 staging 与 archive 混淆

曾同时存在两个项目外目录：

- `D:\All projects\WORK-LAB-STAGING-20260805T120000Z`
- `D:\All projects\WORK-LAB-ARCHIVE`

二者用途不同：

- staging 是旧的、干净的迁移候选 checkout；
- archive 是迁移恢复证据和旧 checkout 的物理归档。

逐文件比对后确认 staging 与 canonical 文件集合完全一致，仅有 9 个已被 canonical 吸收的旧版本文件差异，没有独有任务或恢复文件，因此 staging 已按用户授权删除。

archive 含以下不可替代证据，必须保留：

- `FINAL_MIGRATION_STATE.json`
- `source-checkouts-archive-manifest.json`
- `local-archive-manifest.json`
- `source-checkouts/`
- `physical-checkouts/`
- 三个保留 `.git` 的物理归档 checkout

### 2.4 测试体系不兼容

新增 Desktop 测试最初使用 `node:test`，但项目平台门禁通过 Vitest 收集，导致全量平台测试报告 `No test suite found`。

已将新增测试改为项目现有 Vitest 风格，当前定向结果：

- 2 个测试文件通过；
- 5 个测试通过；
- typecheck 通过；
- lint 0 errors，保留既有 warnings。

### 2.5 Windows package 输出目录被占用

原 `release\\win-unpacked` 被正在运行的 Hermes/Electron 进程占用，直接覆盖会产生 `EPERM`/`EBUSY`。

处理方式：

- 未强杀进程；
- 使用独立输出目录完成 Windows unpacked package 验证；
- package、identity/icon stamping 和 Electron 版本验证通过；
- 独立验证目录已在验证后删除，未进入源码提交。

### 2.6 全量平台测试的边界

WORK-LAB 自身门禁已通过。外部 Hermes 全量 CLI/Electron 测试仍存在若干既有 Windows/POSIX、symlink、SSH 和平台差异失败，不能被误报为全量通过。

本项目交接只采用 WORK-LAB 自身的验证结果，不把外部 Hermes 的平台失败冒充 WORK-LAB 失败，也不把外部 Hermes 定向通过冒充 WORK-LAB 产品完成。

## 3. 当前交付与验证证据

### WORK-LAB Git 状态

- 当前 HEAD：`80400da0fd16b8f7ca634f5bb0ce450ff0fb1126`
- 远端：`https://github.com/DTALEX66/WORK-LAB.git`
- 当前分支：`main`
- `HEAD == origin/main`
- 工作树 clean
- 无未提交、无未推送变更

### 当前云端 CI

- Run ID：`31058551327`
- `headSha`：`80400da0fd16b8f7ca634f5bb0ce450ff0fb1126`
- 状态：`completed`
- 结论：`success`

### WORK-LAB 门禁

- Workflow quality gate：PASS
- Workflow tests：152 passed / 5 skipped
- Contract tests：2 passed
- Security path check：PASS
- `git diff --check`：PASS

### 归档边界

- staging：已删除，路径确认不存在；
- archive：保留；
- 三个旧物理 checkout：存在且 `.git` 保留；
- 三个旧源路径：确认不存在；
- `E:\`：本次未访问。

## 4. 当前应保留的边界

不得执行以下操作：

- 不要把 Hermes Home、认证、session、provider、cron、skills、plugins 或缓存复制进 WORK-LAB；
- 不要向 `NousResearch/hermes-agent` 官方仓库推送或重写历史；
- 不要删除 `90-archive-manifests/migration-20260805/` 内的证据文件（manifest、FINAL_MIGRATION_STATE、AUDIT_CLEANUP_GATE）；
- 不要使用 force-push、destructive reset、广泛 `git clean` 或强杀进程；
- 不要把 `productionRelease=NOT_CLAIMED` 改成已发布，除非有真实 installer、checksum、发布资产和公开回读证据。

## 5. 恢复入口

1. 先读取本文件和 `00-governance/migration-status.json`。
2. 确认 `git status --short --branch`、`HEAD`、`origin/main` 和 exact-SHA CI。
3. 需要恢复旧 checkout 或历史时：
   - 迁移证据：`90-archive-manifests/migration-20260805/`（manifest、FINAL_MIGRATION_STATE、AUDIT_CLEANUP_GATE）。
4. 以 `source-checkouts-archive-manifest.json` 和 `FINAL_MIGRATION_STATE.json` 作为恢复证据入口。
5. 任何跨模块修改都必须有明确 task pack、单一 writer、允许路径、回滚句柄和完整门禁。

## 6. 交接结论

当前 WORK-LAB 已完成本次迁移、定位纠偏、staging 清理、任务包门禁和云端发布。归档证据仍保留，外部 Hermes 状态仍与项目隔离，当前不声称产品 release 或 Hermes 官方发布。
