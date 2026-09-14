# WORK-LAB 交接 — WL-BASELINE-HERMES（Hermes 五维基线适配）

任务 ID：`WL-BASELINE-HERMES`　顺序 1　执行者：**DSH / DeepSeek**　目标软件：**Hermes Agent**
执行日期：2026-09-14　状态：**`PARTIAL_WITH_BLOCKERS`**（软件关键使用面已通过；剩余项逐条列于 §7）

> 本文件是任务包要求的"一次交付"记录，更新并取代 `WL-LAYER` 旧交接中与本轮不一致的段落。
> **未生成新的套娃任务包。** 本地完整证据（28 个文件）在
> `.project-local/artifacts/task-artifacts/WL-BASELINE-HERMES/`，该目录**被 gitignore**，不在本仓库内。

---

## 1. 前后版本与入口

| 项 | 前 | 后 |
|---|---|---|
| 引擎版本 | `Hermes Agent v0.21.2 (2026.9.11)` | **不变（KEEP）** |
| 安装方式 | `git`（**浅克隆**，67 条 shallow 边界） | 不变 |
| 安装目录 | `<HERMES_HOME>/hermes-agent` | 不变 |
| CLI 入口 | `<HERMES_HOME>/bin/hermes.exe` | 不变 |
| 桌面入口 | 桌面快捷方式 → `<HERMES_HOME>/hermes-agent/apps/desktop/release/win-unpacked/Hermes.exe` | 不变 |
| Profile | 2 个：`◆default` = `agnes-3.0-flash`；`deepseek-review` = `deepseek-v4-flash` | 不变 |

### 版本裁决 `KEEP` 的依据

1. **本机就是最新官方稳定发布**：远端最新**版本 tag** = `v2026.9.11`（次新 `v2026.9.7`）；GitHub releases 最新非预发布 release 同名同日；`hermes doctor` 报 `✓ Version files consistent (0.21.2)`。
2. 所谓"**落后 819 提交**"是相对**未打 tag 的 `main` 开发线**，不是相对任何已发布版本。升级到 `main` 等于把生产安装迁到未发布代码，与"受支持且满足用途"相反。
3. 兼容性已验证、用途已满足、升级路径已就绪（`--plan` 报 **code swap only / 无运行服务**；本地安装树洁净 0 处修改）。

### 重估触发条件（写死，避免变成"永不升级"）

出现新稳定 tag（≥ `v2026.9.12` 或 `v0.22.x`）／用户明确要求跟进 `main`／出现已发布稳定版内缺陷且 post-release 已有修复／state.db 健康度恶化到需要新版恢复路径。

> **已知**：post-release `main` 尖端 `9b199246e5` 是 `fix(desktop): cancelAndWait resolves only once the composed drain settles`，**未进入任何稳定 tag** → 取消能力缺口**无法**靠 KEEP 闭合。

---

## 2. 五维基线结果

| 维 | 结果 | 证据 |
|---|---|---|
| 1 唯一入口 | **PASS** | CLI 与桌面入口均可解析且指向正确安装/版本；无冲突启动链；**未新造**任何包装器 |
| 2 桌面入口 | **PASS（入口与窗口）**；界面内容 `NOT_ASSERTED` | 从快捷方式**真实启动**：主窗口标题 `Hermes`（pid 22072，`Responding=True`），gateway 全程 `stopped`；`CloseMainWindow()` 后剩余进程 **0** |
| 3 官方标准＋用户配置 | **PASS** | 逐字段所有权审计、**零写入**、用户选定路由保持、OBSERVE 未越权；升级/迁移/备份机制实测存在 |
| 4 无阻塞开销 | **PASS** | 13 个受管 `SKILL.md` 全部 ≤10 KB（最大 9,194 B，合计 73.5 KB）；**常驻**技能描述 131 条 / 约 46.9 KB；SOUL.md 2,216 B / **0 个含日期的行** |
| 5 任务级模型策略 | **PASS（含 `UNKNOWN` 标注）** | 主/辅/回退/重试关系**逐 profile** 明确；未降级（default `reasoning_effort=high`）；未拉满；费用 `UNKNOWN` |

