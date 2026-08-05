# OPEN-DESIGN-Assistance

面向 **Open Design 软件** 的 Open Design-first / Agent-compatible 商业设计智能、视觉质量、专业生产与可编辑交付增强仓。

本项目不是新的设计系统软件，也不是替代 Open Design 的工作流平台。V3 定位是：把已经吸收进来的 MINIGAME、Design-system、提示词、Schema/Tokens、运行样板、视觉资产、Open Design/Codex 配置经验，以及 V2/V2.1 的专业设计协议，沉淀为 **Open Design-first 的商业设计增强层**。

用户实际进行设计流程、主窗口画布操作、AI 调用和设计生成时，以 **Open Design 软件本体** 为主。

## 项目定义

```text
Open Design 软件
  = 真正的设计入口、主窗口/Figma-like 画布、AI 调用界面、设计流程执行处

OPEN-DESIGN-Assistance
  = Open Design 的增强层：Brief/来源/权利、专业设计方法、风格谱系、大师方法、质量门禁、生产预检、可编辑交付、案例、commercial evidence 与 provenance 证据

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

## V3 主规则

1. **Open Design 软件本体是主角**
   设计流程、主窗口设计、AI 调用、设计生成都在 Open Design 软件里完成。

2. **本仓库增强 Open Design 的专业判断与交付能力**
   本仓库提供资料、提示词、样板、配置说明、Schema/Tokens、视觉资产、运行时参考、质量 Rubric、生产预检、可编辑交付合同和能力证据。

3. **不把本仓库定义为 Open Design 替代品**
   工作流问题、设计流程执行、AI 模型选择与调用，以 Open Design 软件界面为准。本仓库只定义可复用协议、专业知识、运行验证和交付证据，不抢主入口。

4. **不把文件存在冒充运行可用**
   静态文件/Manifest 只能证明 E0/E1；Open Design daemon 注册、插件可见、Scenario/Atom 真运行和产物读回才是 E3。

5. **不再单独强调 Design-system 为主线**
   `design-system/` 是被吸收的设计资产库，服务 Open Design；不是新的主产品。

6. **原 MINIGAME 变成参考样板**
   `minigame-runtime/` 是 Open Design 做游戏 UI / 运行时验证 / 平台适配时的样板和参考实现。

7. **Open Design 内置 Figma-like 主窗口能力优先**
   主窗口设计以 Open Design 为主；外部 Figma 仅作为协作、导入导出或精修备选。

## 优先阅读

```text
project-memory/PROJECT_DEFINITION.md
project-memory/PROJECT_DEFINITION_V3.md
project-memory/MIGRATION_STATUS.md
project-memory/MINIGAME_RUNTIME_CLEANUP.md
project-memory/OPEN_DESIGN_ENHANCEMENT_RESEARCH.md
opendesign-assistance/README.md
opendesign-assistance/ARCHITECTURE_V3.md
opendesign-assistance/ROADMAP.md
opendesign-assistance/config/product-manifest.json
opendesign-assistance/config/capability-status.json
opendesign-assistance/scripts/doctor_open_design_windows.py
opendesign-assistance/scripts/verify_open_design_assistance.py
opendesign-assistance/scripts/verify_product_manifest_v3.py
opendesign-assistance/scripts/verify_runtime_contracts_v3.py
opendesign-assistance/scripts/verify_visual_scoring_v3.py
opendesign-assistance/scripts/generate_open_design_indexes.py
opendesign-assistance/scripts/scaffold_open_design_plugin.py
opendesign-assistance/plugins/INDEX.md
opendesign-assistance/templates/INDEX.md
opendesign-assistance/usage-notes/OPEN_DESIGN_PLUGIN_INSTALL.md
opendesign-assistance/usage-notes/OPEN_DESIGN_SKILL_STATUS.md
opendesign-assistance/plugins/uiux-layout-director/README.md
opendesign-assistance/plugins/graphic-design-director/README.md
opendesign-assistance/plugins/minigame-ui-director/README.md
opendesign-assistance/plugins/design-qa-critic/README.md
opendesign-assistance/plugins/brand-visual-director/README.md
opendesign-assistance/plugins/spatial-exhibition-director/README.md
opendesign-assistance/research/open-source-absorption/ABSORPTION_CANDIDATES.md
opendesign-assistance/templates/qa/anti-ai-slop-checklist.md
opendesign-assistance/templates/layouts/landing-page.md
opendesign-assistance/templates/layouts/dashboard.md
opendesign-assistance/templates/graphic/poster-cover.md
opendesign-assistance/templates/layouts/settings-panel.md
opendesign-assistance/templates/layouts/pricing-page.md
opendesign-assistance/templates/layouts/product-page.md
opendesign-assistance/templates/graphic/social-card.md
opendesign-assistance/templates/decks/pitch-deck.md
opendesign-assistance/templates/motion/motion-system.md
opendesign-assistance/templates/brand/brand-identity-system.md
opendesign-assistance/templates/spatial/culture-wall.md
opendesign-assistance/templates/spatial/exhibition-hall.md
opendesign-assistance/templates/visual/art-direction.md
opendesign-assistance/templates/visual/2d-design.md
opendesign-assistance/templates/visual/3d-design.md
opendesign-assistance/design-systems/anomaly-monitor-dark/README.md
opendesign-assistance/assets/visual-packs/anomaly-monitor-cctv/README.md
opendesign-assistance/exports/minigame-mobile-controls/README.md
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

