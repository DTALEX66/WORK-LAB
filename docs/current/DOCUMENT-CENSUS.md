# 文档与任务总索引（DOCUMENT CENSUS）

> Record资料统一入口：`docs/history/owner-inputs/INDEX.md`（完整登记、别名、包内成员、内容去重、历史摘要）。
> 本次来源覆盖与原字节验证见`docs/history/owner-inputs/RECORD-ARCHIVE-VALIDATION.json`；旧数量仍只是原盘点快照。

> 2026-10-09范围切换：唯一CURRENT为`taskpacks/current/WORK-LAB-UI-PRIORITY-TASKPACK-20261009.md`，完整交接在`docs/current/ui-priority-20261009/NEXT-AGENT-PROMPT.md`。
> 旧文档数量/状态/建议只描述此前盘点，现行任务以OPEN为准；UI优先、手机端不做。
> 旧任务归档与逐条继承：`taskpacks/history/UI-PRIORITY-CUTOVER-20261009/FROZEN-MANIFEST.json`、`docs/current/ui-priority-20261009/LEGACY-TASK-DISPOSITION.json`。


> 本文件解决一件事：**任何会话都不该再问"任务在哪、文档在哪"**。它不新增权威，只把已有权威的位置、
> 状态与守卫一次说清；权威顺序仍以 `WORK-LAB-AUTHORITY.md` 与
> `.project/governance/project-authority-index.json` 为准。
> 生成：2026-10-08。所有数字都注明测量命令与口径；未测的写"未测"。

## 1. 新任务该落在哪（有文字依据，不是我总结的）

| 问题 | 依据（原文位置） |
| --- | --- |
| 新任务卡放哪 | `taskpacks/current/README.md`：任务权威模型是 `CURRENT TaskPack -> OPEN Register + currentTaskCards`； subordinate 卡片是"本目录内的规划记录，不是第二个 CURRENT taskpack"，其机器权威在 `.project/governance/taskpack-authority-index.json` 的 `currentTaskCards[]` |
| 唯一开放任务账本 | `README.md:16`：`taskpacks/current/OPEN-TASK-REGISTER.md`（唯一在册开放任务账本，不建第二个） |
| 归档怎么做 | `docs/current/workflow-assistance/workflow/active-authority-index.md:69-70`：新增权威文件必须登记到索引；归档操作＝移入 `taskpacks/history/` 或 `docs/history/`（保留 Git 历史），**不删除** |
| 移动会被谁拦 | `scripts/ci/verify_authority_index_paths.py` 默认扫 `docs/current/` 下全部受跟踪 md ∪ `EXTRA_SURFACES`（register + 两份设计合同面，实测 42 面）；7 个严格面（`NAVIGATION_SURFACES` ∪ `EXTRA_SURFACES`）refs=0 即 FAIL，每个面另有 refs 下限防扫描面自己缩水报绿；解析只对着 `git ls-files` |

## 2. 文档面全景（实测）

总体：`git ls-files` = **2,172** 个受跟踪文件，其中 `*.md` = **1,046**（`git ls-files -- '*.md' \| wc -l`）。

| 位置 | 数量 | 最后提交 | 角色 | 规范性 |
| --- | --- | --- | --- | --- |
| `WORK-LAB-AUTHORITY.md` | 1 | 2026-10-07 | 最高人类权威 | 是 |
| `AGENTS.md` | 1 | 2026-10-08 | 执行规则 | 是 |
| `.project/governance/` | 54 | 2026-10-08 | 机器权威（含 `.project/governance/generated/CURRENT_STATE.md`） | 是 |
| `taskpacks/current/` | 26 | 2026-10-08 | 活账本 + 当前 taskpack + 卡片 | 是 |
| `docs/current/` | 43 md（2026-10-10 复测；2026-10-08 记为 38） | 2026-10-10 | 当前工作文档 | 是（受引用门禁） |
| `docs/decisions/` | 18 | 2026-10-07 | ADR、`docs/decisions/global-execution-standard.md`、`docs/decisions/instruction-precedence.md` | 是 |
| `docs/future/` | 3 | 2026-10-08 | 蓝图与覆盖投影（含生成物） | 计划 |
| `taskpacks/history/` | 81 | 2026-10-08 | 冻结历史 | **非规范** |
| `docs/history/` | 115 md | 2026-10-08 | 冻结历史 + `docs/history/archive/` + `docs/history/archive/recovered-originals/` | **非规范** |
| `reports/` | 527 | 2026-10-06 | 审计证据（`reports/audit-archive/` 479、`reports/audit-evidence/` 34） | 证据 |
| `knowledge-staging/` | 224 | **2026-09-23** | 边界标记为 `HISTORY_ONLY_CONVERGE`，非活动模块 | 冻结候选 |
| `90-archive/` | 1 | **2026-09-24** | 只剩边界标记文件；内容 2026-09-23 已并入 `docs/history/` | 冻结候选 |
| 仓库根 `*.md` | 11 | 混合 | **8 个不在权威链里**（2026-10-10 复测；原记 10）（见 §4） | 混杂 |