---

## 3. 模型与费用来源（逐 profile，禁止合并）

| | `default` | `deepseek-review` |
|---|---|---|
| `model.default` | `agnes-3.0-flash` | `deepseek-v4-flash` |
| `model.provider` | `agnes-3-0-flash`（`https://apihub.agnes-ai.com/v1`） | `deepseek` |
| `fallback_providers` | `[]` | `[]` |
| `agent.reasoning_effort` | `high` | `medium` |
| 辅助槽 | **19 个，全部继承**主模型 | `vision` 槽**显式**指向 `openai-codex`/`gpt-5.5`，其余 `auto` |
| `model.max_tokens` | `8192`（**KEEP**，见 §4） | **未设置** |

* 第二 provider `tokenrouter`（声明模型 `z-ai/glm-5.3-free`）**已声明但无任何路由指向**（OBSERVE，未触碰）。
* **费用来源**：models.dev 缓存目录价 `agnes-3.0-flash` in 0.05 / out 0.15；`deepseek-v4-flash` in 0.0983 / out 0.1966；`z-ai/glm-5.3-free` 0/0 —— **目录声明，非本机账单**。
* **计费/额度 = `UNKNOWN`**：从不声明免费、从不写 0。历史那次 402 的准确表述为"**请求被拒绝，未观察到成功生成**"。
* 已在**本版本内**的相关上游修复（*release-note 依据，未做代码级复核*）：`#107366` 未选 provider 永不计费；`#107281` 不自动切到无凭据 provider。

---

## 4. 配置与规则变更 —— 扩展裁决清单

| 项 | 裁决 | 依据 |
|---|---|---|
| `model.max_tokens = 8192`（default） | **KEEP** | 用户裁决"按官方推荐"。隔离空 home 实测官方默认**为未设置**；但官方回归测试 `#20741` 明确点名"**custom OpenAI-compatible endpoints** 缺该值会被 `finish_reason="length"` 截断"，而**实测两个 provider 都没有 `max_output_tokens`** → unset 会落到 `None`。且五维第 5 维禁止"拉满"，故也不取满额 65,536 |
| 第二 profile `model.max_tokens` | **HOLD（无需动作）** | 本来就未设置，天然符合官方默认 |
| `SOUL.md`（根 profile） | **KEEP** | 2,216 B / 17 行 / 0 日期行；人格、边界、流程三分；repo 与 live 字节一致 |
| 第二 profile `SOUL.md` | **KEEP（独立）** | 384 B / 4 行，与根 profile 不同 → 登记为**范围约束** |
| `requesting-code-review` / `codex` 受管定制 | **KEEP** | `skills list-modified` 明示二者为 **user-modified bundled skills，`hermes update` 会保留**；`skills diff` 把**我们的副本**标为 `yours`。stock 版分别含 "auto-fix" 与更旧版本，**原生不满足需求**。**不使用** `skills opt-out`（全 profile 级 = 包内禁止的"全部禁用"） |
| `references/validated-cases.md` | **UPDATE（对齐，非删除）** | 该文件是**操作指令**且 `SKILL.md` 明确指向它。保留诊断价值，动作对齐 R7 标准：先确认 PID 归属 → 先请求正常退出 → 强制终止为**已授权的最后手段** → **绝不作为"原生取消可用"的证据**。**不是因为出现 `taskkill` 字符串就判整篇不合格** |
| `agent-workflow-fortress/references/workflow-absorption-2026-07.md` | **UPDATE（隐私对齐）** | 第 5 行是历史记录、第 6 行是 durable rule；**两条教训全部保留**，仅把用户逐字引述改为功能等价转述 |
| MCP | **KEEP** | 声明与启用一致，**仅 `context7`**，版本**钉死** `@upstash/context7-mcp@3.2.2`；未新增、未升级 |
| 插件 | **KEEP（未改）** | enabled 5 / disabled 2 未动；`plugins compat` ✓ 无导入今日将移除的路径；`plugins capabilities` 无声明/持有能力 |
| `observability/langfuse` | **HOLD（不自动开遥测）** | 属用户既有授权；本包未开启、未配置、未改动其外发参数 |
| 同步器 `--plan-json` 输出容器 | **UPDATE（最小修）** | `<repo>/.hermes/task-artifacts/` → `<repo>/.project-local/artifacts/task-artifacts/`（帮助文本与校验消息同步更正 + 理由注释） |
| `hermes plan` 入口 | **REMOVE（本项目不使用）** | 官方仍写 `<workspace>/.hermes/plans/`，与项目数据边界冲突。**更正旧表述：`.gitignore` 不构成写入许可**；**不为它 fork 原生软件** |
| Hermes hooks allowlist | **HOLD（待用户一次同意）** | `hooks doctor` 报 1 issue：受管守卫**在批准后被修改**（改动仅 1 行，`.hermes/task-runtime` → `.project-local/runs`）。**未执行** `revoke`（会改变用户运行状态） |
| curator ↔ 受管技能目录 | **HOLD（所有权裁决未决）** | 结构性冲突；**不得**再称"改 `create_dir` 即可解决" |
| 原生技能 | **未清空、未禁用** | 全程未使用 `skills opt-out/reset/remove` |
| ADD / REPLACE | **本轮无** | 无缺口需新增或替换；未安装任何社区技能/框架/新 MCP |

