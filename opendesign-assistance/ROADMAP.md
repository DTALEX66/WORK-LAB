# Open Design Enhancement Roadmap

本路线图基于 `project-memory/OPEN_DESIGN_ENHANCEMENT_RESEARCH.md`。

## 项目原则

```text
Open Design 软件 = 设计流程、AI 调用、主窗口画布的实际入口。
OPEN-DESIGN-Assistance = 增强 Open Design 的插件、脚本、设计系统、资产包和参考样板。
```

不把本仓库重新变成工作流中心；所有增强都服务于 Open Design 软件本体。

## Phase 1：可用性与迁移复用

状态：完成第一版。

已有：

```text
opendesign-assistance/scripts/configure_open_design_windows.py
opendesign-assistance/scripts/doctor_open_design_windows.py
opendesign-assistance/usage-notes/PORTABLE_OPEN_DESIGN_SETUP.md
opendesign-assistance/templates/open-design-app-config.template.md
```

下一步：把 doctor 输出接入 Open Design usage note，形成新电脑安装后的固定验收清单。

检查内容：

- Open Design 安装路径。
- app-config JSON。
- Codex CLI 可执行文件。
- Codex OAuth 登录态是否存在但不打印凭据。
- 默认 project location 是否指向本仓库。
- proxy launcher 是否存在。
- daemon log / local API 端口是否可探测。

## Phase 2：本地插件化

目标：让 Open Design 软件里能直接选择/安装我们的项目增强能力。

状态：完成第一批专项设计插件。

创建：

```text
opendesign-assistance/plugins/minigame-ui-director/
opendesign-assistance/plugins/anomaly-monitor-hud/
opendesign-assistance/plugins/uiux-layout-director/
opendesign-assistance/plugins/graphic-design-director/
opendesign-assistance/plugins/design-qa-critic/
```

每个插件遵循 Open Design 官方结构：

```text
SKILL.md
open-design.json
README.md
```

### minigame-ui-director

用途：面向小游戏/HUD/IAA 变现界面生成。

输入：

```text
platform: h5 | wechat | douyin | android-webview
screen: start | main | failure | archive | skin-select
theme: anomaly-monitor-dark | custom
```

### anomaly-monitor-hud

用途：专门生成监控终端 / CCTV / HUD 风格 UI。

输入：

```text
scene: elevator | hospital | security | factory | subway | hotel
riskLevel: low | medium | high | critical
```

### uiux-layout-director

用途：专项增强菜单、网站、产品页、dashboard、信息架构与响应式布局。

重点：

```text
- 导航分组与状态
- 页面主次层级
- mobile/tablet/desktop 响应式
- 产品化布局节奏
- 避免普通表单/后台感
```

### graphic-design-director

用途：专项增强平面设计、海报、封面、banner、社媒图和视觉 campaign。

重点：

```text
- 构图网格
- 字体层级
- 视觉焦点
- 出图尺寸
- 安全/高级/传播型三种方向
```

### design-qa-critic

用途：在 Open Design 内对生成结果做审美和落地检查。

检查：

```text
- 是否像游戏/HUD，而不是表单/问卷
- CCTV/主视觉是否占据核心区域
- 移动端可读性
- 控件是否 icon-first / short chips
- 是否可被 minigame-runtime 落地
```

## Phase 3：Open Design-native design system

创建：

```text
opendesign-assistance/design-systems/anomaly-monitor-dark/
```

目标文件：

```text
DESIGN.md
manifest.json
design-tokens.json
components.html
components.manifest.json
preview/index.html
```

来源：

```text
design-system/DESIGN.md
design-system/05_DESIGN_COMMAND_CENTER/design-tokens/anomaly_monitor_dark.tokens.json
design-system/05_DESIGN_COMMAND_CENTER/component-rules/monitor_console.components.json
```

## Phase 4：视觉资产包

创建：

```text
opendesign-assistance/assets/visual-packs/anomaly-monitor-cctv/
```

先不复制大图，使用 manifest 指向仍保留的运行必需资产：

```text
minigame-runtime/assets/generated/*
```

输出：

```text
manifest.json
README.md
prompts.md
```

用途：Open Design 生成 CCTV/HUD 视觉时引用真实资产和提示词。

## Phase 5：上游贡献候选

低风险方向：

- Codex subscription/OAuth + Windows proxy launcher 文档。
- Open Design plugin 示例：game HUD / CCTV console。
- 中文 i18n 缺口。
- Windows 本地 CLI detection/diagnostic 改进。

高风险方向暂缓：

- daemon runtime 核心改造。
- agent adapter 核心逻辑。
- BYOK streaming parser。
- media provider fallback。

## 下一刀建议

直接做：

```text
把这些本地插件在 Open Design 软件中安装/调用一遍，形成 OPEN_DESIGN_PLUGIN_INSTALL.md
```

原因：

- 第一批增强已经覆盖设计能力、平面能力、UI/UX、菜单/网站布局和游戏 HUD。
- 下一步不是继续堆文档，而是确认 Open Design 软件能识别这些 plugin/skill。
- 验证后再进入更细的模板库：landing page、dashboard、mobile menu、settings panel、poster/cover。
