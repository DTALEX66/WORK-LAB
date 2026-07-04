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
scripts/      换电脑配置 Open Design/Codex/项目位置的脚本
usage-notes/  Open Design 软件使用、配置、调用 AI、落地样板的说明
templates/    可复制的任务单、scorecard、artifact、Schema/Tokens、配置模板
prompts/      给 Open Design / Agent 使用的高质量提示词
adapters/     Open Design 与 Codex/GPT/Hermes/运行样板之间的连接说明或脚本
```

## 主规则

- 用户实际设计时进入 Open Design 软件。
- 用户实际调用 AI 时也在 Open Design 软件里完成。
- 本目录只负责让 Open Design 更好用、更懂项目、更容易把输出落地。
- Open Design 内置/Figma-like 主窗口设计能力优先；外部 Figma 只是协作、导入导出或精修备选。