---

## 5. 部署与读回

| 步骤 | run_id / 值 | 结果 |
|---|---|---|
| 建立受管基线 | `sync-20260914T134235Z` | `will write 0 target(s)`；21/21 收敛；前后摘要比对 `changed=0` |
| 发布（上一轮） | `sync-20260914T135005Z` | `windows-development-environment` `59cf51d046f81510`→`2bd2de7e07fe162e` |
| **发布（本轮）** | `sync-20260914T154558Z` | **2 个目标**：`agent-workflow-fortress` `1e3ae54c81f210d5`→**`f56043a8b4337ee3`**；`windows-development-environment` `2bd2de7e07fe162e`→**`5132fc01855817c3`**。`refusing: []`、`suspended: []`、`ACTION_PLAN_READBACK_PASS` |

**四层验证：全部 PASS**
1. **存在**：两棵技能树 live 与仓库均在位；
2. **源等价**：`agent-workflow-fortress` 11/11、`windows-development-environment` 22/22 文件，**0 字节差异**，live-only/repo-only 均为空，两侧树摘要**均等于**发布记录的候选值；
3. **运行时可达**：两处 frontmatter 可解析且 `name` 正确；
4. **行为应用**：对齐语句全部在位；**用户逐字引述已不在任何已部署文件中**。

**发布后原生读回**：两技能在 `skills list` 中为 `local`/`enabled`；`skills list-modified` 仍为 2（升级兼容的定制）；`doctor` exit 0（`Version files consistent (0.21.2)`、`Config version up to date (v44)`、`No deprecated config keys`）；模型路由未变。

**守卫接入真实受管入口（原生证明）**：`hermes hooks test pre_tool_call` 真实触发受管 hook，返回 **Hermes wire shape** 的拒绝：
`{"action": "block", "message": "PROJECT DATA BOUNDARY BLOCKED: terminal calls must declare an explicit Git-project workdir."}`（exit 0，0.063s）。

---

## 6. 独立审核（H6）状态

**尚未进行，本轮不得自签最终通过。** 备料已就绪：

* 4 个权威文件的 blob SHA 与本地 `HEAD:path` **全部 SAME**；远端 `r4-recovery-exec` == 本地 HEAD；
* **须注意的未提交差分**：`config/config-ownership.json` 在包内引用的是**已提交**版本，本轮改动即基于工作树生效版；
* 候选指纹、run-id、门禁绑定、四层验证、原生读回、限制登记均已落盘（本地 `.project-local/artifacts/task-artifacts/WL-BASELINE-HERMES/`）；
* 审核规范须在**本候选变动之前**固定；审核环境**不得加载候选自身可影响验收的指令**。

---

## 7. 剩余项与恢复

### 7.1 剩余项（逐条注明是否影响下一包）

