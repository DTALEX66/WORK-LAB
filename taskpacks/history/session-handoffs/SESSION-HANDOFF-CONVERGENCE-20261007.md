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


## 6. L 轮（同日续做）：Source Registry 升进受版本控制的树

### 6.1 已落地（全部已提交并推送）

| SHA | 内容 | 关键证据 |
|---|---|---|
| `cab412a` | atlas 主 Source Registry 从**本项目自己的忽略根**升进树内；新增升迁工具与其门禁；纠正两条行的 status | `PROMOTED bytes=446119 sha256=79bf958a6e928952… blobIdentical=True`；`test_promote_ignored_root_original.py` 8/8 |
| `999c668` | ERR-154/155 落账；"半升迁标签"变成双向违法；AG-19 钉扫描改读受版本控制的副本 | 证伪 3/3（注入后注册表逐字节复原）；`pinSource=tracked-promoted-copy` |

精确 SHA 读回（`gh run list` 逐头读，不从包装退出码推断）：

- `a382366`：`work-lab-gate` completed **success**、`wlr-060-production-gates` completed **success**（两条 gate 运行都绿）。
- `96d06f4`：`work-lab-gate` completed **success**、`wlr-060-production-gates` completed **success**。
- `999c668`：本轮推送头，读回时仍在跑——**在其变绿之前不得写进 verifiedCommit，也不得对外称绿**。

### 6.2 新确立的事实

1. **AG-19 的权威记录现在 CI 能哈希了。** `.project/governance/recovered-source-registry.json` 的 tracked 行由 7 增至 9；`src-atlas-master-source-registry` 的钉 `79bf958a…` 就是树内 blob 的摘要（`*.json text eol=lf` 且源文件本就是纯 LF，所以工作树＝索引＝blob，没有 ERR-125 的空隙）。
2. **它不是原始导出。** 文档内的 `recoveryAmendment` 记录了 2026-10-07 由 `ag19_register.py` 就地修订；修订前的基线 `439,365 B / 4281e4818890…` 只登记为 `preAmendmentBaseline` 事实，字节仍只在 `.project-local/artifacts/ag19-registry-backup-20261007/`。重建 atlas 必须重放修订，否则钉退回 `BLOCKED_NOT_VISIBLE`。
3. **升迁的判定性质是"干净检出看不见"，不是我猜的三个 role root。** 数据边界只声明 `runtimeRoot/taskArtifactsRoot/canonicalEvidenceRoot`，而 atlas 落在这三者之外的 `.project-local/atlas-2026-09-29/`；屏幕改用 `git check-ignore -v`，并同时要求"在 Git 根内"。
4. **内容安全性是量出来的，不是想当然：** 解析后按键名走一遍——5,608 个字符串、0 个 session UUID、0 个 secret 形键名／prompt-body 形字段／credential 形值／E: 或 F: 路径，最长串 395 字符是关于缺 sha 钉的散文；绝对路径只有 2 处，都指向 owner 素材根的文件名。**绝不晋升**的两件：`src-worklab-summary-2026-09`（含 session UUID 与 prompt body，AGENTS.md 禁止）、`src-history-source-manifest-r4`（派生扫描收据，留在忽略根）。
5. **台账 153 行**（`ERROR_LEDGER_PASS entries=153 classifications=13 counts_consistent=true`），ERR-154/155 的 fixedCommit 绑定前先跑过四条守卫：是提交、含两条承诺路径、动了记录自己点名的路径、相对父提交新增 0 条记录；introducedCommit 由 `git log -S` 量得（`50f77d1`、`950ce65`），不是回忆。

### 6.3 L 轮撤回

