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


## 仍然未知 / 仍然欠（不伪装成已完成）

- 28 处不带 `dir=` 的 `mkdtemp` 在册债务（12 测试文件 21 处 / 3 生产文件 7 处）；是否漏出残渣只对被实测的
  `auth-ref-*` 判定过，其余未判定。`TemporaryDirectory()` 自清理，不在本项范围。
- os-external 那份原件的**仓库外副本仍是权威原件**；镜像只保证仓库内有字节，不保证两处分叉后谁更新。
- `%TEMP%` 里 Codex 预览草稿（1 条）不删——不是本项目的权限；`D:\All projects\Record` 与 DESIGN-LAB 一律不动。
- ledger 现在 6 行：本轮追加 2 行（镜像入 + 残渣释放），其余为历史；“每次写一行”在 2026-10-06 之前的写入上
  根本无法成立，这是扫描器只能按名匹配的结构性理由。
- 桌面 UI/商业级落地、AG-09/10/12/13/15/16/17/18、U02 publish、U03/U08、AG-19 缺失原件其余项、
  Control Surface 可写侧：与本轮之前一致，未推进。