| # | 项 | 影响下一包 |
|---|---|---|
| 1 | `hooks doctor` 报 1 issue：受管守卫批准失效，待用户复核那 1 行后 `revoke` + 重新批准。**功能当前可用且有 wire-shape 证据** | **否** |
| 2 | curator ↔ 受管目录结构性冲突的所有权裁决 | **是** |
| 3 | 分类器残余风险：`structured success + acceptance` 可压过文本终端错误（已固化为 2 项契约测试） | **否** |
| 4 | **原生取消能力受限 `NOT_EXERCISED`** | **是**（禁止假设"可取消"） |
| 5 | **计费/额度 `UNKNOWN`** | **是**（禁止成本声明） |
| 6 | 23 个文件违反 `.gitattributes` 的 `eol=lf`（**20 个与本包无关**） | **否** |
| 7 | `EXACT_SHA_CI_UNVERIFIED` | **是**（不得写 CI green） |
| 8 | `chrome-profiles` toolset 清单缺口（本轮**未复现**，属插件侧） | **否** |
| 9 | H-06 零模型 Radar | **否**（包内正式延后至 WL-LAYER-14） |

### 7.2 恢复方式

1. **Hermes Home**：`<HERMES_HOME>/backups/workflow-assistance-sync-*`（本轮新增 `…-20260914-234558-756707`）；守卫保留已发布基线，可回滚至 `2bd2de7e07fe162e`（windows）与 `1e3ae54c81f210d5`（fortress）；
2. **原生配置/数据恢复**：`hermes backup` / `hermes import` / `hermes checkpoints`；原生升级流程会自建 `state.db` 紧急备份（实证 `state.db.pre-update-emergency-2026-09-02T16-55-44-069Z.bak`，4.07 GB）。**注意 `updates.pre_update_backup = false`** → 未来升级须显式 `--backup`；
3. **仓库**：`git revert <commit>` 或 `git checkout <sha> -- <path>`；本包新增 1 个测试文件与 1 份交接文档可一并回退。

---

## 8. 错误总结（含执行者自曝，勿视为已解决）

### 8.1 本轮（WL-BASELINE-HERMES）执行者自查出的错误

| # | 错误 | 性质 | 处置 |
|---|---|---|---|
| BH-E1 | 判定"N-8：受管副本被 builtin 遮蔽 → **未生效**" | **判断错误** | 已更正。`Source=builtin` 只是**来源标签**；`hermes skills diff` 把我们的副本标为 `yours`、`skills list-modified` 明示"user-modified bundled skills，`hermes update` 会保留"→ **我们的副本生效**。N-8 **不是缺陷** |
| BH-E2 | 称"N-1 curator 冲突**已基本闭合**" | **不成立** | 已更正为**结构性冲突**：`curator.py:86` 状态落在 `HERMES_HOME/skills/.curator_state`、`curator_backup.py:74` 表明 curator 目标就是 skills 目录本身；检索未发现可重定向的配置 → 改 `create_dir` 不能解决，需所有权裁决 |
| BH-E3 | 以 `.gitignore` 作为 `.hermes/plans/` 的写入理由（"越界但受控"） | **口径错误** | 已更正：**`.gitignore` 不构成写入许可**；本项目保持不使用 `hermes plan` 入口 |
| BH-E4 | 报"**12 个文件**行尾被 LF→CRLF 翻转" | **过宽** | 已更正：`.py` 的 CRLF 在本仓库**是正常结出**（382 个 tracked `.py` 中 325 个为 CRLF）。真正违反 `eol=lf` 的 23 个文件中 **20 个与本包无关**；`config/skills-inventory.json` 未修改却同样 CRLF → 证明这是 **git 不可见**的既有稳定状态。**只登记不重写** |
| BH-E5 | 写"**17 个**辅助槽" | **数据错误** | 实测 **19 个**，且漏列 `goal_judge`、`memory_query_rewrite`、`review` |
| BH-E6 | 四层验证首轮报 2 项 FAIL | **检查器错误** | 期望值写错（markdown 加粗 `**never**` 未归一化；误把 hook 输出串当文件内容）。**非部署失败**；修正后全 PASS |
| BH-E7 | 合成额度测试首版断言错误（期望 `reason=billing_*`、并以缺 acceptance 的输入期望 FAILURE） | **契约理解错误** | 分类器实际把具体类别放 `evidence`、`reason` 为泛化值；且 `acceptance=None` 永不产生 SUCCESS。已按**真实契约**重写，并把"结构化成功可压过文本终端错误"这一**文档化设计选择**固化为 2 项契约测试 |
| BH-E8 | 用 PowerShell `Select-String -Context` 渲染造成"provenance 文件重复/乱序"的假象 | **工具误读** | 直接用文件读取复核，确认文件结构正常 |