- 升迁工具的**第一版屏幕写错**：要求源必须在三个 role root 之一内，会把这次合法晋升直接拒掉。落盘前自测发现的，未提交——但形状要登：判定"CI 看不见"要用仓库自己的忽略规则，不能拿声明的角色根当全集。
- 台账 §5 的"选项 (a) 今天重跑以重建证据"**不足以解锁 verifiedCommit**：`stamp_record_verification.py` 要求 fixedCommit 是该头的祖先，而 86 条导入出生的记录本仓历史给不出 fixedCommit。重跑只能把"今天仍然通过"留在 `LEDGER_UNBOUND_RERUN_2026-10-07.json` 里当补偿证据，不能写进 lifecycle 字段。**不要**为了让计数下降而给它们配邻近提交。

### 6.4 下一件事

1. `999c668` 变绿后：`python scripts/audit/stamp_record_verification.py ERR-154 999c668` 与 ERR-155，然后重测 `ledger_binding_readback.py` 与 `LEDGER_FIX_COMMIT_BINDING` 快照。
2. `test_location_claims_agree_with_the_row_status` 只管**字段级**位置声明；prose 里提到的受版本控制路径仍不受管。若要收紧，先量误报率（多条行的 notes 合法地提到树内文件）。
3. 观测老化项未变：harness 版本收据周期性重生成、hermes 版本来源；`qwen2.5vl/7b` 入库、U02 发布半、U03 `web/` 退役、OD02/03/04、AG-09/AG-10/AG-16 仍属 owner 或真实第二执行人类。

### 6.5 L 轮续做（同一交接内的后半段）

| SHA | 内容 |
|---|---|
| `0941e12` | record: round L handoff, including the limit that stops the unbound-record debt from being "fixed" |
| `8192e08` | record: ERR-154's prose boundary is now a measurement, not an open question |
| `1c3d170` | gate: the mirror registry and the atlas are now checked against each other |
| `dcabd71` | record: the lane-by-lane honest-state matrix, measured, and a claim retracted |
| `9e13d80` | test(ui): every lane must tell the transport truth it was handed |
| `2c0afe5` | record: re-measure the derived audits after the two new frontend files |
| `cf94322` | record: the lane transport matrix, and the three false failures the measurement stopped |

新增事实（不需要再论证）：

1. **镜像注册表与 atlas 现在互查**（`test_recovered_source_registry.py` 增至 14 例）。可核的口径是
   「两条受版本控制的记录是否讲同一件事」，不是「本机文件是否存在」：atlas 的 5 条钉要么声明 RECOVERED 且其
   `expected_sha256` **确实**在 642 sources 里，要么声明 NOT_RECOVERED/NOT_FOUND 且自带 ≥120 字符的负证明；
   镜像行的摘要必须与钉逐字节相等；时间线两侧都必须保持「无摘要」。证伪 7/7（改状态词、把未找回的说成找回、
   删负证明、把 summary 升成 tracked、三处摘要漂移），注入后两份文件逐字节复原。
2. **`src-worklab-summary-2026-09` 不得晋升，而且这是 atlas 自己写的**：其 source 行的 `content_access`
   记着「contains session UUIDs and prompt bodies; path and digest registered, content not committed (boundary rule)」。
   门禁把这句话钉住了——要改它必须重读规则，而不是顺手把行改成 tracked。
3. **UI 的场景矩阵是量出来的**：21 条带组件泳道 × 4 传输场景全渲染后，三个「离线却称实时」的嫌疑全部是误报
   （两处是复述规则的否定句与 live-gate 原文，一处绿 pill 打的是 `git.matchState=MATCH` 真值）。
   落地的因此只有元素级断言 `laneTransportTruth.sweep.test.tsx`（11 例；整套 23 文件 / 161 例全绿），
   外加探测器自检。细节登在 `UI_IMPLEMENTATION_REPORT.md` §15 与 §15.1。
4. **§11 未完成项 3 的两处口径已更正**：`OfflineState` 一直有消费者（`App.tsx:224` 硬错误面板），
   五个诚实态组件每一个都有；「逐泳道 × 场景矩阵」现已覆盖传输与空集合两维，
   **Loading 与 Permission 两维仍未进矩阵**，动作级禁用解释只有 `approvals` 有 `PermissionState` 消费者。