## 3. "自称是任务清单"的东西有 9 份，只有一份是账本（2026-10-10 复点；标题原记 10，下表逐名点数实为 9）

实测口径：`grep -cE '^\| [A-Za-z0-9._-]+ \| P[0-9]' taskpacks/current/OPEN-TASK-REGISTER.md` = **163 行**
带优先级的在册任务行（另一口径按"表头行"数到 183，差异来自无优先级单元格与续行；两个数都写出来，
避免下次又为"到底多少条"吵架）。

| 声称者 | 处置 |
| --- | --- |
| `taskpacks/current/OPEN-TASK-REGISTER.md` | **唯一账本** |
| `WORK-LAB-AUTHORITY.md` §14（18 条"当前未决"） | 权威摘要，条目须与账本一致；不一致时以账本行 + 机器合同为准 |
| `docs/future/WORK-LAB-BLUEPRINT-COVERAGE.md` | **生成物，禁手改**；实测 22 个 U 行里 **19 行读 `UNVERIFIED`** 而账本读 `IMPLEMENTED@…`/`CLOSED_LOCAL` → 词汇过期不是新事实，由 `scripts/ci/verify_blueprint_coverage.py --write` 重生成 |
| `README.md`、`taskpacks/current/README.md`、`docs/decisions/PROJECT_POSITIONING.md`、`docs/audits/BLUEPRINT_SYNC_AUDIT_2026-10-06.md`、`taskpacks/current/WORK-LAB-UNIFIED-…-20260918.md` | 描述/投影，不得当账本读 |
| `taskpacks/history/OPEN-TASK-REGISTER-20260917.md` | 冻结孪生，非规范 |

## 4. 仓库根目录是真正的踩坑点

根上有 **8 个不在权威链里的 md（105.9 KB，2026-10-10 复测；原记 10 个约 127 KB）**，其中两份**看起来像活任务**：

- `HANDOFF-UI-L10B.md`（12,588 B）开头即 `⛔ CLOSED — DO NOT RE-EXECUTE`，但放在根目录，新会话按文件名读就会误接；
- `UI_IMPLEMENTATION_REPORT.md`（54,649 B，2026-10-08）与 `reports/UI-CHECK-OBSERVER-20261006.md` 角色重复。

**处置（本索引提出，未擅自执行）**：`git mv` 进 `docs/history/archive/` 是规范动作，但这些路径被
`README.md`、账本行与 `docs/current/workflow-assistance/workflow/active-authority-index.md` 引用，移动会同时打红引用门禁。因此要求：**先改引用、
再移动、同一提交内完成**，并让 `scripts/ci/verify_authority_index_paths.py` 当场复验。逐个移动的清单见 §7。

