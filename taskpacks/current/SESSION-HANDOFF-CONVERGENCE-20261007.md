# SESSION-HANDOFF-CONVERGENCE-20261007

> 只读交接记录，不授予任何权限。分支 `task-decomposition/atlas-gap-archive-20261001`（PR #162，
> `mergeable=MERGEABLE`），交接时刻本机头 `1276547`，`main` 仍为 `cd4daa8`（本轮未合并、未打 tag、未发布）。
> 上一份交接：`taskpacks/current/SESSION-HANDOFF-CONVERGENCE-20261006-B.md`。

## 0. 一句话

**UI 桌面唯一化已由 runner 侧证明，五个客户端版本改为"有日期的本机观测"，模型库回读变成仓库可见证据；
剩余未闭合项全部是 owner 决定类或真人操作类，没有被伪装成进度。**

## 1. 本轮已落地（全部已提交并推送）

| SHA | 内容 | 关键证据 |
|---|---|---|
| `8a5b445` | U02 未认领的一半：`toolchain-declarations.json` + 8 项门禁 | 5 个 lockfile 逐条对树；node/rust 保持 null + `OPEN_RECORDED` |
| `5037dd2` | 重测清单与引用审计 | CI 两条 workflow **全绿**（`gh run list` 读回，5037dd2 上 work-lab-gate 与 wlr-060 各 2 run completed/success） |
| `1ece4af` | ERR-149/150/151 盖印于 `17eb5b6` | `stamp_record_verification` 要求每条 workflow 都 completed/success |
| `bbb79c2` | 候选池吸收语义 + 边界内残留判定 | 见 §2.5 |
| `7375234` | 批量盖印 12 条 + **拒绝** 3 条 | ERR-085 非祖先、ERR-113/127 声明"刻意不接 CI" |
| `7eb8ab4` | 模型库回读收据入仓 + UI 报告 §13 | `docs/audits/MODEL_LIBRARY_READBACK_2026-10-07.json`（blob 摘要见在册行） |
| `25e58c2` | ERR-152 修复：负控制改用 `--ledger` 夹具 | 4 项新控制 + 1 项"忽略 --ledger 就露馅"的检查 |
| `5ee34f9` | ERR-152 入账 + 两处状态精确化 | CI **全绿**（`gh run watch --exit-status` 返回 0；PR 检查面 workflow-assistance=SUCCESS） |
| `8847cdc` | `tool_version_metadata_probe.py`：不启动进程取版本 | 收据 `docs/audits/TOOL_VERSION_METADATA_PROBE_2026-10-07.json`；**CI 两条 workflow 全绿** |
| `1276547` | 五个适配器版本按 AG-07 既有字段入账 + 交叉门禁 | 门禁 8 项、反证 7/7 转红；`QUALITY_GATE_PASS gates=adapter-registry`；**CI 两条 workflow 全绿** |
| `15ed970` | 本轮交接记录 | **CI 两条 workflow 全绿** |
| `ad441a3` | 未绑定台账债务分诊入仓（95→RESOLVES 37 / 无文件操作数 42 / 路径已消失 15 / 仓外 1） | 门禁 7 项 + 反证 5/5；债务数为派生量；**CI 两条 workflow 全绿** |
| `737dac2` | **ERR-123 绑定到真实修复 `763a77f`** 并盖 verifiedCommit=`8847cdc`；分诊加"出生提交"信号后得出硬结论：94 条里 **86 条出生在 cutover 导入提交 `6bd0bd5`**，本仓历史可证的可绑定候选 = **0** | `bound=39 unboundPass=94 anomalies=0`；`test_ledger_fix_commit_binding` 10 项通过；反证增至 6 例（含"把导入出生的行说成可绑定"）全转红。**该头 CI 红**：清单摘要取错 git 对象（ERR-153），修在 `4303bf8` |
| `11042dd` | 几何门禁的 runner 实测读数入档 + 修掉一条误导性 PASS 文案 | 见 §2.7；该文件与 `test_desktop_only_shell.py` 合跑 25 项通过。**该头 CI 红**（同一 ERR-153 因） |
| `95c62a4` | 15 条 PATH_GONE 拆成 6 真丢失 / 3 部分丢失 / 6 非路径 token；新仪器 `adjudicate_gone_guards.py` + 门禁 7 项 + 反证 4/4 | **CI 两条 workflow 全绿**（修复后首个完整读回的头） |
| `4303bf8`+`2f818e7` | **ERR-153**：清单摘要改从**索引**取（要发布的那个对象）；旧 PASS 重跑收据 23 PASS / 7 FAIL（全为"命令已不能按原文执行"）/ 6 REFUSED，**今天真失败的不变量 = 0**；新仪器 `rerun_unbound_pass_checks.py` + 门禁 6 项 | `ERROR_LEDGER_PASS entries=151`、binding 门 10 项、52 项派生门全通过；`2f818e7` CI 于写作时在跑 |

