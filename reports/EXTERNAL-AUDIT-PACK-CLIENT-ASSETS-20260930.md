# WORK-LAB 客户端中立资产清点 · 外部审计包（2026-09-30）

| 项 | 值 |
|---|---|
| 包 ID | `assets-20260930` |
| 采集时间（UTC） | 客户端元数据探针 `2026-09-30T14:02:29Z`；全量清点 `2026-09-30T14:02:48Z`；清理候选 `2026-09-30T14:04:25Z` |
| 证据锚定提交 | `49ce5031de5f29c7fa6e8f32f2be4052fd335650` |
| 分支 | `audit/client-asset-inventory-20260930`（基于 `main` = `cd4daa8`） |
| 审计对象 | Hermes / Codex(又名 ChatGPT Agent 侧代理运行时) / DSH(DeepSeek Harness) / CC Switch / Open Design / OpenHuman / GitHub 客户端面，以及本项目（WORK-LAB）全部工作流增强·治理·管理·全局部署·配置·技能·插件·记忆资产 |
| 性质 | **只读元数据清点**（名称/路径/类型/字节/时间/哈希），引用现有权威登记表，不新建平行账本 |
| 目的 | 为「清理垃圾与过时技能/插件」与「重新部署软件相关内容」提供可审计基线 |
| 是否已执行清理 | **否**。13 条候选全部 `executed: false`，需逐路径逐操作显式授权 |

## 0. 给审计者的最短路径（三个 URL）

1. 本包（入口）：`https://raw.githubusercontent.com/DTALEX66/WORK-LAB/audit/client-asset-inventory-20260930/reports/EXTERNAL-AUDIT-PACK-CLIENT-ASSETS-20260930.md`
2. 证据清单与哈希：`https://raw.githubusercontent.com/DTALEX66/WORK-LAB/49ce5031de5f29c7fa6e8f32f2be4052fd335650/reports/audit-evidence/assets-20260930/MANIFEST.json`
3. 原始清点数据：`https://raw.githubusercontent.com/DTALEX66/WORK-LAB/49ce5031de5f29c7fa6e8f32f2be4052fd335650/reports/audit-evidence/assets-20260930/asset-inventory.json`

同目录其余文件（同一 SHA 前缀可替换 `{file}`）：
`https://raw.githubusercontent.com/DTALEX66/WORK-LAB/49ce5031de5f29c7fa6e8f32f2be4052fd335650/reports/audit-evidence/assets-20260930/{file}`

| 文件 | 用途 | 字节 |
|---|---|---|
| `asset-inventory.json` | 全量元数据清点（客户端 + 仓库侧） | 76,293 |
| `inventory-verification.json` | 清点表 vs live 逐文件哈希比对 | 6,966 |
| `CLEANUP-CANDIDATES.json` | 13 条清理候选（证据/风险/授权要求）+ 1 条审计中发现并修复的外溢 | 9,996 |
| `REPO-ASSET-INDEX.md` | 仓库侧人类可读索引（技能/插件/治理/部署映射） | 7,081 |
| `MANIFEST.json` | 上述文件 sha256 + 引用文件 sha256 | 3,405 |

## 1. 摘要（被审计的结论）

