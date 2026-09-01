# Workflow-assistance 审计、交接与错误总结

日期：2026-08-02（Asia/Shanghai）
仓库：`DTALEX66/Workflow-assistance`
分支：`main`
基线 HEAD：`f8901c3f1cf7ad4fe1447fcfee573b19d8cd67cb`

## 1. 交接结论

本次候选包含三组相互关联但可独立回滚的修改：

1. **Codex Windows launcher**：动态解析当前 Microsoft Store owner，不把 Store 版本、路径或 hash 永久写死；Bash/CMD launcher 保持同一运行时身份边界。
2. **Context7 portable baseline**：默认固定审阅过的包版本；候选 MCP 仍需单独执行 pinned provenance 审计。
3. **项目数据边界**：任务启动前将临时文件、构建输出、依赖缓存、Python bytecode、Cargo/Rust、npm/yarn、Playwright、Ruff/mypy/pre-commit 等路径绑定到所属项目的 `.hermes/task-runtime/`；历史 `D:\a`、`D:\d`、`D:\dev`、`D:\tmp` 只作为外部恢复审计来源，不作为新任务目标。

项目运行数据与恢复证据不进入 Git：

```text
<project>/.hermes/task-runtime/
<project>/.hermes/task-artifacts/
```

已审计的历史外溢根在清理后均不存在；`D:\info@latest` 是独立 UniApp/Vue/Vite 项目，未修改、未移动、未删除。

## 2. 关键实现

- `bin/hermes-project-data.py`
  - 为子进程准备项目本地 runtime layout；
  - 注入 `TMP/TEMP/TMPDIR`、XDG/pip/uv/npm/yarn/Playwright、`RUSTUP_HOME`、`CARGO_HOME`、`CARGO_TARGET_DIR`、Ruff/mypy/pre-commit 和 Python bytecode 路径；
  - 使用 reparse-point 安全检查，避免恢复/清理跟随 junction 或 symlink。
- `scripts/workflow/run_taskpack_agent.py`
  - TaskPack 子进程使用同一项目本地缓存和构建路径。
- `scripts/workflow/run_quality_gate.py`
  - 质量门禁自身也使用同一项目本地 runtime，避免门禁制造外溢缓存。
- `bin/hermes-project-terminal-guard.py`
  - 正常策略是先完成项目路径注入；仅对硬编码旧外溢路径、绕过项目环境绑定的命令提供 fail-closed 兜底，并提示使用 `.hermes/task-runtime`。
- `config/skill-provenance.yaml`
  - 已更新 `project-data-boundary` 当前源文件 hash。

## 3. 错误与修复总结

### 已发现并修复

1. 初始规则把目标错误表达成“拒绝写入外溢目录”，没有突出“自动归属到自己的项目目录”。
   - 修复：改为启动前项目内重定向，显式硬编码外部路径仅作为兜底拦截。
2. `run_taskpack_agent.py` 缺少 `CARGO_HOME/CARGO_TARGET_DIR/RUSTUP_HOME` 等完整注入。
   - 修复：补齐 Cargo/Rust、npm/yarn、Playwright、Ruff/mypy/pre-commit 等变量。
3. `run_quality_gate.py` 使用了 `pip-cache` 但 layout 未声明该路径。
   - 修复：增加项目内 `pip-cache`，质量门禁重新通过。
4. `project-data-boundary` 修改后 provenance hash 未同步。
   - 修复：更新 `config/skill-provenance.yaml`，重新通过 provenance gate。
5. 初始边界测试使用了错误的 `unittest` package 路径调用方式。
   - 修复/验证：改用 `unittest discover`；全量测试正常。
6. 早期审计中的外溢目录含有旧 runtime、Cargo target、pycache、HTTP 响应和截图混合物，不能整目录删除。
   - 修复：按项目归属迁移证据，按可再生性和 hash 记录后精确删除缓存。

### 仍需明确标记的边界

- 当前验证证明的是**仓库源代码、项目 wrapper、隔离 portable install 和本地门禁**。
- 当前 Hermes Home 的 live hook 仍显示为已授权且未变化；本次没有未经单独授权修改 Hermes Home。
- 推送后必须以新提交的 exact SHA 重新核对 GitHub CI；旧 SHA 的 CI 不能作为新提交的发布证据。
- 本次不执行 merge、release 或 live profile apply。

## 4. 验证证据

已执行并通过：

```text
项目边界测试：30 tests，OK
全量 unittest：147 tests，OK (skipped=5)
QUALITY_GATE_PASS
SKILL_PROVENANCE_PASS
PORTABLE_INSTALL_VERIFY_PASS
hermes hooks doctor：All shell hooks look healthy
项目内环境回读：全部标准缓存/构建/临时路径位于项目 .hermes/task-runtime
D:\a/D:\d/D:\dev/D:\tmp：最终不存在
git diff --check：通过
```

质量门禁的 `RUNTIME_COMPATIBILITY_UNVERIFIED` 仅表示 provider 网络执行没有作为本地默认门禁，不等于代码门禁失败；portable isolated runtime gate 已通过。

## 5. 回滚与维护

- 回滚到本次父提交：`f8901c3f1cf7ad4fe1447fcfee573b19d8cd67cb`。
- 不删除 `.hermes/task-runtime` 中仍被活动任务使用的目录；失败任务现场需先交接再清理。
- 不访问或迁移 `E:\` 数据；不读取 credential/auth/session/browser 文件。
- 新任务必须经项目 wrapper 启动，不得直接把 `TMP/TEMP/CARGO_TARGET_DIR/npm cache` 指到盘符根、用户目录或另一个项目。

## 6. 上传状态

本文件记录的是上传前候选审计。提交后应回读：

- commit SHA；
- `origin/main` 是否指向该 SHA；
- exact-SHA GitHub Actions 结果；
- 工作树是否干净。

在这些回读完成前，不应称为“已发布”或“CI 已通过”。
