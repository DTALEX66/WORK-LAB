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
| `8847cdc` | `tool_version_metadata_probe.py`：不启动进程取版本 | 收据 `docs/audits/TOOL_VERSION_METADATA_PROBE_2026-10-07.json` |
| `1276547` | 五个适配器版本按 AG-07 既有字段入账 + 交叉门禁 | 门禁 8 项、反证 7/7 转红；`QUALITY_GATE_PASS gates=adapter-registry` |

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
   `ERROR_LEDGER_PASS counts_consistent=true`，`bound=38 unboundPass=95 anomalies=0`。

## 3. 本轮撤回与自我纠错（照登，不改口径）

1. **UI 报告 §12"几何门禁仍未接入 CI 必需步骤"已被 §13 取代**：那是接线前写的，现为必需步骤且有 runner 读数。
2. **一次性吸收探针报"14 条已吸收落点 ABSENT"是探针错**：它按仓库根解析模块根相对路径。语料没错，文档一字未改。
3. **github 版本我先写 `2.98.0`**：新门禁当场拒绝（收据里是 `2.98.0 (2026-08-20)`）。改的是我的声明，不是门禁。
4. **ERR-152 是我自己造成的红**：两个"必须拒绝"的负控制拿在册台账当输入，合法盖章后它们再也无法失败，
   `1ece4af/bbb79c2/7375234/7eb8ab4` 四个头因此红；我只跑了子集、没重跑那个被改了输入的文件。
5. **本地整轮复现曾出现 governance `errors=1`**，消息指向一个未被跟踪的本机残留目录（其中任务包目录名重复
   了一层），同头裸跑 2130 项全过；我按"本机竞态"记录且**未据此报 PASS**，最终仍以 exact-SHA 读数为准。
   这一条仍未彻底解释，保持挂账。

## 4. 需要 owner 或真人操作（明确挂账，不得代答）

- **U02 发布半段**：Hermes Home 有一条未审阅技能，部署被门禁挡住。
- **U03 `web/` 退役**、**U19 release 二进制重建/发布**（无 tag、无发布已执行）。
- **OD02/OD03/OD04**（AG-12/13/17/18 决策项）；**AG-09/AG-10** 需真实项目 + 第二个真实执行器 + 真实消费者；
  **AG-16** END-TO-END 同上。
- **模型入库缺口**：`registry.ollama.ai/library/qwen2.5vl/7b` 5,969,233,408 B 在库而无注册行。
- **许可判断**：mcp-inspector 与本仓库许可属 owner/法务问题（见候选池与 source-licence 记录）。

## 5. 下一份工作的优先顺序

1. 109 条无 fixedCommit 的挂账记录：先做**只读分诊**（承诺补救是否已在树里），分"可绑定"与"仍是缺口"，
   不得批量造修复。
2. `model_library_readback.py` 的字节数缺陷（内容地址行报整个存储体量）——本机仪器，改前先写反证。
3. 适配器观测的老化：收据日期与注册表 observed_at 一致已由门禁钉住，下一步是让收据本身周期性重生成。
4. PR #162 合并与发布决定权在 owner；本轮未合并、未打 tag。