## V3 当前状态（2026-08-05）

本仓库当前处于 **V3.0.0-staging / Phase 2+ 交接后主线**。云端主线已经包含 V3 的产品 Manifest、能力状态、Scenario/Atom/Bundle 合同、视觉评分收敛和运行时合同验证。

| 证据级别 | 当前含义 | 本仓库可声明的范围 |
|---|---|---|
| E0 declared | 目标、原则或文档已经声明 | 只能说明设计意图 |
| E1 structural | 文件、Schema、Manifest、索引和静态校验通过 | 结构可用、路径可追踪 |
| E2 isolated-runtime | 隔离脚本或 staging 合同执行成功并有读回 | 局部能力可在隔离环境执行 |
| E3 live-runtime | 当前 Open Design runtime 注册、执行并读回产物/Provenance | 才能声明运行时可用 |
| E4 release | 精确树经过审查、提交、推送和精确 SHA CI 读回 | 才能声明发布已验证 |
| E5 commercial | 外部用户、客户或生产验收存在 | 才能声明商业验证 |

当前交接结论：

- V3 产品合同、目录边界、Manifest/Schema 和静态验证已进入主线。
- Product Manifest、Runtime Contracts、Visual Scoring、V2/V2.1 既有协议 gate 已通过交接验收。
- E3 不能由文件存在或静态 gate 推导；仍需要当前 Open Design daemon 注册、最小任务、产物/阶段事件/Provenance 读回以及失败恢复证据。
- E4/E5 不在本 README 中提前宣称；它们分别需要当前精确 SHA 的发布证据和外部接受记录。

## V3 端到端能力模型

Open Design-first 的目标不是“生成一个看起来像设计的文件”，而是把专业判断和交付约束接到 Open Design 的实际设计界面与 Agent 执行链上：

```text
Brief / 文件 / 图片 / 参考
  → 来源、权利与安全门禁
  → Brief 标准化与商业设计路由
  → 竞品、Reference DNA、风格谱系与大师方法研究
  → 三个结构上有区别的方向 + 人工锁定
  → DESIGN.md / DTCG Tokens / Components / Asset Contracts
  → 图片 / HTML / PPTX / PDF / Motion / 3D / Spatial 生成
  → Domain Jury + Visual Quality Jury + 确定性检查
  → 有界精修循环与跨格式一致性
  → 数字 / 印刷 / 包装 / 空间 / 动效 / 3D 生产预检
  → 可编辑交付、BOM、Provenance、版本与回滚
  → Benchmark Case、人工评审与能力证据
```