### 8.2 历史轮次遗留（仍然有效，随交接继承）

| # | 错误 | 处置 |
|---|---|---|
| E-1 | 对生产 `config/skill-provenance.yaml` 运行 `--write`，把 13 个 `live_sha256` 换成 `pending-live-sync` 占位符 | 已从备份恢复；**已建立约束：绝不对生产运行 `--write`** |
| E-2 | 打包脚本 `rmtree` 删除了手工撰写的 `00-INDEX.md` / `06-convergence-addendum.md` | 已恢复；脚本改为只清理生成物 |
| E-3 | 上传自检假阳性（正文出现 `.env`/`config.yaml` 字样即判敏感） | 改为**内容形态**检测 |
| E-4 | 清理动作删除了被引用的 `prov-neg/real-backup.yaml` | 已披露；E-1 的验证改写为"重算复现" |
| E-5 | PowerShell `Get-Content -Raw`+`Out-File` 的 GBK 往返损坏 4 个构建脚本，并残留 17 处 `—?`（曾进入压缩包 README） | 已修复；旧包移入 `superseded/` 并由新包取代 |
| E-6 | shell 设 `PYTHONIOENCODING=utf-8` 导致 `governance` 门禁**假失败**（子进程 UTF-8 写、测试按 GBK 读 → reader 线程 `UnicodeDecodeError` → `stdout=None`） | 确认为调用方环境错配、非回归；**仍记录**：调用方环境能让门禁假失败本身是脆弱点 |

### 8.3 本次上传（公开仓库）相关的强制检查

* **推送前扫描**：对 git 将提交的 **38 个文件**逐个按**内容形态**扫描 → **无凭据材料、无禁止文件类型、无绝对用户路径**；`.project-local` 与 `.hermes` 均被 gitignore。
* **仓库为 PUBLIC**：本次提交使这些内容对公众可见。发布的是**尚未经 H6 独立审核**的候选（见 §6）。
* 本地测试结果**不冒充**云端 CI；`EXACT_SHA_CI_UNVERIFIED` 仍然成立。

---

## 9. 基线绑定值

| 项 | 值 |
|---|---|
| checkout HEAD（改动前） | `c1c6a16454c06f4b90acf7e7913cc7dc62be3802` |
| 分支 | `r4-recovery-exec` |
| 门禁 | **38 / 38 PASS，0 FAIL，0 TIMEOUT**（逐门禁单独调用，非聚合入口） |
| 云端 CI | `EXACT_SHA_CI_UNVERIFIED`（本地测试不冒充） |

---

## 10. 下包前置条件

1. **第 2 包（Hermes 维护 Codex）可用性前置已满足**：CLI 与桌面入口可用、两 profile 模型身份明确、受管资产 21/21 与候选一致、四层验证通过；
2. 第 2 包须先读本文件 §7.1 与本地 `LIMITATIONS.md`（L-1…L-9）：尤其 **原生取消能力受限**、**计费 `UNKNOWN`**、**第二 profile 独立性**（其有独立 105 个技能与独立 `SOUL.md`，受管覆盖层**仅作用于根 profile**）；
3. 第 3A 步独立审核须注意 `config-ownership.json` 的未提交差分（生效版本 ≠ 包内 blob）；
4. `AGENTS.md` 与用户共享技能目录**仍未编辑**（`BLOCKED_ACTIVATION`：本会话加载它们，改它们等于会话激活自己加载的规则），须由不受候选控制的隔离环境执行。