## 2. 已确立的事实（不要重复论证）

1. **UI 桌面唯一化是 runner 证明的，不是本地推断**：`17eb5b6` 的 observer 作业内
   `Build the real Tauri desktop binary (MSVC)`、`U19 real-WebView E2E readback`、
   `Desktop geometry gate (CDP measurement of the built shell)` 三步均 `success`。UI 码经
   `85545b3` 并入收敛线，且实测 `85545b3` 是全绿头 `5037dd2` 的祖先。
2. **版本观测的正确容器早已存在**：`provenance.version_readback`（observed_at/verified_version/method）
   是 AG-07 设计的字段，`version` 只允许承载原生回读值。本轮 codex 0.160.1、github 2.98.0 (2026-08-20)、
   cc-switch 3.20.0、openhuman 0.63.12、open-design 0.24.1 全部按此入账；
   `detection.evidence_state`、`support_level`、`hash` 未动（版本不是包哈希）。
3. **不启动进程也能拿到版本**：读可执行文件自带的版本资源。三个此前被判 `ENTRY_NOT_RESOLVED` 的桌面客户端
   其实都装着（只是没有 .lnk）。hermes 的 CLI 启动器**没有版本资源**、codex 是 `.cmd` 包装器——两者保持未知/
   归属 live probe，不得用文件摘要冒充。
4. **模型库真相**：10 行中 7 行整文件重算相符（24,668,004,626 B），2 行按 ollama 内容地址相符，
   0 行与注册表矛盾；1 行注册表本就无摘要，故只给目录存在性。**两条内容地址行的 `bytes_observed`
   都是 29,751,357,111 = 整个 blob 存储体量而非单模型**——该数不得被任何记录引用（ERR-113 同型仪器缺陷）。
5. **吸收语义**：候选池 22 行里 0 行 PROMOTED；`POC_IN_REPO`/`ADAPTER_IN_FLEET` 是本地重写、
   `CONSTRAINT_IN_CODE` 是规则本地化，门禁查路径存在与标签一致、查不了来源。旧 absorption 文档的
   13 条"已吸收"落点全部存在（按模块根 `packages/client-neutral-core/` 与收敛后 docs 路径解析）。
6. **台账现况**：150 行 / 41 行有 fixedCommit / 38 行已盖 verifiedCommit / 3 行故意不盖 / 109 行无修复；
   `ERROR_LEDGER_PASS counts_consistent=true`，`bound=38 unboundPass=95 anomalies=0`。后续 ERR-123 绑定并盖印后
   更新为 **bound=39 / unboundPass=94**（见 §1 的 `737dac2` 行），旧数保留以显示移动方向。
7. **几何门禁给出的是数字不是口号**（run `37585453264`、head `8847cdc`、observer 第 12 步 success）：桌面档
   `scrollWidth=1264 innerWidth=1264`、顶栏 `height=129/limit=140`、导轨 `rail=214.9/min=200`、`left=0`、
   `gap=731.1`、`brand=91`；紧凑档 `500x629`、`height=111/limit=260`、`rail=None`，结尾 `GEOMETRY_GATE_PASS`。
   **但它不证明面板窗等于声明的 440×780**（实测视口与 tauri.conf.json 不一致，窗框/缩放未量化），也不证明
   临时 user-data 目录被删干净（同跑报出 2 个 PermissionError 残留，一次性 runner 上仍判过，名字被打印出来）。
   同一次运行还暴露我自己的一条误导文案：`topbar_measured PASS no .topbar element` 的详情字符串是写死失败文案，
   元素其实测到；已改为通过时报实测高度、缺元素时报 MISSING 并失败。

## 3. 本轮撤回与自我纠错（照登，不改口径）

1. **UI 报告 §12"几何门禁仍未接入 CI 必需步骤"已被 §13 取代**：那是接线前写的，现为必需步骤且有 runner 读数。
2. **一次性吸收探针报"14 条已吸收落点 ABSENT"是探针错**：它按仓库根解析模块根相对路径。语料没错，文档一字未改。
3. **github 版本我先写 `2.98.0`**：新门禁当场拒绝（收据里是 `2.98.0 (2026-08-20)`）。改的是我的声明，不是门禁。
4. **ERR-152 是我自己造成的红**：两个"必须拒绝"的负控制拿在册台账当输入，合法盖章后它们再也无法失败，
   `1ece4af/bbb79c2/7375234/7eb8ab4` 四个头因此红；我只跑了子集、没重跑那个被改了输入的文件。
