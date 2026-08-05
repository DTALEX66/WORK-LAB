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

## V3 任务包能力面

V3 不是单纯的 Prompt 文件集合，而是围绕 Open Design runtime 组织的合同化增强层：

```text
Source / rights / security gate
  → brief normalizer
  → commercial design router
  → scenario / atom / bundle
  → research / reference DNA / style lineage
  → anonymous master-method translation
  → three directions + human lock
  → generation and visual-quality jury
  → production preflight
  → editable delivery + BOM + provenance + rollback
```

对应目录职责：

| 目录 | 作用 | 当前证据边界 |
|---|---|---|
| `config/` | Product Manifest、Capability Status、运行策略 | 机器可读合同；静态通过不等于 runtime ready |
| `schemas/` | Brief、状态、评分、预检、交付、Provenance 合同 | 结构和引用可验证 |
| `atoms/` | 有界、可测试的细粒度能力 | 需要隔离执行和读回才能升级 E2 |
| `scenarios/` | 商业设计和视觉质量 Pipeline | 需要 Open Design 真实任务才能升级 E3 |
| `bundles/` | `commercial-design-core`、`visual-quality-core` 等组合包 | 组合声明不等于完整编排已完成 |
| `plugins/` | Open Design 兼容的 V1 技能入口 | Manifest 存在不等于当前 daemon 已注册 |
| `knowledge/` / `research/` | 专业知识、来源、许可、风格与大师研究登记 | 研究记录不自动成为可运行 Prompt |
| `evals/` / `profiles/` | Rubric、回归、生产预检配置 | 是质量与交付门，不是商业验收 |
| `design-systems/` / `assets/` | Open Design 原生设计系统和视觉资产 Manifest | 资产必须有来源和许可边界 |
| `exports/` | 自包含示例和交接物 | 单个导出物不代表全链路能力 |

## 当前 V3 验证基线

交接时主线已通过以下 gate：

```bash
python scripts/verify_product_manifest_v3.py
python scripts/verify_runtime_contracts_v3.py
python scripts/verify_visual_scoring_v3.py
python scripts/verify_open_design_assistance.py
```

基线结果：

```text
VERIFY_PRODUCT_MANIFEST_V3=OK total=203 failed=0
VERIFY_RUNTIME_CONTRACTS_V3=OK total=223 failed=0
VERIFY_VISUAL_SCORING_V3=OK total=10 failed=0
VERIFY_RESULT=OK total=456 failed=0
VERIFY_V2_PROTOCOLS=OK
VERIFY_VISUAL_QUALITY_V21=OK
```

上述结果覆盖 Product Manifest、Runtime Contract、Visual Scoring、V2/V2.1 协议和统一增强层验证。它们证明当前仓库的结构和隔离合同收敛，不直接证明每个能力在当前 Open Design daemon 中完成 E3 注册、真实任务执行、产物读回和失败恢复。

## E3/E4/E5 晋级条件

只有同时具备下列证据，能力才能从 E2 isolated-pass 晋级为 E3 runtime-pass：

1. 当前 Open Design daemon 返回运行时 ID 和版本。
2. 支持的 API/CLI 能列出目标 Plugin、Atom、Scenario 或 Bundle。
3. 最小任务经过声明的 stage contract 执行。
4. 产物、阶段事件和 Provenance 可以读回并相互关联。
5. 失败、重试、回滚或恢复行为有记录。

E4 还需要冻结的精确树、独立审查、用户授权的提交/推送和同一 SHA 的 CI 读回；E5 需要真实项目、人工/外部评审和接受记录。不要用文件数量、Prompt 数量、模型自评分或一次成功截图替代这些证据。

## 本机 Open Design 接入

仓库脚本只负责可重复配置和诊断，不保存 API Key、OAuth token 或私有运行时数据：

```bash
python scripts/configure_open_design_windows.py \
  --project-root "D:\\All projects\\OPEN-DESIGN-Assistance" \
  --permission-root "D:\\All projects" \
  --dry-run

python scripts/doctor_open_design_windows.py \
  --project-root "D:\\All projects\\OPEN-DESIGN-Assistance" \
  --strict
```

配置完成后要从 daemon 日志读取实际端口，再检查 `/api/app-config`、技能/插件 registry 和 Codex 连接；连接成功只证明 Agent adapter 可达，不等于 Scenario/Atom 已完成 E3。

## 新增插件/模板的固定闭环

```bash
python scripts/scaffold_open_design_plugin.py my-plugin-director
python scripts/generate_open_design_indexes.py
python scripts/verify_open_design_assistance.py
```

每个插件至少要保持 `SKILL.md`、`open-design.json`、`README.md` 三件套，并在 README 中说明输入、输出、适用类别、设计系统、引用模板、兼容性和当前证据等级。模板、研究来源和资产 Manifest 必须可追溯；许可证不清晰的外部材料只能登记为 candidate/reference，不能伪装成已吸收运行能力。

## 维护优先级

当前依赖安全的顺序是：

1. 保持 Manifest、Schema、索引和验证脚本的一致性。
2. 完成 Open Design runtime 对 V3 Plugin/Atom/Scenario/Bundle 的真实注册和任务读回。
3. 以真实 benchmark case 验证视觉质量、生产预检和可编辑交付。
4. 再推进跨格式适配器、独立审查、精确 SHA 发布和外部验收。

不要因为某个目录已存在，就把它写成“已完成商业设计平台”。本目录是 Open Design 的增强资料与合同层，Open Design 软件本体仍是用户实际设计和调用 AI 的地方。
