# OpenDesign Assistance Layer

这里是后续主开发区：专门为 **Open Design 软件本体** 做辅助增强。

## 定位

```text
Open Design 软件 = 设计流程、主窗口画布、AI 调用、原型生成的实际入口
opendesign-assistance/ = 给 Open Design 提供提示词、模板、适配器、参考说明和落地样板连接
```

这里不负责替代 Open Design 的工作流，也不负责把设计流程从 Open Design 软件里搬出来。

## 目录方向

```text
scripts/      换电脑配置/诊断/验证 Open Design/Codex/项目位置和增强资产的脚本
plugins/      Open Design 本地插件：UI/UX、平面、品牌、文化墙/展厅、2D/3D、小游戏 UI、HUD、设计审查
design-systems/ Open Design 原生设计系统包
assets/       Open Design 可引用的视觉资产包 manifest
usage-notes/  Open Design 软件使用、配置、调用 AI、落地样板的说明
templates/    UI/UX、平面、菜单、网站、排版、QA 等可复用设计能力模板
research/     开源插件/技能/DESIGN.md 可吸收清单与取舍记录
prompts/      给 Open Design / Agent 使用的高质量提示词
adapters/     Open Design 与 Codex/GPT/Hermes/运行样板之间的连接说明或脚本
```

## 验证

```bash
python opendesign-assistance/scripts/verify_open_design_assistance.py
python opendesign-assistance/scripts/generate_open_design_indexes.py
```

该验证脚本统一检查 Open Design 插件 manifest、SKILL 引用、模板库、索引、设计系统、视觉资产包和关键 README 入口。

新增插件时使用：

```bash
python opendesign-assistance/scripts/scaffold_open_design_plugin.py my-plugin-director
```

插件安装/调用说明：

```text
opendesign-assistance/usage-notes/OPEN_DESIGN_PLUGIN_INSTALL.md
```

技能/连接器可用性状态说明：

```text
opendesign-assistance/usage-notes/OPEN_DESIGN_SKILL_STATUS.md
```

注意：本地 `.od-skills` 文件存在且可读，不等于已经被当前 Codex 会话注册成自动触发的正式系统技能。需要 Open Design daemon/API 或真实调用证据确认后才能升级状态。

## 主规则

- 用户实际设计时进入 Open Design 软件。
- 用户实际调用 AI 时也在 Open Design 软件里完成。
- 本目录只负责让 Open Design 更好用、更懂项目、更容易把输出落地。
- Open Design 内置/Figma-like 主窗口设计能力优先；外部 Figma 只是协作、导入导出或精修备选。