**2026-10-10 执行结果（WUI-17：移动被证伪，改为就地标注＋机器守护）**：先量消费者，再决定动不动，结论是
**这六份历史记录今天不能移**。逐名引用实测（口径：`grep -rl -F "UI_IMPLEMENTATION_REPORT.md"`，
扩展名 md/json/py/csv，全仓排除 `.project-local/`，含其自身 = **21** 个文件点名；其中
`taskpacks/history/UI-PRIORITY-CUTOVER-20261009/original-tree/**` 3 份、`docs/audits/` 3 份、`tests/` 2 份、
`taskpacks/current/error-ledger.json` 1 份、`HANDOFF-UI-L10B.md` 1 份），关键约束是：
它被两份测试当作**伪证夹具**使用
（`tests/workflow-assistance/test_path_text_is_one_predicate.py:83`、
`tests/workflow-assistance/test_control_service.py:385-400`——该夹具的作用是让"折叠大小写后仍在根内"这类断言
必须真红，见 `tests/workflow-assistance/test_control_service.py:385` 的注释），以及**活账本**`taskpacks/current/error-ledger.json:5574`
在某条记录的 `fix` 文字里逐字引用了它；`taskpacks/history/UI-PRIORITY-CUTOVER-20261009/original-tree/**`
在 `.gitattributes` 里标了 `-text -diff`，即刻意保留原字节的冻结树。移动要么改写这些原字节，要么让夹具与账本
变成假话，两条都违反 WUI-17
验收里"保留原字节/哈希"。因此接受标准里的"先迁消费者再移动"这一步今天只做了一半，做法改为**就地标注**：
根目录每份 Markdown 的处置现在登记在 `.project/governance/root-document-dispositions.json`（11 份实测：
`authority=2`、`convention-current=3`、`historical-non-normative=6`——本文上面的"8 份不在权威链里"用的是
"除 AGENTS/README/WORK-LAB-AUTHORITY 之外"的口径，两套分类各自成立，故都保留原措辞），六份历史记录在 H1
下方插入一段可见的 `NON-NORMATIVE-HISTORICAL` 声明（含现行任务包逐字路径），正文其余字节未动；必门
`scripts/ci/verify_root_document_dispositions.py`＋`tests/workflow-assistance/test_root_document_dispositions.py`
（14 例）钉住四件事：新出现在根上的 md 若没人分类即红、权威集合是从机器权威里**解析**出来的而不是抄进清册的
（把 AGENTS.md 降级会红）、声明里指向的任务包必须等于 `.project/governance/project-authority-index.json`
的 `currentTaskpack`（旧指针会红）、以及去掉声明块之后的字节必须逐字节等于提交版本（**改写历史正文会红**）。
该门在真文件上做过两次伪证（删掉一段声明→`UNLABELLED_HISTORICAL`；在正文追加一行→`BODY_REWRITTEN`），
两次都红并逐字节还原（13,210 B / 10,255 B），脚本 `.project-local/runs/falsify_root_dispositions.py`。

## 5. 活文档里仍在引用已退役根（实测 `git grep -c -F`，限 `docs/current` + `taskpacks/current`）

以下都是**已退役根的名字，不是可跟随的路径**，故不加反引号：10-workflow **7**（全仓活 md 口径 17/10 文件）、
00-governance 9、contracts/ 21、scripts/workflow 7、apps/observer/web 8（`git ls-files -- apps/observer/web` = **0**，
即引用一个仓库里已不存在的根）、50-taskpacks 5、30-observer 4、80-evidence 3、docs/handoffs 2、docs/audit/ 1。

这些是**引用腐坏**而不是任务缺失；`scripts/ci/verify_authority_index_paths.py` 只覆盖 `docs/current` 与账本，
`reports/`、`knowledge-staging/`、根目录不在其扫描面内——这是"找不到文档"的第二个来源。

## 6. 从 `D:/All projects/Record` 收回来了什么（2026-10-08）

库总量实测 **15,301,597,876 B / 168 项**，其中 **98.31% 是另一个项目的构建包**。WORK-LAB 相关约 44 MB，
其中 11 文件 / 6.5 MB 与仓库字节相同 → **真正在 Git 根外的唯一副本是 9 个文档（456,606 B）+ 一个
37,048,117 B 的 UI 资料包**。

- 入库位置：`docs/history/archive/recovered-originals/RECORD-20261008/`（提交 `3862499b`）。
- 通道：`scripts/maintenance/recover_shared_root_original.py`，逐件产出 sha256、`flow=ALLOW`、
  `untouched=True`，证据 JSON 在 `.project-local/runs/qoder-20261008-d/recovery/`。
- 提交前 `scripts/audit/tracked_secret_shape_scan.py`：6 处命中，**新目录 0 命中**（6 处是此前已裁定的
  占位符与测试植入假值）。
