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
| 移动会被谁拦 | `scripts/ci/verify_authority_index_paths.py` 默认扫 `docs/current/*.md`（实测 38 个）∪ 唯一 register；4 个导航面（`NAVIGATION_SURFACES`）refs=0 即 FAIL；解析只对着 `git ls-files` |

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
4. **活引用要收敛**：§5 的退役根引用逐条改指现路径；把 `reports/`、根目录、`knowledge-staging/` 纳入
   引用门禁扫描面，否则"文档存在但没人能找到"仍会发生。

## 8. 未测 / 不确定（不假装）

- `.project-local/` 内未被跟踪的 md 数量：未测（该根整体被忽略，需要单独枚举才能给数）。
- `apps/observer/docs/` 的 md 字节数：未测。
- 账本行数 163 与 183 的差集逐条归因：未做，只给了两种口径与差异来源假设（无优先级单元格 / 续行）。
- `WORK-LAB_UI开发资料总包_按批次.zip` 内 12 个内层 ZIP 的逐成员清单：未展开（导入的是字节原件）。