其中 Open Design 负责项目 UI、主窗口/Figma-like 画布、Agent 启动、插件/Scenario 注册、预览、导出和运行时事件；本仓库负责协议、知识、提示词、能力包、质量门禁、生产预检和证据合同。

## 能力面与当前交付物

### 1. 产品与运行合同

- `opendesign-assistance/config/product-manifest.json`：产品定位、非目标、目录职责、能力家族、入口和安全边界的机器可读单一事实源。
- `opendesign-assistance/config/capability-status.json`：E0-E5 证据等级、状态集合、晋级规则和硬性不宣称规则。
- `opendesign-assistance/schemas/`：Brief、项目状态、视觉评分、生产预检、交付和 Provenance 合同。

### 2. 专业设计增强

- `atoms/`：来源 Intake、Brief 标准化、Reference DNA、商业预检、交付打包等细粒度能力。
- `scenarios/`：商业设计路由、品牌 360、视觉质量精修、大师方法视觉升级等有序 Pipeline。
- `bundles/`：`commercial-design-core` 与 `visual-quality-core` 等组合能力包。
- `knowledge/`：专业设计、视觉质量、风格谱系、大师方法、标准、生产与治理规则。
- `research/`：来源、许可、风格谱系、Master Studies 和开源吸收登记。

### 3. Open Design 插件、设计系统与模板

- `plugins/`：UI/UX、平面、品牌、空间展陈、小游戏 UI、HUD 和设计 QA 等 Open Design 兼容入口。
- `design-systems/`：Open Design-native 的设计系统包，例如 `anomaly-monitor-dark`。
- `templates/`：网站、Dashboard、菜单、产品页、定价页、海报、社媒、Pitch Deck、动效、品牌、空间、2D/3D 和反 AI-slop QA 模板。
- `assets/`：通过 Manifest 管理的视觉资产包；不把临时大图或来源不明素材直接当作产品资产。
- `exports/`：可交接的自包含示例和导出物，不等于所有能力均已在实时 runtime 运行。

### 4. 被吸收的参考样板

- `design-system/`：历史 DESIGN.md、Tokens、组件规则与 Open Design 界面参考。
- `minigame-runtime/`：小游戏/H5/Android WebView/微信小游戏等运行时回归样板和精选 CCTV 资产。

它们保留为参考和回归对象，不再作为本仓库的独立主产品入口，也不改变 Open Design 是实际设计运行时的边界。

## 从克隆到验证

在 Windows Bash、PowerShell 或 CI 中，先进入仓库根目录，再按顺序运行：

```bash
python opendesign-assistance/scripts/verify_product_manifest_v3.py
python opendesign-assistance/scripts/verify_runtime_contracts_v3.py
python opendesign-assistance/scripts/verify_visual_scoring_v3.py
python opendesign-assistance/scripts/verify_open_design_assistance.py
```

必要时补充既有协议验证：

```bash
python opendesign-assistance/scripts/verify_source_registry_v2.py
python opendesign-assistance/scripts/verify_v2_protocols.py
python opendesign-assistance/scripts/verify_visual_quality_v21.py
```

索引由源 Manifest/注册表生成，不要手工维护计数：

```bash
python opendesign-assistance/scripts/generate_open_design_indexes.py
```

预期的交接基线输出为：

```text
VERIFY_PRODUCT_MANIFEST_V3=OK total=203 failed=0
VERIFY_RUNTIME_CONTRACTS_V3=OK total=223 failed=0
VERIFY_VISUAL_SCORING_V3=OK total=10 failed=0
VERIFY_RESULT=OK total=456 failed=0
VERIFY_V2_PROTOCOLS=OK
VERIFY_VISUAL_QUALITY_V21=OK
```