| # | 结论 | 关键数字 |
|---|---|---|
| 1 | 客户端软件面共 **7** 个受管客户端（`config/software-registry.json`）：hermes / codex / deepseek-harness / cc-switch / open-design / openhuman / github | CC Switch = `LEGACY_OBSERVE`（只观察，无活动写入） |
| 2 | Hermes 技能面实为 **26 个技能分类目录 + 6 个内部项**，**无空目录垃圾** | 见 §2-A1 与 §4-1（Windows 目录 `st_size=0` 是假象） |
| 3 | 本项目受管技能 **13** 项（权威 `config/skill-provenance.yaml`）；Codex 执行器技能 **14** 项 | 两者是不同面，不是重复 |
| 4 | 发现**真实陈旧/漂移 3 处**：`config/skills-inventory.json` 6/14 哈希不符；`config/plugin-inventory.json` 缺 chrome-profiles revision；`skill-provenance.yaml` 的 `model-switch` source≠live | 全部是可判定、可复核的事实 |
| 5 | 发现**可回收冗余候选 13 条**（≈1.5 GiB Codex 历史库、20 个 Codex 临时/守卫文件、Hermes `state.db` 4.2 GiB、DSH 两套历史备份等） | **未执行删除** |
| 6 | 隐私：凭据与记忆正文**未被读取**；包内 **0** 处密钥命中（正则扫描 6 文件，含本文件） | 见 §2-G |
| 7 | 外部数据盘 `E:\` `F:\` **未访问** | 见 §2-G |
| 8 | 清点过程本身产出价值证据：**发现并修复 1 处真实边界外溢**（`apps/.project-local`），门禁由 FAIL 恢复 | 见 §2-C5 |

## 2. 逐条可判定声明

### A. 客户端软件面（元数据，均为本机实测）

| # | 声明 | 证据字段 | 预期 |
|---|---|---|---|
| A1 | Hermes 技能目录 32 个子项 = 26 个分类目录 + 6 个内部项（`.archive`/`.curator_backups`/`.hub`/`.locks`/`.bundled_manifest`/`.usage.json` 等），**全部非空** | `clients.hermes.skills.children[].child_count` | 目录项 `child_count ≥ 1`；最小者 `apple`/`quality-assurance`/`social-media`/`yuanbao` = 1 |
| A2 | Hermes 用户插件目录只有 **1** 个插件 `chrome-profiles`，其安装元数据记录 `revision=5b9c3257b464c0f926d4355149a8aed9c8f307b4`、`pinned=false`、源 `github.com/anpicasso/hermes-plugin-chrome-profiles` | `inventory-verification.json: hermes_plugin_install_metadata` | 与该字段逐字一致 |
| A3 | Hermes 记忆为 4 个文件（`MEMORY.md` 3,345 B、`USER.md` 2,743 B + 2 个 0 字节 lock），**正文未采集** | `clients.hermes.memories.children[].size` | 仅名称/大小/时间 |
| A4 | Hermes `state.db` = **4,518,653,952 B（≈4.2 GiB）**，为单项最大运行态数据 | `clients.hermes.state_db_size_bytes` | 数值一致 |
| A5 | Codex 主目录 **92** 个子项，其中 **20** 个为 `..codex-global-state.json*.tmp-*` / `.codex-provisioning-*.guard` 残留（**17 个 0 字节**） | `clients.codex.home.children` | 计数一致 |
| A6 | Codex 历史库：`logs_2.sqlite` 675,295,232 B、`thread_history_1.sqlite` 930,263,040 B（≈1.5 GiB） | 同上 `.size` | 数值一致 |
| A7 | DSH `.dsh` 状态目录 16 项，含 `settings.yaml` 61,987 B、`memory/`(3)、`profiles/`(4)、`sessions/`(5)、`skin-center`、`task-board`、`storages`(3)、`llm-deepseek`、`.agent-presets`(2)；`.credentials.yaml` 标记 **SECRET_NOT_READ** | `clients.dsh.state.children` | 密钥文件仅记录"存在"，无内容 |
| A8 | DSH 安装根 12 项：`DSH Desktop.exe` 289,313,640 B、`desktop-user-data`(35)、`locales`(55)、`resources`(3)、**两套历史备份** `.dsh-backup-20260918`(26)/`.dsh-backup-20260920-data`(14)、`.migration`(4)、`.research-20260918`(3)、`pnpm-store`(1) | `clients.dsh.root.children` | 计数与数值一致 |

### B. 本项目（WORK-LAB）资产面

| # | 声明 | 证据 | 预期 |
|---|---|---|---|
| B1 | 目录规模：`config` 25、`.project/governance` 33、`packages/contracts/schemas/workflow` 40、`services` 14、`apps` 3、`scripts` 4、`reports` 9 | `repo_assets.dirs` | 数值一致 |
| B2 | 受管技能 13 个 `SKILL.md` 全部具名并含 sha256 | `repo_assets.managed_skill_files` | 13 条 |
| B3 | Codex 执行器技能 14 个目录（`integrations/executors/codex/skills`），与 `config/skills-inventory.json` 记录条数一致 | `repo_assets.codex_executor_skill_files`、`codex_executor_live` | 14 = 14 |
| B4 | 18 个关键权威文件全部存在（config 8 + governance 10），逐一附字节数与 sha256 | `inventory-verification.json: key_authority_files` | `exists=true` ×18 |
| B5 | 插件登记：3 启用（chrome-profiles / security-guidance / web-ddgs）+ 2 隔离（hermes-media-studio、hermes-telegram-business，均 `DANGEROUS`） | `config/plugin-inventory.json` | 与文件一致 |

### C. 陈旧与漂移（"垃圾/过时"的可判定证据）

| # | 声明 | 核验方法 | 预期 |
|---|---|---|---|
| C1 | `config/skills-inventory.json`（生成于 `2026-09-04T16:49:43Z`）与 live 不一致：**8 项匹配、6 项哈希已变、0 缺失** → 该清点表**已陈旧** | 读 `inventory-verification.json: skills_inventory_check`，逐项比对 `sha256` | `verdict = DRIFT_OR_STALE`；变更项为 observer-delivery / project-data-boundary / safe-project-execution / self-improvement / verification-hardening / windows-development |
| C2 | `config/plugin-inventory.json`（生成于 `2026-08-26`）对 `chrome-profiles` 记 `commit: null`，而 live 安装元数据已有 `revision=5b9c3257…` → **登记不完整** | 比对两文件 | `commit=null` vs live revision 非空 |
| C3 | `config/skill-provenance.yaml` 的 `model-switch`：`source_sha256=37aed9558bc1…` ≠ `live_sha256=0a02c1fc8b65…`，其余 12 项完全一致 → **单点漂移** | 读 `repo_assets.skill_provenance_drift` | 仅 `model-switch` 的 `drift=true` |
| C4 | 两个清点表的 `generatedAt` 均早于本轮（09-04 / 08-26），而 live 已在 09-27~09-30 变动 | 时间戳比对 | 表旧于 live |
| C5 | 清点过程**发现并修复**一处真实边界外溢：`apps/.project-local/runs/frontend-baseline.json`（206 B，早期失败基线），已被仓库门禁 `test_nf11_manifests_present_and_apps_clean` 判为 `unexpected_apps=['.project-local']` | 读 `CLEANUP-CANDIDATES.json: resolved_during_audit[0]`；`ls apps/` | 现存 `observer` + `token-monitor`；副本在 `.project-local/runs/frontend-baseline.failed-attempt-20260930.json` |

### D. 清理候选（**仅候选，未执行**）

候选全量见 `CLEANUP-CANDIDATES.json`。摘要：

| id | 面 | 类型 | 规模/计数 | 风险 | 建议动作 |
|---|---|---|---|---|---|
| CC-1 | codex | 陈旧临时文件 | 14 个 `..codex-global-state.json*.tmp-*` | 低 | 删除（先列清单） |
| CC-2 | codex | 失效守卫 | 6 个 0 字节 `.codex-provisioning-*.guard` | 低 | 删除 |
| CC-3 | codex | 备份 | 10 个 `*.bak*`（config.toml×5、AGENTS.md×2 等） | 中 | 保留最近 1 份，余归档 |
| CC-4 | codex | 大历史库 | `logs_2.sqlite` + `thread_history_1.sqlite` ≈1.5 GiB | 中 | 走官方清理机制，勿手工删活动库 |
| HH-1 | hermes | 大状态库 | `state.db` ≈4.2 GiB | 中 | **属 OBSERVE 字段**，由用户设置决定，本项目不覆盖 |
| HH-2 | hermes | 策展产物 | `.archive`(71)、`.curator_backups`(5)、账本 1.6 MB | 低 | 归档旧条目；账本属审计证据，保留 |
| HH-3 | hermes | 自动备份 | `backups/` | 低 | 保留最近 N 份 |
| DD-1 | dsh | 历史备份 | 两套（26/14 子项，09-18/09-20 迁移期） | 中 | 新 2.0.13 稳定后归档 |
| DD-2 | dsh | 历史快照 | `.research-20260918`(3)、`.migration`(4) | 低 | 保留 `.migration` 日志，快照可归档 |
| DD-3 | dsh | 缓存 | `pnpm-store`(1) | 低 | 确认无活动安装后删（可再生） |
| RR-1 | repo | 陈旧登记 | `skills-inventory.json` 6/14 不符 | 低 | **重新生成**（非删除） |
| RR-2 | repo | 登记不全 | `plugin-inventory.json` 缺 revision | 低 | 补录（非删除） |
| RR-3 | repo | 漂移 | `model-switch` source≠live | 低 | 确认基准后单向对齐 |

### E. 重新部署映射（"重新部署软件相关内容"的通道）

| 目标面 | 源 | 唯一通道 | 受管/观察 |
|---|---|---|---|
| Hermes 受管技能（13） | `packages/client-neutral-core/skills/**` | `scripts/sync_hermes_workflow_assets.py`（备份后发布 + 同批更新 `skill-provenance.yaml` 哈希） | 受管 |
| Hermes 提示层 | `config/SOUL.md` | 同上 | 受管 |
| Hermes 启动器 | `bin/`（codex / hermes-npx / 守卫脚本） | 同上 | 受管 |
| Hermes 配置字段 | 仅 `display.language`、`display.busy_input_mode` | 同上 | **其余字段 OBSERVE，绝不覆盖**（`config-ownership.json`, `preserve_unknown: true`） |
| Codex 执行器技能（14） | `integrations/executors/codex/skills/**` | Codex 侧通道；本项目仅只读登记 | 观察 |
| DSH 桌面 | `%DSH_ROOT%\DSH Desktop.exe` + `.lnk` 三字段 | 覆盖部署脚本 + `--user-data-dir` 重 pin（ERR-087 回退见 runbook） | 受管（保留用户数据/会话/插件/技能） |

### F. 仓库一致性（审计者可公开验证）

| # | 声明 | 核验方法 | 预期 |
|---|---|---|---|
| F1 | 锚定提交存在 | `https://api.github.com/repos/DTALEX66/WORK-LAB/commits/49ce5031de5f29c7fa6e8f32f2be4052fd335650` | HTTP 200 |
| F2 | 证据文件确在该提交树内 | 直接抓 §0 的 raw URL | HTTP 200 且非空 |
| F3 | 证据未被篡改 | 用 `MANIFEST.json` 内 sha256 对每个文件重算 | 逐一相符 |
| F4 | 分支存在 | `https://api.github.com/repos/DTALEX66/WORK-LAB/branches/audit/client-asset-inventory-20260930` | HTTP 200 |

### G. 隐私与边界声明

| # | 声明 | 核验方法 | 预期 |
|---|---|---|---|
| G1 | 包内无凭据值 | 对 5 个包文件跑密钥正则（`sk-…`/`gh[pousr]_…`/`AKIA…`/`BEGIN … PRIVATE KEY`/`bearer …`） | **0 命中**（本机实测 `total_hits=0`） |
| G2 | 未读取凭据正文 | 检查清点结构：`.env`、`auth.json`、`.credentials.yaml`、`.sandbox-secrets` 仅以 `SECRET_NOT_READ` 出现 | 无对应内容字段 |
| G3 | 未读取记忆正文 | `clients.hermes.memories` 仅含名称/大小/mtime | 无正文 |
| G4 | 未访问 `E:\` `F:\` | 包内路径令牌集合仅含 `%WORKLAB_ROOT%`/`%USERPROFILE%`/`%LOCALAPPDATA%`/`%APPDATA%`/`%DSH_ROOT%` | 无 E/F 路径 |
| G5 | 清理零执行 | `CLEANUP-CANDIDATES.json` 每条 `executed: false` | 全为 false |

## 3. 审计者**无法**从公开信息验证的部分（请据此调整结论强度）

| 无法公开验证 | 原因 | 本机自证方式 |
|---|---|---|
| 元数据采集时刻之后的状态 | 客户端数据是**时点事实**，且不随仓库发布 | 每文件含 `generated_at_utc`；重跑 `client_roots_probe.py` 可比对 |
| 未上传的本地实体（如 `state.db` 4.2 GiB、Codex 92 项内容） | 体积与隐私，故意不发布 | 包内提供大小/计数/哈希前缀，不提供内容 |
| "私有面确实无凭据" | 未发布的本地文件不在包内，自然不可核 | 只能验证"包内 0 命中"（G1） |
| DSH/Codex 客户端的运行时行为 | 运行时状态不可从仓库推断 | 需用户在本机手动验证（本包不声称已验） |
| Hermes 记忆是否"过时" | 正文未读（隐私），无法判断质量 | 需用户显式授权逐文件读取后才能评估 |

## 4. 一致性自检（审计者可能发现的矛盾点，先说清）

| 可能的疑问 | 说明 |
|---|---|
| 为什么 Hermes 技能目录里有些项"0 字节"，却没被列为垃圾？ | Windows 下**目录** `st_size` 恒为 0，与内容无关。补测 `child_count` 后 26 个分类目录全部非空，故**撤回**"空目录垃圾"的初判（见 `CLEANUP-CANDIDATES.json: corrections[0]`）。 |
| 为什么 `plugin-inventory.json` 记 3 个启用插件，而 live 用户插件目录只有 1 个？ | `security-guidance`、`web-ddgs` 是 **bundled**（随 Hermes 发行版），不在用户插件目录。这是**记录口径差异，不是缺失**（见 `corrections[1]`）。 |
| `skills-inventory.json`（14 Codex 技能）与 `skill-provenance.yaml`（13 受管技能）为何数量不同？ | 二者是**不同面**：前者登记 Codex 执行器技能，后者登记部署到 Hermes Home 的受管技能。不是重复账本，无需合并。 |
| 本包是否构成"平行账本"？ | 否。本包只**引用**现有权威登记表（`config/*`、`.project/governance/*`），不定义新权威字段；`schema` 为 `workflow/neutral-asset-inventory/v1`，属证据层。 |
| 为什么把 `%USERPROFILE%` 等令牌化，而不是绝对路径？ | 中立化要求：产物需跨机器可读；同时避免把用户名写进公开仓库。本机绝对路径仅存在于 `.project-local/`（不跟踪）。 |

## 5. 复核命令（公开可做 / 本机可做）

公开（无需本机）：

```bash
curl -s https://api.github.com/repos/DTALEX66/WORK-LAB/commits/49ce5031de5f29c7fa6e8f32f2be4052fd335650 | jq -r .sha
curl -s -o /dev/null -w '%{http_code}\n' https://raw.githubusercontent.com/DTALEX66/WORK-LAB/49ce5031de5f29c7fa6e8f32f2be4052fd335650/reports/audit-evidence/assets-20260930/MANIFEST.json
```

本机（可复现清点）：

```bash
python .project-local/runs/client_roots_probe.py        # 客户端元数据
python .project-local/runs/build_asset_inventory.py      # 全量清点
python .project-local/runs/verify_inventories.py         # 清点表 vs live 哈希比对
python .project-local/runs/secret_scan_package.py        # 密钥扫描
```

## 6. 下一步（达到"清理 + 重新部署"目标所需授权）

1. **清理授权**：对 `CLEANUP-CANDIDATES.json` 逐条给出"路径 + 操作"授权（默认全拒）。
2. **登记修复授权**：重建 `config/skills-inventory.json`、补录 `plugin-inventory.json`、对齐 `model-switch`（均需确认基准侧）。
3. **重新部署授权**：经 `sync_hermes_workflow_assets.py` 重新发布受管技能/SOUL/启动器（本会话未执行）。
4. **合并授权**：本分支 → `main`（合并后本节 URL 应改用合并 SHA 以求稳定）。
