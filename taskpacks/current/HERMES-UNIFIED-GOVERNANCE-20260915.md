# 三方治理收拢：全部由 HERMES 执行（2026-09-15）

用户指令：`现在 CODEX 和 DSH 的治理全部 HERMES 来执行` + 回答 `HERMES 是否能自己治理自己`。
纪律：**不干扰**（不在 ChatGPT/Codex 运行时期间强杀其进程）、全程离线不花钱（本轮零模型调用）。
分支 `r4-recovery-exec`，不合并 main。

## 三方环现状（收拢后 = HERMES 统一治理 Codex + DSH + 自检）

原三方环（Codex→DSH / DSH 独立复核 / 工具层沙箱 ACL）已按用户指令收拢为
**单一治理者 HERMES**，DSH 独立复核段不再由 DSH 自己发起。

| 环段 | 原属 | 现属 | 本轮状态 | 证据 |
|---|---|---|---|---|
| Hermes→Codex 模型层 | Hermes | Hermes | ✅ PASS（上轮 astra 真实 turn） | `codex-gpt6-live-drift-and-acceptance-2026-09-15.json` |
| Hermes→Codex 工具层 | Hermes | Hermes | ⚠️ BLOCKED（沙箱 ACL） | 本轮复测坐实，见下 |
| Codex→DSH | Codex | **Hermes** | 🔄 收拢到 Hermes，DSH 已启动待复核 | 本轮启动 DSH |
| DSH 独立复核 | DSH | **Hermes** | 🔄 收拢到 Hermes | 本轮只读结构面 |
| Hermes→Hermes 自检 | — | **Hermes** | ✅ 结构面全绿（2 信息级项） | 本轮 doctor |

## ① Hermes→Codex 工具层沙箱 ACL（复测坐实，未变）

- `icacls "C:\Users\Default"`：`BUILTIN\Users:(RX)`、`Default 用户:(S,RD,X)` —— **当前用户只读执行，无写/改属性权**。
- `codex-command-runner`（`.sandbox-bin` 现 21 个版本，0.144.0→0.154.0）以当前用户身份对
  `C:\Users\Default` 调 `SetFileAttributesW` → **ACCESS_DENIED (error 5)** → 统一 exec 创建失败。
- 判定：**非产品缺陷，是 ACL 边界**。recovery path（需用户交互，不静默）：
  ① 用户在交互式桌面跑一次让 runner 落 ACL；或 ② 授权 runner 对 `C:\Users\Default` 的属性写。
- 未 bypass 沙箱、未改 ACL、未提权（纪律）。
- Codex 不在 PATH/`scoop\shims\codex*`（`where codex` 空）——由 ChatGPT 桌面 App 内嵌管理，
  本轮**未触碰**任何 ChatGPT/Codex 进程（不干扰纪律）。

## ② Hermes 治理 DSH（只读结构面，DSH 已启动）

- **DSH Desktop 官方安装铁证**：`D:\All projects\DSH\DSH Desktop.exe` + `Uninstall DSH Desktop.exe`（NSIS）均在位。
- **已启动**：launch 前 :43120 无监听/无进程 → detached 启动 → web 起在 :43120，
  `/`、`/api/health` 返回 **401 Unauthorized**（认证门，正常安全机制，非故障）；`/plugins.json` 404。
- **`~/.dsh` 结构面全绿（只读，未读凭据正文 `.credentials.yaml`/`vision.env`）**：
  - `settings.yaml`（62KB）14 组结构键合法：`agent-default-model`（provider/model/reasoningEffort）
    是 **DSH 自己的**模型策略，与 WORK-LAB 五维基线分离——**无跨系统干扰**。
  - sessions 170MB / storages 7.5MB / memory 113KB / profiles 410MB 健康；
    `dsh-update-checker-state.json` + `skin-center-active.json` 在位。
  - `dsh-desktop.networkExposure` 结构键存在（DSH 自我网络暴露声明）。
- **DSH 段收拢**：DSH 独立复核由 HERMES 承接 = 本轮只读结构面已做；
  行为级复核（启动会话/跑任务）需用户交互授权 + 非离线（可能触发模型调用），本轮**未做**。

## ③ Hermes 自我治理（诚实能力边界）

`hermes --version` = **v0.21.2 (2026.9.11)**，**落后 upstream 1415 commits**（官方 updater 通道）。

**能自我治理（只读结构面，本轮已做，全绿）**：
- `hermes doctor`：无活跃安全通告、MCP 无可疑 stdio、Python 3.11.15 / SQLite 3.53.1 /
  SSL CA 有效、6 个 SQLite 库均 WAL 模式（state.db 3.8GB）。
- `hermes config check`：config v44 ✓（已配置 OPENROUTER_API_KEY / DEEPSEEK_API_KEY，可选键省略）。
- profile 2（default=agnes-3.0-flash / deepseek-review=deepseek-v4-flash，gateway 均 stopped）、
  plugins 21、MCP 1（context7 enabled）、cron 1 paused、sessions 1 / 246840 msgs。

**不能自我治理（需人授权，诚实声明，本轮未做）**：
1. **行为级 hook 再批准**：`hermes-project-terminal-guard.py`（pre_tool_call）自
   08-06 批准后于 **09-14 被修改** → 需 `hermes hooks doctor` 再验证，但该命令会**合成调用
   配置的 hook**（非只读）→ 审计纪律下 omit，留用户交互。
2. **gateway 陈旧 state**：`gateway_state.json` 记录 'running' 但进程已没（非优雅停机）
   → 无活跃 cron job 时属**信息级**，非故障；重启 gateway 是 mutation，不静默做。
3. **升级 1415 commits**：`hermes update` 是有副作用的 mutation，需用户授权，
   **绝不"自己治理自己"地静默升级**。
4. **secret 正文**：`.env`/`config.yaml`/`auth.json`/`.credentials.yaml` 只报结构/存在性，
   正文不读不打印不复制（纪律）。

**判定**：Hermes 能自我治理**只读结构面**（已闭环全绿）；**行为自批准/自升级/secret 治理**
超出自我治理边界，需人授权——这是设计使然（治理者不能单方面给自己放行权限或升级）。

## 本轮未做（卡外部输入 / 非离线 / 需授权）
- Codex 工具层 ACL 的 recovery（用户桌面重跑或授权属性写）
- DSH 行为级复核（需交互 + 可能触发模型调用）
- Hermes 1415-commit 升级 + hook 再批准 + gateway 重启（mutation，需授权）
- 收费四臂 / Codex 实机取消（需付费授权）
- **不干扰纪律**：本轮未 kill 任何 ChatGPT/Codex 进程；DSH 仅新开窗口，不碰现有

## 双端一致
- 分支 `r4-recovery-exec`；提交本台账 + 推送；本地=远端，main 未动，worktree clean。