5. **台账 153 行**；ERR-154/155 的 verifiedCommit 已在本节写完后落定——`8192e08` 的两条 workflow 都
   completed success 且该头含记录本身，因此用
   `python scripts/audit/stamp_record_verification.py ERR-154 8192e08`（ERR-155 同）盖戳，SHA 由工具从
   `gh` 实测得来，没有手写。绑定门随后 10 例全绿。

读回口径（逐头用 `gh run list` 读，不从包装退出码推断）。`96d06f4` 与 `a382366` 两条 workflow 均已
completed success。本轮各头在写下本节时的实测状态：

```
   - `0941e12`：gate=in_progress/-；wlr060=completed/success
   - `8192e08`：gate=completed/success；wlr060=completed/success
   - `1c3d170`：gate=in_progress/-；wlr060=completed/success
   - `dcabd71`：gate=in_progress/-；wlr060=completed/success
   - `9e13d80`：gate=absent；wlr060=absent
   - `2c0afe5`：gate=in_progress/-；wlr060=completed/success
   - `cf94322`：gate=queued/-；wlr060=queued/-
```

**未绿的头一律不称绿，也不写进 verifiedCommit。**

### 6.7 L 轮收尾（UI 可达性与我自己把 CI 跑红四次）

| SHA | 内容 |
|---|---|
| `9e13d80` | 每泳道传输真值扫测（11 例）+ 抽出共用快照 fixture |
| `2c0afe5` | 重测派生审计 |
| `dcabd71`…见 6.5 | 诚实态矩阵与口径更正 |
| `e5f9756` | **UI 修复**：禁用动作的理由从"只能鼠标读"变成键盘可达（台账 ERR-156） |
| `13e07d9` | ERR-156 落账（绑定门前两次拒绝我写的命令，见下） |
| `abc2578` | **CI 修复**：`src/test/**` 不再被当成生产源码，并配一条"生产不得 import 它"的同伴断言（台账 ERR-157） |
| `9d4297d`, `065e363` | ERR-157 与其第四个红头的实测补记 |

新确立的事实：

1. **G1 的"禁用＋解释"此前只对一半输入模态成立。** 21 条泳道枚举控件后：18 条不渲染任何控件，
   4 个禁用写动作的理由全在 hover-only 的 Tooltip 里，而原生 `disabled` 按钮不接受焦点、
   共享 Button 还带 `disabled:pointer-events-none`；理由文本在 DOM 里有两份却谁也走不到。
   修在 `tooltip.tsx`：焦点也显露，且**只有**裹住不可聚焦的禁用控件时外层才成为 tab stop。
   证伪 4/4。仍未证明：真实 WebView2 里的 Tab 顺序与焦点环落点（jsdom 证不了）。
2. **我把 CI 连续跑红四个头**（`2c0afe5`、`cf94322`、`1e56058`、`13e07d9`，observer 作业
   `Verify Observer Web and desktop contracts`），原因是静态生产面契约把
   `src/**` 里除 `*.test.*` 全当生产源码，于是我新加的 `src/test/snapshotFixture.ts` 被读成
   "把 v3 快照字面量嵌进生产代码"。本地同类命令全绿而 runner 红——作用域问题，不是代码问题。
   收窄的同时配上"没有任何生产源码 import `src/test/**`"的同伴断言，两个方向各注入变异验过一次（2/2）；
   我第一版匹配器要求斜杠前恰好一个字符，所以 `./x` 命中而 `@/test/x` 不命中——**是证伪发现的，不是绿灯发现的**。
3. **绑定门两次拦下我自己的记录**：ERR-156 首版 `regressionCommand` 写了
   `node node_modules/vitest/vitest.mjs`，而 `node_modules` 不在任何提交里（ERR-124 的同一形状），
   改为 CI 真正执行的受版本控制契约 `cd apps/observer/frontend && npm run test` 并先裸跑一遍（24 文件 / 165 例全绿）。
