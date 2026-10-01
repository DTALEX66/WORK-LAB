# 客户端全局资产归档（只读副本）— 供网页 GPT 审计收敛

| 项 | 值 |
|---|---|
| 包 ID | `audit-archive/20260930` |
| 生成时间（UTC） | 2026-09-30T15:25:10Z |
| 性质 | **只读复制**：源文件一律未修改；副本 LF 归一化后入库，供公开审计 |
| 规模 | 476 个文件 / 4,662,519 B（4.45 MiB） |
| 索引 | `ARCHIVE-INDEX.json`（逐文件 来源/归档路径/字节/sha256/状态/脱敏） |
| 安全 | `SECRET-SCAN-REPORT.json`（排除项、脱敏项、占位符保留项） |

## 1. 覆盖范围（逐客户端）

| 客户端 / 仓 | 复制文件 | 字节 | 复制面 |
|---|---|---|---|
| Hermes 全局层 | 363 | 3,999,010 | `SOUL.md`、`config.yaml`、`plugins/*`、`.workflow-assistance-*`、`skills/**/SKILL.md`（含 references 附属文档） |
| Codex 全局层 | 18 | 127,166 | `AGENTS.md`（含 .bak）、`config.toml`（含 .bak）、`rules/*.rules`、`skills/**/SKILL.md`、`prompts/*.md` |
| DSH（DeepSeek Harness） | 17 | 142,645 | `.dsh/settings.yaml`、`.agent-presets/*`（preset/agent/tool-bootstrap）、`llm-deepseek/files-v3.json`、`profiles/*/cordis*.yml|package.json` |
| CC Switch（LEGACY_OBSERVE） | 2 | 1,792 | `settings.json`、`model-pricing.json`（skills 目录为空） |
| Open Design 客户端 | 3 | 4,065 | `installation.json`、`launcher/channels/*`、`ws/*/apps/*/package.json` |
| OpenHuman | 4 | 35,250 | `active_user.toml`、`window_state.toml`、`users/*/config.toml(.bak)` |
| ArcheAxis-Knowledge-OS（另仓，只读） | 8 | 61,477 | `AGENTS.md`、`DIRECTORY_AUTHORITY.yaml`、`.project/governance/*.json`、`docs/decisions/*.md`、`README.md` |
| DESIGN-LAB（另仓，只读） | 61 | 291,114 | `AUTHORITY.md`、`AGENTS.md`、`.project/governance/*.json`、`docs/decisions/*.md`、`README.md` |

## 2. 明确**未**复制的内容（及其对审计结论的含义）

| 类别 | 例子 | 为何不复制 | 审计者应如何理解 |
|---|---|---|---|
| 凭据与认证 | `.env`、`.credentials.yaml`、`auth.json`、`*_auth.json`、`dev-keychain.json`、`auth-profiles.json`、`Local State` | 公开仓库不得含凭据 | **不能**据此判断『无凭据』，也不能判断其内容是否合规；这些文件只在本机存在 |
| 会话与数据库 | `state.db*`、`*.sqlite*`、`session_index.jsonl`、`*.db`、`cache.json` | 含私有会话/日志正文与体量 | 审计的是**规则面**，不是会话内容 |
| 私有记忆 | `memories/`、`memory/`、`sessions/`、`attachments/`、`storages/`、`task-board/` | 隐私边界 | 记忆/会话生成质量**不在本包可判定范围** |
| 二进制/工作区 | `node_modules/`、`workspace(s)/`、`.exe/.dll`、缓存与日志 | 非规则资产、体量不可控 | 工具链版本需另经官方渠道核对 |

## 3. 脱敏与占位符

- **脱敏**：1 个文件按模式级替换（`[REDACTED_BY_WORKLAB]`），清单见 `SECRET-SCAN-REPORT.json`；配置文件命中时**脱敏而非排除**，以保留结构供审计。
  - `hermes/skills/.archive/durable-execution-boundaries/SKILL.md`（1 处，模式：kv_secret）
- **占位符保留**：文档中的示例令牌（如 `sk-xxxx`、`<your-key>`、`example-…`）经判定为占位符后**原样保留**，因此文档可用；扫描器对其余命中一律排除（不会出现在本归档内）。
- **扫描器误报防护**：`sk-` 类规则加词边界（避免命中 `task-2026-…`），并对低熵/示例值做占位符判定。

## 4. 配额与丢弃（审计完整性说明）

- 按客户端配额裁剪共丢弃 **494** 个文件，其中 `SKILL.md` **0** 个。
- 丢弃对象为附属文档（`skills/**/references/*.md`，优先级最低者）；**所有技能主文件 SKILL.md 均已完整复制**（计数已更正 2026-10-01：hermes 363 个文件中含 **178** 个 SKILL.md，另 **8** 个在 codex 目录下，两者合计 186。此前的「hermes 186」把 codex 的 8 个错记到了 hermes 名下。）。
- 逐客户端配额：hermes=4,000,000B、codex=500,000B、dsh=600,000B、cc-switch=400,000B、open-design=400,000B、openhuman=300,000B、project-archeaxis-rules=400,000B、project-design-lab-rules=800,000B。
- 若某条结论依赖被丢弃的附属文档，请注明『依据缺失』，不要据缺口推断内容。

## 5. 校验方法（公开可做）

```bash
python - <<'PY'
import json, hashlib, urllib.request
SHA = "<证据锚定提交>"
B = f"https://raw.githubusercontent.com/DTALEX66/WORK-LAB/{SHA}/reports/audit-archive/20260930"
g = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "audit"}), timeout=60).read()
idx = json.loads(g(f"{B}/ARCHIVE-INDEX.json"))
ok = sum(1 for r in idx["files"] if r["status"].startswith("COPIED") and hashlib.sha256(g(f"{B}/{r['archive_path']}")).hexdigest() == r["sha256"])
print("verified", ok, "of", idx["totals"]["copied"])
PY
```

> 副本按仓库字节（LF）计算 sha256，下载后直接对**下载到的字节**重算即可逐字匹配。

## 6. 与主审计包的关系

- 本归档是**内容层**：把规则/规范/技能/配置的实际文本复制进来，供逐字审计。
- 主审计包 `reports/EXTERNAL-AUDIT-PACK-CLIENT-ASSETS-20260930.md` 是**索引层**：元数据清点、权威引用、覆盖判定与缺口登记。
- 两者合看：先用索引层定位声明与缺口，再用本归档核对文本是否真的支持该声明。