- **故意不导入**：`WORK-LAB_MASTER_ATLAS_2026-09-29.zip`（`.project-local` 下已存两份，其压缩包内 repo 快照的 111 个
  文件今天全部能解析到受跟踪路径 → 零独有代码）；4 个 taskpack ZIP（成员与受跟踪文件哈希相同）；
  142 MB 三项目共享材料（不是 WORK-LAB 可单独发布的）。
- 待裁定：共享材料是否由本项目代表三项目发布；`C:\Users\ALEX` 出现在 atlas 的 4 个文件里（与 ERR-177
  同类，已在册）。

## 7. 让"下次还找不到"不再发生的四条硬要求

1. **本索引必须被引用**：`README.md` 与 `docs/current/workflow-assistance/workflow/active-authority-index.md` 各加一行指向本文件；
   本文件位于 `docs/current/`，因此受 `scripts/ci/verify_authority_index_paths.py` 约束——写错路径会直接红。
2. **根目录清零**：§4 的 8 个文件（2026-10-10 复点）按"改引用 → 移动 → 同提交复验"处理，根目录最终只留权威与入口文档。
3. **冻结面要被标记**：`knowledge-staging/`（224 文件，2026-09-23）与 `90-archive/` 需一份
   `FROZEN` 声明（现只有 `BOUNDARY.md`）；`taskpacks/history/` 无 README，`docs/history/archive/` 6 个子树
   只有 3 个有——统一补，并采用 `reports/audit-archive/20260930/ARCHIVE-INDEX.json` 那种**逐文件
   path+bytes+sha256** 清单（三套归档约定里只有它做到字节可核对）。
   **已做（2026-10-08，第 3 项的清单部分）**：`knowledge-staging/`、`docs/history/archive/`、
   `reports/audit-archive/` 各得一份 `FROZEN.md` 声明 + `FROZEN-MANIFEST.json` 逐文件清单
   （225 / 137 / 480 条，字段沿用 `ARCHIVE-INDEX.json` 的 `path`/`bytes`/`sha256`，不另立新约定），
   由 `scripts/audit/generate_frozen_surface_manifest.py` 生成、
   `tests/ci/test_frozen_surfaces_are_intact.py` 每次复验并点名增删改；清单不能自摘要所以按名字排除自己，
   该排除也被断言。已在真实文件上注入一次字节改动验证门禁会红（`CHANGED knowledge-staging/BOUNDARY.md
   manifest=0c84bdef6151 now=ce0703307370`），随后按字节还原。
   **`90-archive/` 不配清单**：它只剩 1 个边界标记文件（本文件第 34 行早就这么写），对单文件做逐文件
   哈希清单是仪式而非控制，`BOUNDARY.md` 本身就是冻结声明——我一度以为本文件写错了，核对后是本判断错，
   在此收回。
   **实测更正一处**：`docs/history/archive/` 6 个子树里有 README 的是 **2 个**（`session-history`、
   `superseded-current`），不是 3 个；缺的是 `recovered-originals`、`reports-history`、`scripts-history`、
   `workflow-assistance`。另外该面字节数 38.5 MB（96% 是 2026-10-08 导入的一个 UI 资料原件包），
   我用不带 `-z` 的 `git ls-files` 量到过 1.09 MB——git 会引号化非 ASCII 路径，那些"文件"根本不存在，
   于是被静默跳过；清单类统计一律 `-z` 分割。
