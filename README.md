# OPEN-DESIGN-Assistance

Open Design 增强与 MINIGAME 生产系统总仓。

本仓库的主方向已经调整为：**增强 Open Design 软件为主**，把原来的 MINIGAME 游戏生产系统、Design-system / Design Command Center、Open Design 配置经验与提示词全部吸收进来，形成一个面向 Open Design 的设计-实现-验收中枢。

## 核心定位

```text
Open Design Desktop = 主前端设计界面 / 主窗口设计平台 / Figma-like 画布
OPEN-DESIGN-Assistance = 增强 Open Design 的协议、提示词、模板、游戏系统样板与自动化资料库
MINIGAME runtime = 被吸收的原游戏生产系统样板，可供 Open Design 生成和验收时参考/复用
Design-system = 被吸收的 Open Design-first 设计系统与 Design Command Center
```

## 目录结构

```text
design-system/             原 D:\All projects\Design-system，Open Design-first 设计系统
minigame-runtime/          原 D:\All projects\MINIGAME 的游戏生产系统源码/文档/测试/平台样板
opendesign-assistance/     后续新增的 Open Design 增强层：适配器、提示词、工作流、模板
project-memory/            吸收记录、迁移说明、决策与边界
```

## 使用入口

优先阅读：

```text
project-memory/ABSORPTION_PLAN.md
design-system/OPEN_DESIGN_START_HERE.md
design-system/OPEN_DESIGN_WORKFLOW.md
design-system/DESIGN.md
minigame-runtime/README.md
```

## Open Design 主规则

Open Design 里已经有 Figma 主窗口 / Figma-like 画布能力，因此：

```text
主窗口设计以 Open Design 为主
外部 Figma 只作为协作、导入导出或精修备选
Codex/GPT 只按 Schema / Tokens / Component Rules / Artifact 实现
```

## 被吸收内容

- 原 MINIGAME 游戏生产系统：源码、H5、Canvas、Android WebView、微信小游戏样板、skins、schemas、tests、docs、generated CCTV assets。
- 原 Design-system：Open Design-first Design Command Center、DESIGN.md、UI Schema、Design Tokens、component rules、Open Design prompts。
- Open Design GPT/Codex 订阅配置经验：通过本地 Codex CLI 与 `CODEX_HOME` 使用订阅登录态，不要求 OpenAI API Key。

## 不纳入 Git 的本地内容

为了避免仓库膨胀和泄露本机环境，以下本地运行/缓存类目录不并入 Git：

```text
.git/
.gradle/
.tools/
.tmp/
.hermes/
node_modules/
coverage/
test-output/
```

这些不是产品协议或源码资产，可按需要在本地重新生成。
