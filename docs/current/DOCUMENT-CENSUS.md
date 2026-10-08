# 文档与任务总索引（DOCUMENT CENSUS）

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
| `docs/current/` | 38 md | 2026-10-08 | 当前工作文档 | 是（受引用门禁） |
| `docs/decisions/` | 18 | 2026-10-07 | ADR、`global-execution-standard.md`、`instruction-precedence.md` | 是 |
| `docs/future/` | 3 | 2026-10-08 | 蓝图与覆盖投影（含生成物） | 计划 |
| `taskpacks/history/` | 81 | 2026-10-08 | 冻结历史 | **非规范** |
| `docs/history/` | 115 md | 2026-10-08 | 冻结历史 + `docs/history/archive/` + `docs/history/archive/recovered-originals/` | **非规范** |
| `reports/` | 527 | 2026-10-06 | 审计证据（`reports/audit-archive/` 479、`reports/audit-evidence/` 34） | 证据 |
| `knowledge-staging/` | 224 | **2026-09-23** | 边界标记为 `HISTORY_ONLY_CONVERGE`，非活动模块 | 冻结候选 |
| `90-archive/` | 1 | **2026-09-24** | 只剩边界标记文件；内容 2026-09-23 已并入 `docs/history/` | 冻结候选 |
| 仓库根 `*.md` | 11 | 混合 | **10 个不在权威链里**（见 §4） | 混杂 |

## 3. "自称是任务清单"的东西有 10 份，只有一份是账本

实测口径：`grep -cE '^\| [A-Za-z0-9._-]+ \| P[0-9]' taskpacks/current/OPEN-TASK-REGISTER.md` = **163 行**
带优先级的在册任务行（另一口径按"表头行"数到 183，差异来自无优先级单元格与续行；两个数都写出来，
避免下次又为"到底多少条"吵架）。

| 声称者 | 处置 |
| --- | --- |
| `taskpacks/current/OPEN-TASK-REGISTER.md` | **唯一账本** |
| `WORK-LAB-AUTHORITY.md` §14（18 条"当前未决"） | 权威摘要，条目须与账本一致；不一致时以账本行 + 机器合同为准 |
| `docs/future/WORK-LAB-BLUEPRINT-COVERAGE.md` | **生成物，禁手改**；实测 22 个 U 行里 **19 行读 `UNVERIFIED`** 而账本读 `IMPLEMENTED@…`/`CLOSED_LOCAL` → 词汇过期不是新事实，由 `verify_blueprint_coverage.py --write` 重生成 |
| `README.md`、`taskpacks/current/README.md`、`docs/decisions/PROJECT_POSITIONING.md`、`docs/audits/BLUEPRINT_SYNC_AUDIT_2026-10-06.md`、`taskpacks/current/WORK-LAB-UNIFIED-…-20260918.md` | 描述/投影，不得当账本读 |
| `taskpacks/history/OPEN-TASK-REGISTER-20260917.md` | 冻结孪生，非规范 |

## 4. 仓库根目录是真正的踩坑点

根上有 **10 个不在权威链里的 md（约 127 KB）**，其中两份**看起来像活任务**：

- `HANDOFF-UI-L10B.md`（12,588 B）开头即 `⛔ CLOSED — DO NOT RE-EXECUTE`，但放在根目录，新会话按文件名读就会误接；
- `UI_IMPLEMENTATION_REPORT.md`（54,649 B，2026-10-08）与 `reports/UI-CHECK-OBSERVER-20261006.md` 角色重复。

**处置（本索引提出，未擅自执行）**：`git mv` 进 `docs/history/archive/` 是规范动作，但这些路径被
`README.md`、账本行与 `active-authority-index.md` 引用，移动会同时打红引用门禁。因此要求：**先改引用、
再移动、同一提交内完成**，并让 `verify_authority_index_paths.py` 当场复验。逐个移动的清单见 §7。

## 5. 活文档里仍在引用已退役根（实测 `git grep -c -F`，限 `docs/current` + `taskpacks/current`）

以下都是**已退役根的名字，不是可跟随的路径**，故不加反引号：10-workflow **7**（全仓活 md 口径 17/10 文件）、
00-governance 9、contracts/ 21、scripts/workflow 7、apps/observer/web 8（`git ls-files -- apps/observer/web` = **0**，
即引用一个仓库里已不存在的根）、50-taskpacks 5、30-observer 4、80-evidence 3、docs/handoffs 2、docs/audit/ 1。

这些是**引用腐坏**而不是任务缺失；`verify_authority_index_paths.py` 只覆盖 `docs/current` 与账本，
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

1. **本索引必须被引用**：`README.md` 与 `active-authority-index.md` 各加一行指向本文件；
   本文件位于 `docs/current/`，因此受 `verify_authority_index_paths.py` 约束——写错路径会直接红。
2. **根目录清零**：§4 的 10 个文件按"改引用 → 移动 → 同提交复验"处理，根目录最终只留权威与入口文档。
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
   `SCREEN_SPEC.md` 进 `EXTRA_SURFACES`（受严格面规则），每个面配实测下限（`DESIGN.md` 25 / 34、
   `SCREEN_SPEC.md` 8 / 10、register 300 / 393、`docs/current/` 300 / 396），下限的作用是**缩水必须被
   决定一次**，不是装饰。同一轮把提取器补上样式与组件后缀（css/scss/sass/less/vue/svelte）：此前
   `DESIGN.md` 引用最密的那一列它一条都读不到。实测两个口径都写清楚——原始匹配 837→854，去掉示意名后
   真正被判定的引用 817→833；新增判定里 6 条落在外树或路由上，5 条需要各自的就地声明
   （`DESIGN.md` 3、`SCREEN_SPEC.md` 1、register 1），第 6 条被同面已有的目录级声明顺带覆盖。都按所在句
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
- `WORK-LAB_UI开发资料总包_按批次.zip` 内 12 个内层 ZIP 的逐成员清单：未展开（导入的是字节原件）。
