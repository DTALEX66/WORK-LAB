# Absorption Plan｜把原游戏系统并入 OPEN-DESIGN-Assistance

## 用户决策

用户新建云端仓库：

```text
DTALEX66/OPEN-DESIGN-Assistance
```

本地目录：

```text
D:\All projects\OPEN-DESIGN-Assistance
```

后续方向改为：

```text
增强 Open Design 软件为主
```

因此原来的游戏系统、设计系统、Open Design 配置经验都要吸收到本仓库中。

## 吸收原则

1. **不覆盖原仓库**：`D:\All projects\MINIGAME` 和 `D:\All projects\Design-system` 原目录不删除、不重写。
2. **新仓库成为总中枢**：OPEN-DESIGN-Assistance 以后承载 Open Design 增强、设计协议、游戏样板、提示词、验收标准。
3. **保留可运行样板**：原 MINIGAME 源码、测试、H5/Android/微信样板、skins、schemas、docs、generated assets 进入 `minigame-runtime/`。
4. **保留设计协议**：原 Design-system 整体进入 `design-system/`。
5. **排除本地缓存/工具链**：`.git`、`.gradle`、`.tools`、`.tmp`、`.hermes`、`node_modules` 等不进入 Git。
6. **Open Design 主窗口为准**：Open Design 内置/包含 Figma-like/Figma 主窗口能力；外部 Figma 只作为协作或导入导出备选。

## 目标结构

```text
OPEN-DESIGN-Assistance/
├─ README.md
├─ design-system/
│  ├─ OPEN_DESIGN_START_HERE.md
│  ├─ OPEN_DESIGN_WORKFLOW.md
│  ├─ DESIGN.md
│  └─ 05_DESIGN_COMMAND_CENTER/
├─ minigame-runtime/
│  ├─ src/
│  ├─ assets/
│  ├─ docs/
│  ├─ tests/
│  ├─ android-webview/
│  ├─ wechat-minigame/
│  └─ package.json
├─ opendesign-assistance/
│  ├─ README.md
│  ├─ prompts/
│  ├─ adapters/
│  ├─ templates/
│  └─ workflows/
└─ project-memory/
   └─ ABSORPTION_PLAN.md
```

## 后续开发方向

### Phase 1：吸收

- 把 Design-system 并入 `design-system/`。
- 把 MINIGAME 并入 `minigame-runtime/`。
- 建立 Open Design 增强层骨架。
- 提交并推送到新 GitHub 仓库。

### Phase 2：增强 Open Design

把过去散落在 MINIGAME / Design-system 的流程，提炼成 Open Design 能直接使用的：

- prompts
- DESIGN.md 合同
- component rules
- schema/tokens handoff
- visual QA scorecards
- artifact generation workflows
- Codex/GPT subscription agent integration notes

### Phase 3：把游戏系统变成 Open Design 样板库

原游戏系统不再只是单独游戏仓库，而是作为 Open Design 的：

- anomaly game runtime sample
- Canvas/H5 implementation reference
- platform adaptation reference
- skin/reskin contract reference
- visual QA reference

## 当前吸收边界

纳入：源码、docs、schemas、skins、tests、scripts、platform samples、generated visual assets、Design-system 文档与 JSON 协议。

不纳入：本地构建缓存、SDK/toolchain、Hermes 附件缓存、Git 历史目录、node_modules、coverage/test-output。
