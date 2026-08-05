# OpenDesign Assistance Layer

这里是 V3 主开发区：专门为 **Open Design 软件本体** 提供 Open Design-first 商业设计智能、视觉质量、风格研究、专业生产和可编辑交付增强。

## 定位

```text
Open Design 软件 = 设计流程、主窗口画布、AI 调用、原型生成、预览和导出的实际入口
opendesign-assistance/ = 给 Open Design 提供 Brief/来源/权利、Scenario/Atom/Bundle、专业知识、Rubric、生产预检、交付合同和证据索引
```

这里不负责替代 Open Design 的工作流，也不负责把设计流程从 Open Design 软件里搬出来。静态文件只能证明结构存在；运行可用必须由 Open Design runtime 注册、真实任务、产物读回、evidence 和 provenance 证据证明。

## 目录方向

```text
config/       产品 Manifest、能力状态和运行策略的机器可读单一事实源
schemas/      Brief、方向、状态、评分、预检、交付、provenance 和 Manifest 合同
scripts/      配置/诊断/验证 Open Design、Codex、项目位置和增强资产的脚本
plugins/      V1 本地插件：UI/UX、平面、品牌、文化墙/展厅、2D/3D、小游戏 UI、HUD、设计审查
atoms/        V2/V2.1 细粒度能力：来源门禁、Brief 标准化、参考 DNA、视觉 Jury、精修、交付等
scenarios/    可运行 Pipeline：商业设计路由、品牌 360、视觉质量精修、大师方法升级等
bundles/      组合能力包：commercial-design-core、visual-quality-core
knowledge/    专业设计、风格谱系、大师方法、标准、供应链和生产规则
evals/        领域 Rubric、视觉质量模型、基线和回归评测材料
profiles/     数字、印刷、包装、空间、动效、3D 等生产预检配置
design-systems/ Open Design 原生设计系统包
assets/       Open Design 可引用的视觉资产包 manifest
exports/      Open Design 生成/交接出的自包含原型与视觉资产
usage-notes/  Open Design 软件使用、配置、调用 AI、落地样板的说明
templates/    UI/UX、平面、菜单、网站、排版、QA 等可复用设计能力模板
research/     开源/标准/风格/大师来源登记、许可状态和晋级证据
prompts/      给 Open Design / Agent 使用的高质量提示词
adapters/     Open Design 与 Codex/GPT/Hermes/运行样板之间的连接说明或脚本
```

## 验证

```bash
python opendesign-assistance/scripts/verify_product_manifest_v3.py
python opendesign-assistance/scripts/verify_runtime_contracts_v3.py
python opendesign-assistance/scripts/verify_visual_scoring_v3.py
python opendesign-assistance/scripts/verify_open_design_assistance.py
python opendesign-assistance/scripts/generate_open_design_indexes.py
```

该验证脚本统一检查 Open Design 插件 manifest、SKILL 引用、模板库、索引、设计系统、视觉资产包和关键 README 入口。

V3 机器可读入口：

```text
project-memory/PROJECT_DEFINITION_V3.md
opendesign-assistance/ARCHITECTURE_V3.md
opendesign-assistance/config/product-manifest.json
opendesign-assistance/config/capability-status.json
opendesign-assistance/scripts/verify_product_manifest_v3.py
opendesign-assistance/scripts/verify_runtime_contracts_v3.py
opendesign-assistance/scripts/verify_visual_scoring_v3.py
```

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
