# Project Definition｜OPEN-DESIGN-Assistance

## 最终定义

`OPEN-DESIGN-Assistance` 是一个 **全面辅助增强 Open Design 软件** 的仓库。

它不是：

- 另一个独立设计系统产品
- 替代 Open Design 的工作流系统
- 替代 Open Design 的设计界面
- 独立主线的 MINIGAME 仓库

它是：

- Open Design 软件的增强资料库
- Open Design 的提示词/模板/适配器/参考实现仓库
- Open Design 进行 AI 设计调用时可参考的上下文仓库
- Open Design 生成游戏 UI / 原型 / 视觉资产后可用来验证和落地的样板仓库

## 用户使用方式

用户进行实际设计时，进入：

```text
Open Design 软件
```

在 Open Design 里完成：

- 主窗口 / Figma-like 画布设计
- AI 模型调用
- 设计流程执行
- 原型生成
- 设计迭代
- 视觉输出

本仓库只提供辅助内容，不把用户从 Open Design 软件中拉出来。

## 本仓库的价值

本仓库负责把已吸收的内容变成 Open Design 可用的增强上下文：

```text
prompts           给 Open Design / Agent 的高质量提示词
adapters          Open Design 与 Codex/GPT/Hermes/运行样板之间的连接说明或脚本
templates         任务单、scorecard、artifact、Schema/Tokens 模板
references        从 MINIGAME 和 Design-system 吸收来的参考实现
runtime samples   可运行样板，用于验证 Open Design 输出是否能落地
assets            CCTV/HUD/游戏 UI 视觉参考资产
```

## 内容吸收后的角色变化

### design-system/

原先它像一个独立设计系统。现在它变成：

```text
Open Design 的设计上下文 / Schema-Tokens 参考 / 视觉合同样板
```

### minigame-runtime/

原先它是 MINIGAME 游戏系统。现在它变成：

```text
Open Design 的游戏 UI 生成参考 / 运行时落地样板 / 平台适配验证对象
```

### opendesign-assistance/

这是后续主开发区。它承载：

```text
Open Design 增强提示词
Open Design 使用说明
Agent/Codex 集成说明
样板到 Open Design 的吸收方法
Open Design 输出到运行样板的落地方法
```

## 决策边界

- 工作流怎么走、在哪里设计、调用什么 AI：以 Open Design 软件本体为主。
- 本仓库不再争夺“流程主控”定位。
- 本仓库只做 Open Design 的资料增强、上下文增强、样板增强、落地增强。
- 后续新增内容应优先放入 `opendesign-assistance/`，除非明确是在维护被吸收样板。

## 一句话

```text
Open Design 负责设计与 AI 调用；OPEN-DESIGN-Assistance 负责让 Open Design 更懂项目、更会生成、更容易落地。
```