4. **活引用要收敛**：§5 的退役根引用逐条改指现路径；把 `reports/`、根目录、`knowledge-staging/` 纳入
   引用门禁扫描面，否则"文档存在但没人能找到"仍会发生。
   **已做（2026-10-08，第 4 项的设计合同部分）**：`apps/observer/frontend/DESIGN.md` 与
   `apps/observer/frontend/SCREEN_SPEC.md` 进 `EXTRA_SURFACES`（受严格面规则），每个面配实测下限（`apps/observer/frontend/DESIGN.md` 25 / 34、
   `apps/observer/frontend/SCREEN_SPEC.md` 8 / 10、register 300 / 393、`docs/current/` 300 / 396），下限的作用是**缩水必须被
   决定一次**，不是装饰。同一轮把提取器补上样式与组件后缀（css/scss/sass/less/vue/svelte）：此前
   `apps/observer/frontend/DESIGN.md` 引用最密的那一列它一条都读不到。实测两个口径都写清楚——原始匹配 837→854，去掉示意名后
   真正被判定的引用 817→833；新增判定里 6 条落在外树或路由上，5 条需要各自的就地声明
   （`apps/observer/frontend/DESIGN.md` 3、`apps/observer/frontend/SCREEN_SPEC.md` 1、register 1），第 6 条被同面已有的目录级声明顺带覆盖。都按所在句
   声明，不改成仓库级静音。引用解析加了"先根、后同目录"两级候选：设计文档里的 `src/…` 写法指的是自己
   旁边的文件（示意名按本仓约定带省略号，才不会被当成一次死链断言——我第一版把示例直接写成反引号路径，
   引用门禁当场把这一句判红，这是它在正常工作）；顺序就是安全性——根形式永远先试，
   原本能在根上解析的名字断了仍报 broken。新增 8 条断言（`tests/ci/test_authority_index_paths_resolve`
   由 28 例到 36 例全绿），5 个关键特性各做一次"把实现拿掉必须变红"的反证。反证脚本的第一版是**假通过**：
   加载器名写错，五条全部在到达断言之前就报错，而判据只看"有失败或错误"，于是统一打印 CAUGHT。
   认出它的特征是五条形状完全一致（`errors=1 failures=0`，真实断言失败应是 `failures=1 errors=0`）；
   修正判据为"必须是 failures 且 errors=0"并重跑，才是真的 5/5。
   **未做（第 4 项剩余部分，含明确理由）**：`reports/`、`knowledge-staging/`、根目录**没有**并入扫描面。
   开闸前先量代价（2026-10-09 复量，口径：这三面全部受跟踪 md，用同一条规则逐面 `check()`）——
   397 个有引用的面、4,153 条引用里 **3,262 条断链**。naive 并入就是把这些一次倒进队列，那是负担不是控制。
   按文档来源拆开看才有办法：
   外购技能副本（`knowledge-staging/asset-provenance/` 下的，与任何名为 SKILL.md 或路径含 /skills/ 段的文件）559 面 /
   3,327 引用 / **2,871** 断——这些句子讲的是它们自己上游仓库，本来就不是本仓的导航面；
   本仓日期化归档（`reports/audit-archive/`，非技能副本）70 面 / 329 引用 / **243** 断——改了会让带日期的
   记录说假话，与第 3 项冻结清单冲突；
   当下仍在写的（根目录 9 面与归档外的 reports）33 面 / 497 引用 / **148** 断——只有这一档是真正的活引用腐坏。
   所以并入不是一份 3,262 行的基线，而是三种策略各一条：副本子树按**面**声明为"非本仓导航面"（并让测试盯住该
   声明仍然成立），日期归档用**棘轮**（条数不得增长、基线里每条今天仍须断，修好一条就同提交重发基线），
   当下在写的 148 条**逐条清**。追正一句：本轮早先我写过 naive 代价是 **3,492**，那是更宽口径下的旧数，
   以本次复量的 3,262（口径如上）为准。登记为账本行 `REFS-RATCHET-HISTORY-SURFACES-20261009`，不是静默丢弃。

## 8. 未测 / 不确定（不假装）

- `.project-local/` 内未被跟踪的 md 数量：未测（该根整体被忽略，需要单独枚举才能给数）。
- `apps/observer/docs/` 的 md 字节数：未测。
- 账本行数 163 与 183 的差集逐条归因：未做，只给了两种口径与差异来源假设（无优先级单元格 / 续行）。

## 9. 2026-10-10 复测更正（WUI-17：默认加载链的引用可追溯性）

- **本文件自身四组数字已过期，现按逐名点数复值**：`docs/current/*.md` = **43**（原写 38）；仓库根受跟踪 md =
  **11**，其中不在权威链里的 = **8**（11 − AGENTS/README/WORK-LAB-AUTHORITY 三份，原写 10），合计 **105.9 KB**
  （原写约 127 KB）；§3 标题的"自称任务清单"逐名点数为 **9** 份（原写 10，差异就在被合并进同一表格单元格的 5 项
  只计了一次标题行）；§7.3 之后三处冻结面已共用同一 `FROZEN.md` + `FROZEN-MANIFEST.json` 约定，
  所以"三套归档约定"今天是**一套约定、三处实例**——本文其余段落保留当时的措辞，因为那是那天的事实。
