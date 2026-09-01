# Token Monitor 交接摘要

更新时间：2026-08-05
项目：`D:\All projects\Workflow-assistance`
分支：`fix/project-local-task-data`

## 交接结论

Tauri 2 + Rust + Vite Windows Token Monitor 已完成当前阶段交付，并已推送到远端分支。PR #10 仍为 OPEN；最新 exact-SHA Linux/Windows CI 均通过。当前仓库不应被描述为已合并到 `main`、已安装或已发布。

## 当前 HEAD

```text
d944ad2566fc37c4ae53a8becdd522580c5022bc
```

最近相关提交：

| SHA | 内容 |
|---|---|
| `d944ad2` | 明确 LIVE/HISTORY/PAUSED 状态并补齐键盘可访问性 |
| `4af7f7a` | 防止 Provider、同名模型和重叠数据源重复统计 |
| `0dc8814` | 强化 usage 准确性、轮转 fail-closed 和托盘停靠 |
| `fd117fd` | 初始 Tauri 桌面 Token Monitor |

远端分支：`origin/fix/project-local-task-data`
PR：`https://github.com/DTALEX66/Workflow-assistance/pull/10`

## 已实现能力

- Tauri 2 + Rust + Vite Windows 桌面应用；
- Apple-inspired 浅色界面；
- Windows notification-area tray；
- 关闭窗口隐藏到托盘，托盘可显示、隐藏、退出；
- 默认“本次新增”，显式切换“历史累计”；
- 默认不读取文件，必须点击“开始监控”；
- 仅统计明确 usage 字段，不做字符、字节或上下文估算；
- GPT / Codex、DeepSeek、Kimi、Other Provider 归类；
- 显式 `provider` / `provider_name` / `vendor` 优先于模型名和文件路径；
- 同模型跨 Provider 分开统计；
- JSON / JSONL 递归 usage 解析；
- 父级 summary 与深层嵌套 usage 防重复计数；
- 相同 JSONL 内容位于不同日志行时保留为独立请求；
- 多源路径规范化，父目录覆盖子目录时避免重复扫描；
- 检测文件截断、轮转、删除或替换后暂停实时模式并要求重建 baseline；
- symlink、junction、Windows reparse point 不跟随；
- 状态区、错误提示、输入说明和键盘焦点具备基础可访问性。

## 主要错误与根因总结

### 1. 历史数据误显示为实时调用

根因：早期页面直接展示全量扫描快照，因此只调用 GPT 时也可能显示数据源中历史的 DeepSeek / Kimi。

处理：启动时建立 baseline；默认视图显示 baseline 之后的差量；历史数据只能通过“历史累计”显式查看。

### 2. 日志轮转 / 截断导致差量错误

根因：全量快照相减无法理解文件身份和历史 offset。文件缩小或被替换后可能出现漏报或负差量。

处理：后端返回文件大小快照；前端检测文件缩小、删除或替换后 fail-closed 暂停，要求重新开始监控建立新 baseline。

限制：当前仍是定时全量扫描，不是 offset/inode 级增量读取。

### 3. 父级 summary 与嵌套 usage 重复计算

根因：递归访问对象时，父对象和子对象都可能包含 token 字段。

处理：递归检测后代 usage；父级包含嵌套 usage 时不再同时计数。

### 4. 内容指纹误删合法重复请求

根因：旧指纹只由模型、时间戳和 token 数组成，相同请求可能被错误认为是同一事件。

处理：指纹加入 JSONL 行号 / JSON 节点位置；同内容不同日志行保留为两个请求。

### 5. 多源和同名模型被错误合并

根因：每个 source 独立去重，父目录 + 子目录会重复扫描；模型统计只使用 model 名称。

处理：规范化和裁剪重叠 source；模型键改为 Provider + Model；前端 baseline 差分使用相同复合键。

### 6. Provider 被文件路径误判

根因：文件路径中的 provider 名称可能覆盖真实模型或显式 Provider。

处理：优先级改为显式 Provider → 模型名 → 文件名回退。

### 7. 页面状态误导

根因：页面曾在历史模式或暂停状态仍显示 `LIVE`。

处理：状态现在区分 `LIVE`、`HISTORY`、`PAUSED`、`SOURCE ROTATED · RESTART MONITOR`。

## 验证证据

本地：

```text
Rust cargo fmt：通过
Rust cargo test --lib：8 passed
Rust cargo check：通过
node --check src/main.js：通过
npm run build：通过
npm run tauri build：通过
Python 全量测试：152 passed，5 skipped
QUALITY_GATE_PASS
git diff --check：通过
```

Release 构建产物路径：

```text
apps/token-monitor-desktop/src-tauri/target/release/hermes-token-monitor.exe
```

构建产物位于被忽略的 `target/` 下，不属于已发布安装包证据。

远端 exact-SHA CI（绑定 `d944ad2566fc37c4ae53a8becdd522580c5022bc`）：

```text
Linux：通过
Windows：通过
```

## 安全与数据边界

- 不读取真实凭据、OAuth、Cookie、`.env` 或认证状态；
- 不调用 Provider 云端 quota / balance API；
- 不上传本地日志；
- 不把 quota、余额或上下文限制当作请求级 token usage；
- 所有测试 fixture 使用项目内 `.hermes/task-runtime/`；
- 未访问或修改 `E:\`；
- 未修改 `D:\info@latest`；
- 不跟随 symlink / junction / reparse point；
- Tauri 权限未增加文件写入或凭据访问能力。

## 当前剩余事项

1. **真正增量扫描**：仍为约 3 秒一次的全量扫描；后续可设计受控的文件 identity + offset + rotation 状态机。
2. **托盘自动化验收**：代码和手动 smoke 已完成，但还缺稳定的自动化 UIA 生命周期测试，尤其是关闭隐藏、托盘恢复和托盘退出。
3. **实时错误态细分**：目前能够显示 source error、unknown usage 和 rotation pause，仍可进一步区分权限错误、解析错误和空目录。
4. **Provider 专用适配器**：当前依赖本地 JSON/JSONL 中明确 usage 字段，尚未实现 Codex session、Claude Code session、CC Switch SQLite 等专用只读 adapter。
5. **发布状态**：当前只有源码、CI 和本地 Release 构建证据；没有 installer 签名、发布页、安装验证或 `main` 合并证据。

## 下一位维护者操作顺序

1. `git status --short`，确认工作树干净；
2. 核对当前分支与 PR #10 head SHA；
3. 不要把 `target/release/*.exe` 当作已发布产品；
4. 若继续开发，先为新增行为写 Rust 回归测试，再修改解析或前端；
5. 任何 source / baseline 语义修改必须同时验证历史模式和本次新增模式；
6. 继续保持单 writer，禁止共享工作树并行写入；
7. 推送后必须用 `gh pr checks 10 --watch` 核验最新 exact SHA；
8. 合并前必须再次确认 PR head、CI、分支保护和工作树状态一致。