5. **本地整轮复现曾出现 governance `errors=1`**，消息指向一个未被跟踪的本机残留目录（其中任务包目录名重复
   了一层），同头裸跑 2130 项全过；我按"本机竞态"记录且**未据此报 PASS**，最终仍以 exact-SHA 读数为准。
   这一条仍未彻底解释，保持挂账。
6. **"14 条可绑定"是我自己工具的假象**：加入"出生提交"信号后初看得 14 条候选，逐条核查发现 13 条出生在同一次
   cutover 导入提交（一次搬进整批 2026-08 记录），导入提交不是修复提交；加上"相对父提交最多新增 1 条"的判据后
   归零。结论入档而不是悄悄改掉前一个数。
7. **有一条本地测试常红，但不是本分支的缺陷**：`tests/ci/test_exact_tree_review.py` 断言 HEAD==origin/main 且
   在册任务全 COMPLETED——那是**合并之后**才成立的交付不变量，且没有 CI 作业调用它。我没有为了让分支好看去
   改它；要么由 owner 把它移到合并后检查，要么保持"未合并即红"这一诚实信号。
8. **三个头是红的，原因已定位并修复**：`737dac2`、`11042dd`、`7595adb` 的 work-lab-gate 都败在同一门
   `test_the_shipped_inventory_describes_the_tree`（清单摘要记的是**上一个提交**的字节：`tool_inventory_readback.py`
   原来"HEAD 优先、否则工作树"，对已跟踪文件的修改就取错对象）。三个红因逐个从各自 runner 日志确认为同一类，
   修复在 `4303bf8`（摘要改取索引 `git show :path`）；修复后的头 `95c62a4` **两条 workflow 全绿**（实测读回），
   `2f818e7` 在跑。教训是"暂存→重测→提交"这条纪律本身没错，错在测量取错了 git 对象——**要被发布的那个**。

## 4. 需要 owner 或真人操作（明确挂账，不得代答）

- **U02 发布半段**：Hermes Home 有一条未审阅技能，部署被门禁挡住。
- **U03 `web/` 退役**、**U19 release 二进制重建/发布**（无 tag、无发布已执行）。
- **OD02/OD03/OD04**（AG-12/13/17/18 决策项）；**AG-09/AG-10** 需真实项目 + 第二个真实执行器 + 真实消费者；
  **AG-16** END-TO-END 同上。
- **模型入库缺口**：`registry.ollama.ai/library/qwen2.5vl/7b` 5,969,233,408 B 在库而无注册行。
- **许可判断**：mcp-inspector 与本仓库许可属 owner/法务问题（见候选池与 source-licence 记录）。

## 5. 下一份工作的优先顺序

1. **94 条未绑定 PASS 的正确处理方式已被本轮实测限定**：86 条出生在导入提交，本仓历史给不出修复 SHA，
   所以只有两条诚实路径——(a) 逐条**今天重跑**它自己的回归命令以重建证据：**这条已在 2026-10-07 做完**
   （36 条可解析命令 → 23 PASS / 7 "命令已不能按原文执行" / 6 REFUSED，**今天真失败的不变量 0 条**，
   见 `docs/audits/LEDGER_UNBOUND_RERUN_2026-10-07.json`；剩下 58 条要么无文件操作数要么守卫已消失）；
   (b) 回到被合并前的分支历史（`6bd0bd5` 的父链之外）去取真实因果。**不得**用邻近提交冒充 fixedCommit。
   15 条 PATH_GONE 已进一步拆开（`docs/audits/LEDGER_GONE_GUARD_ADJUDICATION_2026-10-07.json`）：6 条真的失去文件守卫且无后继、3 条只是多操作数命令部分丢失、6 条根本没有丢失文件（上游匹配器把 URL/分数/标识对/裸目录当路径）。
   其中 **ERR-104 的"守卫"位于被忽略根目录**——干净检出永远看不到它，这类 PASS 从未可验证，不是"测试消失"，需单独处置。
2. `model_library_readback.py` 的字节数缺陷（两条内容地址行报的是整个 blob 存储 29,751,357,111 B 而非单模型）；
   改前先写反证，改后重生成 `docs/audits/MODEL_LIBRARY_READBACK_2026-10-07.json`。
3. 观测老化：`test_adapter_version_readback` 已把"声明↔收据"钉住，下一步是让版本收据周期性重生成，
   并给 hermes 找到不需要启动的版本来源（它的 CLI 无版本资源）。
4. `qwen2.5vl/7b` 权重在库未登记（5,969,233,408 B）、`30-products/minigame` 等已消失守卫的归属，
   都属需要 owner 点头的入库/撤账动作。
5. PR #162 合并与发布决定权在 owner；本轮未合并、未打 tag、未发布。合并预演在交接时**重跑过一次**：对
   `origin/main` 的 `git merge-tree` 干净无冲突，合并态台账 151 行（ERR-001…ERR-153）、候选池 22 行，两者均无重复 id。
