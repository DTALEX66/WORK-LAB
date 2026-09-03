# WORK-LAB 工作流运行时交接（2026-08-22）

## 交接结论

Hermes 与 DeepSeek Harness（DSH）已按“官方运行体 + 用户配置”恢复，并从桌面唯一入口完成实际启动验证。WORK-LAB 仓库只记录治理合同与交接，不接管认证、会话、记忆或桌面内部状态。

| 软件 | 交接状态 | 运行证据 |
| --- | --- | --- |
| Hermes | `INSTALLED_RUNTIME_VERIFIED` | `v0.20.5`；`HEAD == origin/main == 261a4efb90d7dbe4e71786861858f721b4ab730c`；桌面进程已启动 |
| DSH 后端 | `INSTALLED_RUNTIME_VERIFIED` | 官方源码 `0.1.1-rc.2`；唯一监听 `127.0.0.1:3080`；`GET /` 返回 200 |
| DSH 桌面 | `INSTALLED_RUNTIME_VERIFIED` | 单一 `dsh-desktop.exe` 进程；与 3080 存在活动连接 |
| Codex | 见独立交接 | 当前 CLI 可用，但入口候选仍需由 Hermes 收敛 |

## Hermes

- 正式源码：`C:\Users\ALEX\AppData\Local\hermes\hermes-agent`
- 安装方式：Nous Research 官方 Git 安装。
- 当前版本：`Hermes Agent v0.20.5 (2026.8.19)`。
- 精确提交：`261a4efb90d7dbe4e71786861858f721b4ab730c`，与 `origin/main` 一致。
- CLI：`C:\Users\ALEX\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe`
- 桌面唯一入口：`C:\Users\ALEX\Desktop\Hermes.lnk`
- 快捷方式最终目标：`C:\Users\ALEX\AppData\Local\hermes\hermes-agent\apps\desktop\release\win-unpacked\Hermes.exe`
- 快捷方式不经过 VBS；旧 `Hermes_Desktop.vbs` 与快捷方式备份已删除。
- 用户 provider、model、认证、会话、记忆和未知配置字段未读取、未清理、未覆盖。

更新验收必须同时满足：`hermes --version` 正常、Git `HEAD` 与显式 `origin/main` 相同、桌面快捷方式目标存在。不要用错误的 tracking branch 或单一版本字符串代替精确提交验证。

## DeepSeek Harness

- 安装根：`D:\All projects\DSH`
- 官方源码唯一根：`D:\All projects\DSH\deepseek-harness\source`
- 官方版本：`0.1.1-rc.2`
- 用户状态根：`D:\All projects\DSH\deepseek-harness\dsh-home`，必须保留。
- 桌面程序：`D:\All projects\DSH\dsh-desktop\src-tauri\target\release\dsh-desktop.exe`
- 桌面唯一入口：`C:\Users\ALEX\Desktop\DeepSeek Harness.lnk`
- 后端：`127.0.0.1:3080`

实际启动链为：

```text
DeepSeek Harness.lnk
  -> dsh-desktop.exe
  -> D:\All projects\DSH\run-dsh.js
  -> deepseek-harness\source（官方 0.1.1-rc.2）
  -> web profile / 127.0.0.1:3080
```

`dsh-maintain.js` 是桌面端调用的非阻塞维护组件，`run-dsh.js` 是桌面端启动官方源码的必要桥接，两者不是第二套前端。旧 `deepseek-harness\launch\DSH_Desktop.vbs` 及其图标目录已经删除。

冷启动时 3080 可能先监听而 `/` 短暂返回 404；必须按条件等待，直到 `GET http://127.0.0.1:3080/` 返回 200，再判定启动结果。最终验收同时观察到单一桌面进程、单一监听和 8 条活动连接。

## 已执行清理

- 两阶段永久删除 45 个目标，盘点值合计约 17.91 GB。
- 第一阶段删除 38 个已确认可再生目标，约 10.28 GB。
- DSH：npm/pnpm store、测试健康页面、历史运行日志、旧 VBS 启动目录。
- Hermes：音频/图像/bootstrap/通用缓存、历史日志、临时目录、Python/pytest/research 临时缓存、快捷方式备份、旧 VBS 启动器。
- WORK-LAB：task-runtime 下的通用/pip/plugin/pycache/tmp 缓存、下载归档、旧安装器与 Hermes/DSH 更新临时包。
- 正式源码、构建后的桌面程序、虚拟环境、`node_modules`、DSH 用户目录和 WORK-LAB 活跃账本均保留。

Hermes 重启后会立即重建空的 audio/image cache、约 32 KB 的基础 cache 和约 1.59 MB 的 Python bytecode cache；这些目录的创建时间均晚于清理时间，属于当前运行所需的新缓存，不是历史缓存残留。

第二阶段经用户在风险知情后明确授权，永久删除以下 7 个已退出启动链的历史回滚目录，约 7.62 GB：

```text
D:\All projects\DSH\deepseek-harness\source-legacy-0.1.0-rc.7-quarantined-20260822
C:\Users\ALEX\AppData\Local\hermes\.curator_backups
C:\Users\ALEX\AppData\Local\hermes\backups
C:\Users\ALEX\AppData\Local\hermes\path-backups
D:\All projects\WORK-LAB\.hermes\task-runtime\dsh-backup-2026-08-20
D:\All projects\WORK-LAB\.hermes\task-runtime\dsh-backup-2026-08-20-rc7
D:\All projects\WORK-LAB\.hermes\task-runtime\git-mirror-backup-20260816.git
```

删除后逐路径验证结果为 `Remaining=[]`。这些目录不能从本机恢复；其中旧 DSH 未提交内容已经丢弃，正式官方源码仍可从上游重新取得。

## 后续维护规则

1. Hermes 更新只使用 Nous Research 官方更新器；更新后复核版本、精确 SHA、用户 overlay 和桌面入口。
2. DSH 更新只替换唯一官方源码根；不要并行保留第二个活动 source 目录。
3. DSH 桌面重建后，必须从“后端完全停止”状态只点击桌面快捷方式验证，不得预先手动启动 3080。
4. 缓存可清理，用户状态、认证、会话、记忆和未知配置字段不可作为缓存处理。
5. 运行证据必须区分结构检查、实际进程、HTTP、精确版本和 Git 提交。
