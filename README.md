# OPEN-DESIGN-Assistance

全面辅助增强 **Open Design 软件** 的主仓库。

本项目不是新的设计系统软件，也不是替代 Open Design 的工作流平台。它的定位是：把已经吸收进来的 MINIGAME、Design-system、提示词、Schema/Tokens、运行样板、视觉资产和 Open Design/Codex 配置经验，全部沉淀为 **Open Design 软件的辅助增强包**。

用户实际进行设计流程、主窗口画布操作、AI 调用和设计生成时，以 **Open Design 软件本体** 为主。

## 项目定义

```text
Open Design 软件
  = 真正的设计入口、主窗口/Figma-like 画布、AI 调用界面、设计流程执行处

OPEN-DESIGN-Assistance
  = Open Design 的辅助增强仓库：资料、样板、提示词、接口约定、参考实现、配置经验、验收材料

被吸收的 MINIGAME / Design-system
  = 给 Open Design 提供参考、样板、素材、Schema/Tokens、运行时验证对象；不再单独定义主流程
```

## 当前主目录

```text
D:\All projects\OPEN-DESIGN-Assistance
```

云端仓库：

```text
https://github.com/DTALEX66/OPEN-DESIGN-Assistance
```

旧目录仅作为历史来源/临时备份，不再作为主开发入口：

```text
D:\All projects\Design-system
D:\All projects\MINIGAME
```

## 目录职责

```text
opendesign-assistance/     面向 Open Design 软件本体的增强资料：scripts / plugins / design-systems / assets / prompts / templates / usage notes
design-system/             已吸收的设计协议资产：DESIGN.md / Schema / Tokens / component rules，供 Open Design 参考或导入
minigame-runtime/          已精简的游戏系统参考样板：运行时、平台样板、测试、精选素材，供 Open Design 生成/验证时参考
project-memory/            项目定义、迁移记录、吸收边界、清理决策记录
```

## 主规则

1. **Open Design 软件本体是主角**  
   设计流程、主窗口设计、AI 调用、设计生成都在 Open Design 软件里完成。

2. **本仓库只辅助增强 Open Design**  
   本仓库提供资料、提示词、样板、配置说明、Schema/Tokens、视觉资产、运行时参考和验证材料。

3. **不再把本仓库定义为工作流中心**  
   工作流问题、设计流程执行、AI 模型选择与调用，以 Open Design 软件界面为准。本仓库只记录和增强，不抢主入口。

4. **不再单独强调 Design-system 为主线**  
   `design-system/` 是被吸收的设计资产库，服务 Open Design；不是新的主产品。

5. **原 MINIGAME 变成参考样板**  
   `minigame-runtime/` 是 Open Design 做游戏 UI / 运行时验证 / 平台适配时的样板和参考实现。

6. **Open Design 内置 Figma-like 主窗口能力优先**  
   主窗口设计以 Open Design 为主；外部 Figma 仅作为协作、导入导出或精修备选。

## 优先阅读

```text
project-memory/PROJECT_DEFINITION.md
project-memory/MIGRATION_STATUS.md
project-memory/MINIGAME_RUNTIME_CLEANUP.md
project-memory/OPEN_DESIGN_ENHANCEMENT_RESEARCH.md
opendesign-assistance/README.md
opendesign-assistance/ROADMAP.md
opendesign-assistance/scripts/doctor_open_design_windows.py
opendesign-assistance/plugins/uiux-layout-director/README.md
opendesign-assistance/plugins/graphic-design-director/README.md
opendesign-assistance/plugins/minigame-ui-director/README.md
opendesign-assistance/plugins/design-qa-critic/README.md
opendesign-assistance/research/open-source-absorption/ABSORPTION_CANDIDATES.md
opendesign-assistance/templates/qa/anti-ai-slop-checklist.md
opendesign-assistance/templates/layouts/landing-page.md
opendesign-assistance/templates/layouts/dashboard.md
opendesign-assistance/templates/graphic/poster-cover.md
opendesign-assistance/design-systems/anomaly-monitor-dark/README.md
opendesign-assistance/assets/visual-packs/anomaly-monitor-cctv/README.md
opendesign-assistance/usage-notes/PORTABLE_OPEN_DESIGN_SETUP.md
opendesign-assistance/scripts/configure_open_design_windows.py
opendesign-assistance/prompts/OPEN_DESIGN_MAIN_WINDOW_UI_PROMPT.md
design-system/DESIGN.md
minigame-runtime/README.md
```

## 已吸收内容

- 原 MINIGAME 游戏生产系统：源码、H5、Canvas、Android WebView、微信小游戏样板、skins、schemas、tests、docs、运行必需的精选 CCTV assets。
- 原 Design-system：Open Design-first Design Command Center、DESIGN.md、UI Schema、Design Tokens、component rules、Open Design prompts。
- Open Design GPT/Codex 订阅配置经验：通过本地 Codex CLI 与 `CODEX_HOME` 使用订阅登录态，不要求 OpenAI API Key。

这些内容现在统一作为 Open Design 的辅助增强材料使用。

## 不纳入 Git 的本地内容

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