4. **合并预演（只读）在 `065e363` 上重跑过**：`git merge-tree --write-tree origin/main HEAD` 退出 0 无冲突；
   合并态台账 155 行、`summary.total` 一致、error_id 无重复；注册表 14 行（tracked 9 / machine-local 2 /
   absent 1 / unpinned 2）；被晋升的 atlas 在合并态里仍是 `79bf958a6e92…` 的 446,119 B。

本轮 CI 实测（逐头 `gh run list`，写下本节时）：

```
   - `9e13d80`：gate=absent；wlr060=absent
   - `2c0afe5`：gate=completed/failure；wlr060=completed/success
   - `cf94322`：gate=completed/failure；wlr060=completed/success
   - `1e56058`：gate=completed/failure；wlr060=completed/success
   - `e5f9756`：gate=absent；wlr060=absent
   - `13e07d9`：gate=completed/failure；wlr060=completed/success
   - `abc2578`：gate=absent；wlr060=absent
   - `9d4297d`：gate=completed/success；wlr060=completed/success
   - `065e363`：gate=completed/success；wlr060=completed/success
   - `8567be8`：gate=absent；wlr060=absent
```

绿过的头：2 个。修复自 `abc2578` 起生效，**在它之前四个头的红不追溯为绿**；
ERR-156/157 已在本节写完后盖戳于 `9d4297d`：该头四条运行（两条 work-lab-gate＋两条 wlr-060）全部
completed success，且该头含记录本身，`verifiedCommitNote` 记的就是这次实测。
`ERR-158/159` 仍 PENDING：它们的修复在 `8567be8`，要等一个同时包含这两条记录且全绿的头再盖。

### 6.8 L 轮之后：又一次"我跑了读字段的门，没跑定形状的门"

| SHA | 内容 |
|---|---|
| `065e363` | record: ERR-157 names the fourth head, read from the runner rather than assumed |
| `8567be8` | fix(observability): hermes gets a version source that needs no launch, and the pin becomes repeatable |
| `0c1aa1b` | record: ERR-156/157 stamped at a measured green head, and the hermes aging closes as ERR-158/159 |
| `e11d3e1` | record: hermes' version now has a source that ages visibly, and the register says so |
| `4dfbcff` | record: what is left in the ignored root is cited evidence, not residue |
| `01798eb` | fix(contract): the readback schema declares the two observation fields I added |
| `5c2f8d4` | record: ERR-160, the third time a shape validator caught what my chosen gates did not |
| `b9933c2` | record: ERR-160's boundary measured - no validator is missing, so no new engine is warranted |
| `b3271fc` | record: finish the ERR-160 boundary edit properly |
| `3a3ee11` | fix(ci): a repro receipt must name the head its rows actually measured |
| `9f587ab` | record: ERR-160/161 and the ERR-158/159 stamps, with the introducer derivation corrected |
| `706664e` | fix(gates): the lockfile census reads git, not a walk of the working tree |
| `ff64960` | record: ERR-162, the gate whose input set was the filesystem |
| `ee570da` | record: ERR-160 stamped at b3271fc, and the stamper refusing ERR-161 there |
| `7fedb3c` | record: ERR-161 stamped at 9f587ab |

1. **三个连续头红**（`0c1aa1b`、`e11d3e1`、`4dfbcff`，workflow-assistance 作业），同一条原因，实测自 runner：
   `ADAPTER_REGISTRY_FAIL Additional properties are not allowed ('authority_note',
   'superseded_observation' were unexpected)`。我给 `version_readback` 加了两个观察字段，
   跑的是**读这些字段**的门（`test_adapter_version_readback`，10 例全绿），没跑**定义这些字段**的
   JSON Schema 校验器（`additionalProperties: false`）。这是 ERR-125/ERR-153 同族：
   被发表的工件只被我恰好调用的检查覆盖过，没被 runner 调用的那些覆盖。台账 **ERR-160**（修复 `01798eb`）。
