# SESSION HANDOFF — convergence 2026-10-07 round J

> 本轮范围：外溢数据的**分类与回收**（不是又一个扫描器），以及两处自家仪器的自我膨胀。
> 铁律不变：无证据一律 FAIL/PENDING，不伪报 PASS；本地绿 ≠ CI 绿 ≠ 桌面证明；判内容只认 hash 与 `git diff`。

## 这一轮真正改变了什么

1. **扫描开始区分“谁写的”。** `scripts/audit/outside_root_spill_sweep.py` 从前把所有 Git 根外的 WORK-LAB 名字
   合成一句 `SPILL_TO_EXPLAIN`。现在每个命中必须匹配一条带 `basis`（指名支持它的在册记录）和 `disposition`
   的规则，匹配不到就是 `UNADJUDICATED` 并让运行失败。实测 16 条命中分四类：owner 交付材料 13、兄弟项目自己的
   历史文档 1、客户端运行时草稿 1、本项目自己写过且**已回收**的原件 1。verdict 改为
   `NAMED_OUTSIDE_ROOT_ADJUDICATED_AND_RECOVERED`，`notClaimed` 里仍写明按名扫描看不见通用缓存键下的外溢。
2. **一个“原件只在仓库外”的实例被收回。** `WORK-LAB-SHARED-DEPENDENCIES-2026-08-15.md`（自述来源项目 WORK-LAB，
   躺在声明共享根 os-external 的 `docs/`，仓库内 0 处提及，早于 ledger 首行）由
   `scripts/maintenance/recover_shared_root_original.py` 以字节相同镜像入
   `docs/history/archive/recovered-originals/`：3,763 B，sha256
   3a71b7bedd042d7c9e936a01ab08c2625ca4356a880cd2a3f899a950eeee5972，工作区＝git blob＝仓库外原件；原件不动，
   复测 digest 未变。镜像前的关卡：只接受声明根、拒绝 E:/F:、拒绝已存在或已跟踪的目标、内容必须过在册
   `artifact_flow_policy` 且 decision == ALLOW、密钥形状扫描命中即停手（只报数量与点分路径，从不打印值）。
3. **清掉了本仓库自己泄漏到 %TEMP% 的治理材料（ERR-140）。** 根因是
   `tests/ci/test_project_authority_reference.py` 用不带 `dir=` 的 `mkdtemp(prefix="auth-ref-")` 复制整套权威包，
   `tearDown` 的 `ignore_errors=True` 把 Windows 上的删除失败咽掉，19 个目录（304 文件 / 7,126,653 B，全部创建于
   2026-10-01）留在了用户临时目录。先清单后删除：`scripts/maintenance/release_authority_reference_temp_residue.py`
   对每个文件判定“与工作区字节相同 / 在 git 历史里可找到 / 独一无二”，7 份独有内容（271,845 B）先存档再删，
   其中 `taskpacks/current/WORK-LAB-ATLAS-GAP-REMEDIATION-TASKCARD-20261001.md` 在 git 历史里找不到任何等价 blob，
   属于**真独有**——这就是为什么不能直接 `rm`。删后 %TEMP% 剩 0，ledger 追加一行，根因改为
   `dir=_runtime_root()`（`.project-local/runs/`，与 `test_machine_identity.py` 已在用的在册约定一致），
   该文件 19 项测试仍全绿且不再留残渣。

## 两处自家仪器骗了自己（详见 ERR-139 与 INSTRUMENT-FIXES-20261007）

- 引用审计把**自己的输出**当语料，一次重跑 1,705,686 B → 3,676,712 B，而裁决（22 queued / 0 unadjudicated）
  一字未变。排除自身产物后 130,695 B，连跑两次除时间戳外字节相同。
- `artifact_flow_policy._walk_keys` 不产出 list 里的裸字符串，`find_nested_secrets` 对“独占一行的 token”是瞎的
  （docstring 声称覆盖 list 元素）。它是别的模块的代码，改它需要跨模块任务卡，本轮不动；恢复工具改为按行键值化
  喂入，并用测试把上游缺陷和绕过方案一起钉住。
