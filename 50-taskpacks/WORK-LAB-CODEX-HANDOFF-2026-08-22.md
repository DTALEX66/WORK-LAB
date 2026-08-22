# WORK-LAB → Hermes：Codex 运行时交接（2026-08-22）

## 交接边界

按用户指令，Codex 的真实用户运行时收敛交由 Hermes 执行。WORK-LAB 继续拥有声明式治理合同、managed overlay 源和验证工具，但本轮不直接改写 Codex 用户配置、认证、会话、记忆、Desktop 内部状态或 provider/model/base URL。

权威边界：

- `10-workflow/workflow-assistance/config/config-ownership.json`
- `10-workflow/workflow-assistance/config/codex-enhancement-boundary.json`
- `10-workflow/workflow-assistance/docs/workflow/codex-enhancement-boundary.md`
- `10-workflow/workflow-assistance/docs/workflow/codex-global-enhancement.md`

## 当前只读采样

- CLI：`codex-cli 0.149.0`
- PowerShell 当前首选：`C:\Users\ALEX\AppData\Local\hermes\node\codex.ps1`
- 同时发现的其他候选包括 Hermes Node 包的 `codex.cmd`/`codex`、Hermes managed `bin\codex.cmd`/`bin\codex`，以及 WindowsApps 官方 Codex 包内 executable。
- WindowsApps 包采样路径版本：`OpenAI.Codex_26.818.4152.0_x64__2p2nqsd0c76g0`。
- `codex --version` 可正常执行；本轮未读取用户 `config.toml`、认证文件或私有运行时。

当前交接状态为 `PARTIAL`：运行体可用，但入口候选不满足“wrapper candidates resolve to exactly one runtime”的五维基线。PowerShell 首选项当前绕过 `C:\Users\ALEX\AppData\Local\hermes\bin\codex.cmd`，必须由 Hermes 完成入口收敛后再升级为 `INSTALLED_RUNTIME_VERIFIED`。

## Hermes 待执行任务

1. 在不删除 WindowsApps 官方包、不读取认证内容的前提下，采样 `Get-Command codex -All`、`where.exe codex` 和各候选的最终 executable。
2. 选择 Hermes managed wrapper 作为唯一用户命令入口；Bash/CMD wrapper 必须使用相同的版本化 glob 与同一最终 runtime。
3. 调整入口时只处理 PATH/重复 wrapper，不删除官方 Codex Desktop 包，不重置 `.codex`，不覆盖 provider/model/base URL。
4. 使用 canonical 同步器先 `plan`，人工核对 write set 和排除项；只有明确批准后才 `apply`，随后 `verify`。
5. 对真实用户运行时执行以下验收：
   - `codex --version`
   - PowerShell、CMD、Bash 三种 shell 的入口解析
   - managed wrapper 只解析到一个官方 executable
   - Codex Desktop 正常启动
   - 用户 provider/model/auth/session 保持不变
6. 将最终入口、CLI 版本、Desktop 包版本、同步器 verify 结果和未执行项回写到本文件或新的日期化交接。

## Canonical 命令位置

从模块根 `10-workflow/workflow-assistance` 执行：

```text
python scripts/workflow/sync_codex_global_assets.py plan --codex-home C:/Users/ALEX/.codex --agent-home C:/Users/ALEX/.agents
python scripts/workflow/sync_codex_global_assets.py verify --codex-home C:/Users/ALEX/.codex --agent-home C:/Users/ALEX/.agents
```

应用操作必须使用已审阅的 plan digest 和项目规定的批准参数；不得把 `plan` 或项目内测试当作真实用户运行时已应用的证据。

## 禁止事项

- 不读取、复制、输出或删除 Codex 认证、会话、记忆和私有状态。
- 不整文件覆盖用户 `config.toml`。
- 不把 Hermes 当前聊天模型/提供商当作 Codex Desktop 用户配置事实。
- 不因存在多个扩展名入口就直接删除官方 WindowsApps 包；先解析最终目标和 PATH 优先级。
- 不由 Codex 自己执行这次全局收敛；按用户要求由 Hermes 接管。


---

## 2026-08-21 Hermes 执行回写（收敛完成）

- 同步器：BLOCKED（managed 块被外部移除 + unowned targets）→ 备份清理 → plan(17 write set) → apply(14 skills + config 块，sandbox_mode 用户值保留) → **verify PASS**。
- 入口收敛：drift 修复（Store 26.818.5229 codex.exe 同步到 plugin_bin + per-user bridge，SHA256 一致）→ npm 包装（@openai/codex）已卸载 → **PATH 唯一入口 = Hermes managed `bin/codex.cmd` + `bin/codex`（bash/CMD 同一 runtime）**。
- 三 shell 验收：PowerShell / CMD / git-bash 均解析到 `codex-cli 0.149.0-alpha.4.1`（Store 官方通道）。WSL bash（WindowsApps bash.EXE）UTF-16 乱码不可用——用户环境为 git-bash，不受影响。
- 未执行：Codex Desktop GUI 启动验收（用户操作）；provider/model/auth/session 未触碰（verify PASS + preserved 字段确认）。
- 状态：**INSTALLED_RUNTIME_VERIFIED**（入口唯一 + 运行时一致 + 同步器 PASS）。