- **默认加载链的引用已机械化正规化**：`scripts/audit/normalise_doc_citations.py` 把权威引导链 8 份文档中的
  201 条反引号路径引用里的 **56 条**改写为仓库根相对真路径（裸文件名与相对前端的 `src/...` 形状），
  对 14 个"类指/非本仓"引用（`SKILL.md`、`FROZEN.md`、`BOUNDARY.md`、`config.yaml`＝Hermes Home live、
  `tauri.conf.json` 两应用各一份、包内 `design_tokens.json`/`ui_read_model.ts` 等）改为**带理由的显式声明**，
  并要求每条声明仍被实际使用（不再需要的声明会让复验变红，避免许可腐化）。历史副本
  （`taskpacks/history/`、`docs/history/`、`reports/audit-archive/`）不参与"按文件名猜路径"，
  因此 `project-authority-index.json` 这类同名不会再被指向 2026-10-09 冻结树。
- **必门**：`tests/workflow-assistance/test_default_load_doc_citations_resolve.py`（5 例）钉住范围文件在盘、
  引用零不可解析、扫描数 ≥150（防止正则失明）、许可全部仍在用，并用合成断言证明解析器确实会判
  "不存在的路径"为不可解析、会把相对简写改回真路径、且不会把简写建议成历史冻结副本。
- **仍属未做**（保持原样，不假装完成）：上列"未做"三条今天仍未做；`reports/`、`knowledge-staging/`、根目录
  也还没并入引用扫描面（§5 第 4 项）。WUI-17 本轮只处理"仍影响默认加载"的消费者。
- **同日稍后更正上一条**：上一条写"正是这 8 份文档"是**错的**——`auditBootstrap` 第 6 步就是活账本
  `taskpacks/current/OPEN-TASK-REGISTER.md`，而它不在作用面里；把它加进去（8→9 份）之后当场量出
  **374 条引用、80 处从根目录打不开的简写形状、9 条完全解析不了**（7 个裸证据回执名 + 2 条"引用它就是为了说它错"的路径）。
  同轮还修了作用面本身的口径缺陷：`working_tree()` 原先按手写的 `SOURCE_DIRS` 十一根目录走盘，量得 2,474 个路径，
  里面**没有**受跟踪且被 WUI-16 引用的 `projections/agents/generate.py`，于是一条诚实引用被判为不可解析；
  改为 `git ls-files` ∪ 全仓走盘（排除 `.project-local`，运行时副本不得决定一个裸名的含义），量得 **2,700**。
  走盘一放宽又立刻出现**相反**缺陷：`.ui-reference/WORK-LAB/**` 里另有一套与本仓同名的前端文件（对应本仓
  `apps/observer/frontend/src/types.ts` 与 `apps/observer/frontend/src/lib/navigation.ts`），
  两条正确引用改判"歧义"——处理方式是把冻结树与外购参考副本从**裸名索引**里排除（`NOT_INDEXED_PREFIXES`），
  显式路径照旧可引。两条被判错的错误路径改由 `QUOTED_AS_ABSENT`（按整条引用而非文件名匹配、逐条带理由、
  **必须仍在被使用否则复验变红**）豁免；七个裸回执名改为逐字运行时路径（7 处替换、写后按字节复核）。
  最终态：`DOC_CITATIONS CHECKED docs=9 citations=365 rewritten=0 blocked=0 generic_allowed=14 absent_quoted=2 stale_allowances=0`，
  门增至 **8 例**（新增：账本必须在作用面内、受跟踪文件与目录无关地可见、外购副本不作裸名含义），
  且三条都用**改工具本体**的方式伪证过（去掉参考副本排除→该例红 failures=1；把走盘限制到单个根→红 failures=2；
  两次工具均按字节还原、还原后 8/8 绿，`.project-local/runs/falsify_citation_cases.py`）。教训登记 ERR-242。