- 我自己的参数名写错（`kind` 而非政策读取的 `artifact_kind`），让一份从未被真正分类的文档拿到看着无害的
  PENDING_AUTHORIZATION；现在 decision 必须等于 ALLOW。

## 门禁与在册

- 新模块：`tests/workflow-assistance/test_outside_root_spill_sweep.py`（11）、
  `tests/workflow-assistance/test_recover_shared_root_original.py`（12）、
  `tests/workflow-assistance/test_temp_fixture_stays_inside_the_boundary.py`（5，AST 扫描，能区分“一句关于 mkdtemp 的话”
  与一次 mkdtemp 调用）。引用审计模块补到 11 项。
- 在册：`SPILL-ADJUDICATION-20261007`、`TEMP-FIXTURE-DEBT-20261007`、`INSTRUMENT-FIXES-20261007`；
  ERR-139（政策扫描器与我的参数名）、ERR-140（治理材料泄漏 %TEMP%，含根因修复与残留清理）。
- 本轮三件新工具都由上述行与本文件引用，因此通过 `test_tool_inventory_coverage.py` 的“不得有无人引用的工具”。


## AG-19：把缺失原件的检验推到 owner 材料根

`scripts/audit/ag19_record_root_pin_test.py` 用 atlas 的 5 个 pin 去测 `D:\All projects\Record`
（114 文件 / 39 zip / 31,382 成员 / 15,078,228,346 B）。两个有 `expected_bytes` 的 pin（时间线
15,558,839 B、WORK-LAB-SUMMARY 164,397 B）在该根下**尺寸命中 0**；zip 只读中央目录，成员未解压，所以这
个否定证明覆盖到归档内部。`SRC-WL-HANDOFF-20260903` 没有 pinned size，工具因此加了“按归一化文件名取名再哈希”
的第二入口（pin 名带 `(1)`，成员名不带——纯精确名字匹配会漏掉范围内唯一真正匹配 pin 摘要的那一条），解包到
`.project-local` 后 sha256 dff24bed285700d2b2c873d39e1356340f4599268449bbd6ab1e74ead525afce 与 pin 完全相同：一件**已恢复原件的第二处独立副本**，
不是找回了丢失的东西，登记时按这个措辞写。

- 名字命中 9 条按归属拆分：6 条属于 AAOS/ArcheAxis/DESIGN-LAB/三项目，2 条无归属，1 条 WORK-LAB（已做内容检验）。
- `REQ-20260928-START` / `REQ-20260928-EXEC` 在 atlas 里没有 `expected_sha256` ⇒ 哈希级否定证明对它们结构性不可
  能；记录与门禁都禁止把“没搜到名字”说成“不存在”。
- 仓库外只读：只解包了一个成员到忽略目录，`D:\All projects\Record` 未被写入、移动或删除任何东西。
- 在册：`AG19-RECORD-20261007`；`.project/governance/recovered-source-registry.json` 新增
  `src-new-chat-handoff-20260903`（machine-local，含复测命令），并把时间线 `absent` 行的范围说明补宽。
- 门禁：`tests/workflow-assistance/test_ag19_record_root_pin_test.py`（12 项）。



## CI 红了两次：机器状态泄漏进门禁（ERR-142）

- 现象：`workflow-assistance` 作业在 c53de17 与 3e1f88b 失败，失败项是我本轮新加的引用审计幂等测试——它断言审计退出码为 0，而 runner 上审计把只有本机的
  `.project-local/toolchains/…` 路径入了队。本地 `reproduce_ci_commands.py` 89 条命令只有 3 个已知 cargo/npm 失败，因为它跑在这台机器上。
- 根因：审计用**本机磁盘**回答“字节在不在”，而 `.project-local/` 按声明就是 git-ignored 运行根 ⇒ 结论随机器变，CI 就跟着随机器变。
- 修法是一条规则：`exists()` 只对仓库负责；`.project-local/` 在任何机器上都判为不可从检出验证；`checkoutVerifiable` 恒 0；`presentOnThisMachine` 只报数不参与跨机比较。
- 直接套规则会让队列 22 → 148，于是改成声明两个类别：`machine_local_runtime_narration`(489 引用) 与 `machine_local_runtime_pointer`(132 引用)；面向读者的文档与
  被跟踪的 machine 字段仍入队 ⇒ ERR-131 类缺陷没有被放宽，队列 6 条全部带处置（写明重测命令或替代的 tracked 观察）。