这些输出证明当前树的合同/隔离验证通过，不自动证明 Open Design 的每个插件、Scenario 或 Bundle 已经达到 E3。

## Open Design 本机接入

本仓库提供可移植脚本和说明，但不提交用户级 Open Design 配置或 Codex OAuth 状态：

```bash
python opendesign-assistance/scripts/configure_open_design_windows.py \
  --project-root "D:\\All projects\\OPEN-DESIGN-Assistance" \
  --permission-root "D:\\All projects" \
  --dry-run

python opendesign-assistance/scripts/doctor_open_design_windows.py \
  --project-root "D:\\All projects\\OPEN-DESIGN-Assistance" \
  --strict
```

配置路径、Codex CLI、`CODEX_HOME`、代理启动器、默认 Project Location 和 daemon/API 端口的完整说明见：

- `opendesign-assistance/usage-notes/PORTABLE_OPEN_DESIGN_SETUP.md`
- `opendesign-assistance/usage-notes/OPEN_DESIGN_PLUGIN_INSTALL.md`
- `opendesign-assistance/usage-notes/OPEN_DESIGN_SKILL_STATUS.md`

订阅/OAuth 路径使用本地 Codex CLI 和当前用户的 `CODEX_HOME`，不要求把 OpenAI API Key 写入仓库。用户级权限根必须是明确批准的最小项目范围；禁止授权整个系统盘或 `E:/`。

## 插件与模板扩展规则

新增插件优先使用脚手架，避免 `SKILL.md`、Manifest 和 README 漂移：

```bash
python opendesign-assistance/scripts/scaffold_open_design_plugin.py my-plugin-director
python opendesign-assistance/scripts/generate_open_design_indexes.py
python opendesign-assistance/scripts/verify_open_design_assistance.py
```

插件应明确：输入、输出、适用类别、设计系统、引用模板、运行模式、兼容版本和证据等级。大型第三方工具、许可证不清晰的素材、模型权重、字体、私有运行时状态和凭据只能留在研究/适配边界，不能因为“参考过”就进入运行时 Prompt 或被声明为已吸收。

## 后续路线

路线按照依赖顺序推进，而不是按目录数量或 Prompt 数量推进：

1. 可信来源/权利/安全底座与能力证据。
2. 隔离 overlay 应用、回滚和现有七个插件兼容升级。
3. Scenario/Atom/Bundle 的 Open Design runtime 注册与真实任务读回。
4. 视觉质量、反 AI-slop、风格谱系和匿名大师方法引擎。
5. 品牌、UI 产品、平面 campaign、空间展陈、包装、编辑、动效和 3D 域 Pipeline。
6. 数字、印刷、包装、PPTX、Lottie、glTF/OpenPBR 等生产适配器。
7. Benchmark、回归证据、独立审查、精确 SHA 发布和外部验收。

候选方向和阶段定义见：

- `opendesign-assistance/ROADMAP.md`：Open Design 集成、插件、设计系统、模板和维护闭环。
- `opendesign-assistance/ROADMAP_V2.md`：可信底座、商业闭环、领域 Pipeline、工具适配器和商业证明。
- `project-memory/OPEN_DESIGN_V3_PHASE2_HANDOFF.md`：当前 V3 交接范围、验证结果和未完成的 E3/E4/E5 门槛。

## 协作与发布边界

- 远端 GitHub 仓库是长期代码真相；本地 live Project copy、daemon 数据和 `.hermes/` 证据不作为提交内容。
- 修改前先 `git status --short --branch`；只提交明确批准的文件。
- `commit`、`push`、PR、merge、ruleset 和 release 都需要用户授权。
- 发布前必须检查 `git diff --check`、验证结果、暂存区范围、远端 SHA 和最终 clean worktree。
- 任何描述都必须区分：已声明、结构通过、隔离运行、实时运行、发布验证和商业验证。