- **根目录处置已成机器合同**（§4 末）：清册 `.project/governance/root-document-dispositions.json` 实测
  11 份 = `authority=2 / convention-current=3 / historical-non-normative=6`；门
  `scripts/ci/verify_root_document_dispositions.py` 输出 `ROOT_DISPOSITIONS_PASS root_md=11 authority=2
  convention=3 historical=6`，必门 `tests/workflow-assistance/test_root_document_dispositions.py` **14 例全绿**
  （含 6 条合成伪证 + 2 条真文件伪证：删声明→`UNLABELLED_HISTORICAL`、追加正文→`BODY_REWRITTEN`，
  均逐字节还原 13,210 B / 10,255 B）。六份历史文件各 +481 B，正文与提交字节逐字节相同由门复核。
- **同日第三轮：两表引用形状与"改完又被整表覆掉"的收据问题**。绑定矩阵与验收清单自身的必门
  `tests/workflow-assistance/test_ui_v2_csv_citations_resolve.py` 本轮两次判红，量出的形状是：233 条引用里
  **58 条只有 basename**、**6 条写了不存在的目录**、**1 条指从未存在的文件**；而指针内容检查"打不开就跳过"，
  于是 144 条带行号引用只有 **106** 条被真正读过（普查地板 `POINTER_FLOOR=140` 因此判红——地板不是被下调的，
  是被路径修复满足的）。修法是**改数据不是改门**：`.project-local/runs/wui-20261010/expand_shorthand_citations.py`
  的替换表取自门自己的扫描（所以正文里类指的文件名不会被机械改写），裸名必须在树中**唯一**才落笔，
  写错目录的六条还要求**候选文件里确实命中被引代码**才采用；B34 的死人路径改为具名 `ABSENT:` 并指向
  `apps/observer/frontend/src/lib/ruleProjectionTruth.ts:34`。路径一通即暴露 **8 条行号漂移**（±1～4 行），
  由 `.project-local/runs/wui-20261010/repoint_convicted_pointers.py` 只搬"门点名"的指针、只落在 30 行内唯一命中处，写后用门的谓词复跑：
  `BEFORE checked= 144 problems= 8` → `AFTER checked= 144 problems= 0`；最终 `resolves=223 / runtime=10 /
  declared_absent=1 / 未解析 0`。
- **两条早先修复在出厂字节里找不到**（WUI-23 段登记的 `CITATION_NORMALISE APPLIED rewritten=58` 与上一段登记的
  7 条指针改正，重读文件时都回到了修前状态）：链式脚本里**最后一个写者**拿的是自己早先载入的整表副本，
  而每个写者都只在"自己写完"后复读过。此后规则写进 ERR-248：一批写入链的末尾必须重读出厂文件、复跑判决，
  并把读回的 SHA 写进登记（矩阵 `13ece1b83c2c24be` → `17a89217d7ad509b` → **`4c39aff8677b48c3`**，
  清单 **`6c93e1bb4a51ec30`**）。同轮我自己的第二缺陷：把含逗号的句子原文替换进**未加引号**的 CSV 字段，
  B34 由 14 列变 15 列，而 `csv.DictReader` 把多余字段挂在 `None` 键下、门只断言表头与行数因而**看不见**；
  门已加**逐行字段数**断言并伪证（对照 exit 0 → 种入多一列 exit 1 且命名 `('B34', 15)` → 按字节还原 exit 0）。
- **文档引用面随之调整**（同一类问题的另一面）：账本新段要原样写出六条坏路径才能记录"这里曾经写错"，
  而 `scripts/audit/normalise_doc_citations.py` 的 basename 兜底会把它们"改好"——那等于把判决从文档里抹掉。故六条按**整条
  引用**加入 `QUOTED_AS_ABSENT`（理由逐条写明是 ERR-247 更正记录），类指的 `package.json` 加入
  `GENERIC_CITATIONS`；新增必门例 `test_a_quoted_wrong_path_is_only_safe_because_of_its_allowance`
  证明这些豁免是**承重**的（撤掉一条，工具立刻报 `rewritten=1` 即会把更正记录改写）。最终态
  `DOC_CITATIONS CHECKED docs=9 citations=436 rewritten=0 blocked=0 generic_allowed=16 absent_quoted=8 stale_allowances=0`，
  该门 8→**9 例**、两表门 **7 例**全绿。教训登记 ERR-247（假出处与失明普查）、ERR-248（写入秩序与表形状）。
- `WORK-LAB_UI开发资料总包_按批次.zip` 内 12 个内层 ZIP 的逐成员清单：未展开（导入的是字节原件）。
