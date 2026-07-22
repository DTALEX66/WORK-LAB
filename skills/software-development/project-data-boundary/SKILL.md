---
name: project-data-boundary
description: "将 Agent 任务的临时文件、缓存、日志与产物锁定在当前 Git 项目的忽略目录；用于执行、审查、睡眠模式和修复任务。"
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [project-boundary, task-data, temp, cache, containment, hooks]
    related_skills: [sleep-mode, agent-workflow-fortress, hermes-agent]
---

# 项目任务数据边界

## 触发条件

当任务会生成临时文件、缓存、测试环境、日志、评审报告、下载物或运行时产物时加载。默认目标是**当前 Git 项目**，而不是用户 Home、系统 Temp、Hermes Home 或相邻项目。

## 强制边界

1. 先确定 Git 根目录；没有 Git 根目录则停止，不猜测输出位置。
2. 所有可再生产出的任务数据都必须落入：

   ```text
   <project>/.hermes/task-runtime/
     tmp/
     cache/
     logs/
     artifacts/
     pip-cache/
     pycache/
   ```

3. `.hermes/` 必须被 Git 忽略；否则 helper fail-closed，先由项目维护者加入忽略规则或在本地 Git exclude 中显式隔离。
4. 禁止把项目产物写到 `%TEMP%`、`~/.cache`、`~/.hermes/tmp`、桌面、用户 Home 或另一个项目。Hermes 的认证、会话数据库、配置、全局技能和 scheduler 元数据仍是**全局运行时状态**，不是项目产物，不能移动或删除。
5. Hermes Kanban 原生支持 `HERMES_KANBAN_HOME`，因此项目任务板不是全局状态：必须经本 helper 运行，固定落入 `<project>/.hermes/kanban/`；不得直接使用未固定 board root 的 `hermes kanban`。
6. 显式绝对路径会绕过任何环境变量；执行前必须拒绝项目根外的 output/cache/log 参数。此 helper 不是 OS sandbox，不能把任意恶意/错误子进程伪装成安全。
7. `E:\\` 是用户保护的数据区：默认禁止枚举、读取、复制、写入、移动、重命名或删除其任何数据。只有用户在**当前请求**中明确给出精确路径和操作范围时才可访问；授权按路径和本次任务限定，读权限不等于写/移动/删除权限，任务结束即失效。

## Hermes terminal gate

默认 profile 的 `hooks.pre_tool_call` 应匹配 `terminal` 并指向 `$HERMES_HOME/bin/hermes-project-terminal-guard.py`。该 hook 必须 fail-closed：要求每个 terminal call 有显式 Git-project `workdir`，且只有单个 `hermes-project-data.py --project . <subcommand>` 调用可通过；拒绝 raw command、非 Git workdir、错误 project 参数和 shell chaining。

配置/脚本变更后执行 `hermes hooks doctor`。若提示 hook 脚本在授权后变化，先 `hermes hooks revoke <command>`，再用 `hermes --accept-hooks` 启动一次新会话重新授权。Desktop/Gateway 已运行进程需 `/reset` 或重启才能注册新 hook。

## 标准执行器

部署包会把 `bin/hermes-project-data.py` 同步到 `$HERMES_HOME/bin/`。对会产生数据的命令，先检查再经 wrapper 启动：

```bash
python "$HERMES_HOME/bin/hermes-project-data.py" --project . check
python "$HERMES_HOME/bin/hermes-project-data.py" --project . run -- python -m pytest
```

`run` 会向子进程注入以下项目本地路径：`TMP`、`TEMP`、`TMPDIR`、`XDG_CACHE_HOME`、`PIP_CACHE_DIR`、`UV_CACHE_DIR`、npm/yarn、Playwright、Rust target、Ruff/mypy/pre-commit cache、`PYTHONPYCACHEPREFIX`、`HERMES_KANBAN_HOME`、`HERMES_PROJECT_RUNTIME_ROOT`、`HERMES_PROJECT_ARTIFACTS`、`HERMES_PROJECT_LOGS`。

初始化策略并运行项目本地 Kanban：

```bash
python "$HERMES_HOME/bin/hermes-project-data.py" --project . init
python "$HERMES_HOME/bin/hermes-project-data.py" --project . kanban -- boards list
```

## 审计与恢复

- 开始长任务前运行 `check`；它会验证 Git 根和 ignore 边界，并创建受控目录。
- 成功任务收尾：先将必要 handoff、review 和恢复证据写入同项目 `.hermes/task-artifacts/`，然后运行 `python "$HERMES_HOME/bin/hermes-project-data.py" --project . cleanup`。默认清除 `tmp/logs/artifacts/pycache`，保留依赖缓存；仅在确认无须加速缓存时传 `--all-regenerable`。
- 失败任务不得自动擦除现场；其项目内 runtime data 是可审计、可恢复的，不应因“自动清理”丢失根因证据。
- 外部遗留物先按内容、Git workdir、任务名称和时间追踪归属；先复制并校验 hash，再删除原路径。无法可靠归属的内容不得移动到错误项目，也不得删除。
- Windows 的 Gradle/Android 深层缓存可能超过普通 Win32 路径长度，导致 `shutil.rmtree()` 报“目录不是空的”或间歇性找不到文件。仅在已验证该路径是非 symlink、位于 `%LOCALAPPDATA%\Temp` 且属于已关闭任务的情况下，使用 Win32 extended-length (`\\?\`) 路径删除；删除后必须重新扫描目标前缀，不能把首次异常当作“已清理”。
- 若发现全局 Hermes Home 中已有明确归属项目的 Kanban board：先确认 Gateway 已停止、board 没有 running task/worker；复制到 `<project>/.hermes/kanban/`，逐文件校验大小和 SHA-256，使用 `hermes-project-data.py kanban` 实读 board/task 后，才删除全局副本与其 stale current 指针。迁移 manifest 必须留在项目 `.hermes/task-artifacts/`。
- cron 的 Hermes 原生 job 元数据/输出由 Hermes Home 管理；项目任务应在 prompt 中使用 `workdir=<project>`，并将任务证据写回项目 `.hermes/`。不要直接篡改 Hermes cron 数据库；启用有限 `cron.output_retention`，并按项目归档确定归属的孤儿输出。
- `state.db` 是跨项目桌面会话与搜索的共享库，不能按项目拆分或盲删；使用官方 session retention/auto-prune 管理结束会话。同步器产生的备份只可清理其自身有命名前缀的已验证旧副本，必须保留至少两份，绝不触碰用户 pre-update/recovery backup。