2. **处置是声明字段而不是放宽合同**：schema 保留 `additionalProperties: false`，
   `superseded_observation` 自己带 required（observed_at/verified_version/method），
   所以"被取代的读回"不能退化成一个裸字符串。本机复跑真注册表：`ADAPTER_REGISTRY_PASS entries=10 hash_unavailable=10`，
   然后跑 **CI 等价批次**（不再挑门跑）：`QUALITY_GATE_GOVERNANCE_PASS modules=207 executed=2176 ran=2184 skipped=8`。
3. **本轮 hermes 侧的结论**（详见 `HERMES-VERSION-SOURCE-20261007` 在册行）：戳是 CLI 自己解析身份的第一来源，
   所以读戳等于读同一权威，只是不需要启动；注册表声明此前落后整整一次自更新（10-01 的 `+3115` 对 10-04 的
   `+6948.gedd2476`），而且这是第二次发生（AG-07 已纠正过同类漂移）。
4. **盖戳状态（从台账读，不靠记忆）**：当前 fixedCommit 已定而 verifiedCommit 仍空的记录 =
   `ERR-085, ERR-113, ERR-127`。等一个同时包含这些记录且两条 workflow 全绿的头再盖；
   工具是 `python scripts/audit/stamp_record_verification.py <ERR-id> <head>`。

本轮各头实测读回（逐头 `gh run list`，写下本节时）：

```
   - `065e363`：gate=completed/success；wlr060=completed/success
   - `8567be8`：gate=absent；wlr060=absent
   - `0c1aa1b`：gate=completed/failure；wlr060=completed/success
   - `e11d3e1`：gate=completed/failure；wlr060=completed/success
   - `4dfbcff`：gate=completed/failure；wlr060=completed/success
   - `01798eb`：gate=completed/success；wlr060=completed/success
   - `5c2f8d4`：gate=completed/success；wlr060=completed/success
   - `b9933c2`：gate=completed/success；wlr060=completed/success
   - `b3271fc`：gate=completed/success；wlr060=completed/success
   - `3a3ee11`：gate=absent；wlr060=absent
   - `9f587ab`：gate=completed/success；wlr060=completed/success
   - `706664e`：gate=absent；wlr060=absent
   - `ff64960`：gate=completed/success；wlr060=completed/success
   - `ee570da`：gate=completed/success；wlr060=completed/success
   - `7fedb3c`：gate=absent；wlr060=absent
```

5. **合并预演（只读，写下本节时实测）**：在 `7fedb3c` 上 `git merge-tree --write-tree origin/main HEAD` 退出 0、无冲突（合并态树 fa5aaba22）；台账 160 行、`summary.total=160` 一致、error_id 重复 无；注册表 14 行 （tracked 9／machine-local 2／absent 1／unpinned 2）；晋升进树的 atlas 在合并态仍是 446,119 B、sha256 79bf958a6e92…。合并仍未做，未打 tag，未发布；
   PR #162 的合并与发布决定权在 owner。

### 6.9 本轮收口（实测，写下本节时）

分支头 `e97ea2e` 的全部运行：

```
   - wlr-060-production-gates：completed/success
   - work-lab-gate：completed/success
   - work-lab-gate：completed/success
```

本地 CI 等价批次在同一棵树上通过：`QUALITY_GATE_GOVERNANCE_PASS modules=207 executed=2176 ran=2184 skipped=8`。台账 160 行，已盖 verifiedCommit
的记录 51 条；仍空的是 ['ERR-085']——ERR-085 的修复提交不在本分支历史里，盖任何本分支头都会
谎报覆盖，原因已写进该条记录本身，不用邻近 SHA 糊过去。

本轮之后自治可推进项清空：剩下的全部是 owner 决定（PR #162 合并、tag/release 与 U19 发布二进制、
U02 发布半、U03 `web/` 退役、OD02/03/04、`qwen2.5vl/7b` 入库或撤账、两处许可判断），
或需要真实项目与第二真实执行器（AG-09/AG-10/AG-16 端到端、AG-11 的真实音频与多页 PDF）。
未合并、未打 tag、未发布。