- 我加的测试自己也犯过一次同类错：比较了 `presentOnThisMachine`（干净检出里是 10 vs 本机 174），已在 d2e0234 改为只比较三个确定性计数，并加断言
  `checkoutVerifiable == 0`。AG-19 的解包件校验改为在缺 `.project-local` 的检出上诚实 skip。
- **验证方式换掉**：推之前用 `git worktree` 指向精确 SHA、`.project-local` 为空，跑相关门禁；六个门禁 61 passed / 2 skipped。同时确认 worktree 不能替代 CI：
  Hermes Home / portable-install 那 17 项因缺实际环境而红（与 ERR-133 的结论一致），所以 worktree 只用来抓“本机文件泄漏进判定”这一类。
- 在册：`CI-MACHINE-STATE-20261007`；错误账本 ERR-142（status_after=PARTIAL，verifiedCommit 仍空，等 9e518e2 或更后面的 exact-SHA 回读全绿才转正）。


## 账本承诺的可核验性：标注、改指，以及被现有门禁抓住的绑定器

- 140 条记录全部打上 `regressionTestVerifiability`；50 个操作数改指到当前跟踪路径；34 条 PATH_GONE、44 条无文件操作数、3 条**故意读客户端 home**（不是坏指针）。
- 标注只从写入后的字节产生：替换没命中就在 note 里自我声明"不声称 re-point"（9 条如此），面向读者的路径全部可解析才叫 REPOINTED。
- 绑定：两个依据（条目引入提交 / 回归文件引入提交 + 日期窗）× 四道闸（≤3 条记录的批量上限、承诺脚本必须存在于该提交、提交必须改到记录点名的路径、不得等于 introducedCommit）。
- **我自己写的绑定器把 86 条记录的分支 cutover 读成 +1 条**（`git show --format= -- <commit> -- <path>` 顺序错，读到空 diff），于是报告 99/99 可绑定；这个"过于干净"的数字本身就是探测器坏了的信号。
  已有的 `test_ledger_fix_commit_binding` 抓到了 ERR-124（承诺 `node_modules/vitest/vitest.mjs`）——按"改我的作品，不动真值测试"，撤销当天 6 条绑定、写明原因、加闸，重跑得 4 条成立（共 28 绑定 / 95 逐条拒绝并给理由）。
- 门禁 17 项，含六种 token 形状反例；标签分布由账本自身结构重算，计数不许手写。工具：`scripts/audit/ledger_regression_command_targets.py`、`scripts/audit/bind_ledger_fixes_with_guards.py`。
- 记录：`LEDGER-PROMISE-STATE-20261007`、ERR-143；ERR-139/140/142 的 verifiedCommit 已在 c1b2997 的全绿回读后补上（该提交含其修复与门禁）。


## 仍然未知 / 仍然欠（不伪装成已完成）

- 28 处不带 `dir=` 的 `mkdtemp` 在册债务（12 测试文件 21 处 / 3 生产文件 7 处）；是否漏出残渣只对被实测的
  `auth-ref-*` 判定过，其余未判定。`TemporaryDirectory()` 自清理，不在本项范围。
- os-external 那份原件的**仓库外副本仍是权威原件**；镜像只保证仓库内有字节，不保证两处分叉后谁更新。
- `%TEMP%` 里 Codex 预览草稿（1 条）不删——不是本项目的权限；`D:\All projects\Record` 与 DESIGN-LAB 一律不动。
- ledger 现在 6 行：本轮追加 2 行（镜像入 + 残渣释放），其余为历史；“每次写一行”在 2026-10-06 之前的写入上
  根本无法成立，这是扫描器只能按名匹配的结构性理由。
- 桌面 UI/商业级落地、AG-09/10/12/13/15/16/17/18、U02 publish、U03/U08、AG-19 缺失原件其余项、
  Control Surface 可写侧：与本轮之前一致，未推进。

