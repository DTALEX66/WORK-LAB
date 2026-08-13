# 2026-08-13 审计预防控制交接

> 范围：供应链安装控制、受管配置的最小写入合同、Hermes 受管资产路径围栏、以及全局/项目所有权边界。
>
> 证据等级：本文只记录本仓库候选树的本地验证结论。GitHub PR、exact-SHA CI、合并、远端 `main` 和跨机器状态必须在实际发生后单独回读，不能由本文预先声称。

## 当前结论

WORK-LAB 是官方软件之上的受控工作流基线与恢复层，不是日常软件升级器、第二 runtime/provider、用户认证存储或任意项目的全局写入控制面。

- 官方软件升级由官方渠道、用户或组织 IT 决定；升级后仅可在明确授权下恢复合同明确拥有的受管资产。
- 模型、Provider、base URL、认证、MCP、插件、会话、私有 memory、Desktop 内部状态和未知字段不由本模块自动写入。
- 项目 `AGENTS.md`、项目规则和项目 Skills 由目标项目自身拥有。全局合同仅可观察，不得由全局同步器 apply 或替换。
- 用户层受管 apply 必须经过发现、最小 write set、目标/机器/计划 digest 绑定、明确审批与回读；空计划不得写入。

## 本轮控制

### 供应链

GitHub Actions 中的 Python 安装按每个真实 shell invocation 检查：

- Action 必须固定为完整 commit SHA 并有版本注释；
- pip install 必须有真实 `--require-hashes` token；
- 只能引用唯一的 `10-workflow/workflow-assistance/requirements.lock`；
- `;`、`&&`、`||`、`|`、注释伪造和混合 requirements 都会逐调用 fail-closed；
- shell 的 `backslash-newline` 依 POSIX 语义直接删除，而不凭空加入空格。因此命令名跨续行也会被识别和审查。

独立只读供应链复审对先前候选给出 GO；其记录的 Medium 是注释或引号中的 `pip install` 文字可能触发保守误报，不是绕过或降级。合同边界收敛后必须对新的精确 tree 重新复审，旧 GO 不可外推。

### 配置与受管资产

- 配置协调器保留已有值（包括 `null`），未知/不适用字段进入 quarantine，未进入 write set。
- Hermes 同步在计划、staging、promotion、readback、rollback、prune 和 retired asset 路径对 symlink/junction/reparse、越界及所有权不明 fail-closed。
- retired asset 只有在证明项目受管所有权和预期内容时才可删除；否则保留并阻断普通同步。
- Codex overlay writer 在函数层复核当前计划、目标、已审阅 digest、授权和读回，防止直接调用绕过。

## 已验证（本地候选）

在本次最后一次合同边界收敛后，至少应保留以下命令的实际输出：

```text
PYTHONDONTWRITEBYTECODE=1 python 10-workflow/workflow-assistance/tests/test_config_coordinator.py
PYTHONDONTWRITEBYTECODE=1 python 10-workflow/workflow-assistance/tests/test_config_ownership.py
PYTHONDONTWRITEBYTECODE=1 python 10-workflow/workflow-assistance/scripts/workflow/verify_config_ownership.py
PYTHONDONTWRITEBYTECODE=1 python tests/ci/test_supply_chain.py
PYTHONDONTWRITEBYTECODE=1 python scripts/ci/verify_supply_chain.py
PYTHONDONTWRITEBYTECODE=1 python scripts/ci/verify_error_ledger.py
PYTHONDONTWRITEBYTECODE=1 python tests/ci/test_error_ledger.py
PYTHONDONTWRITEBYTECODE=1 python scripts/ci/generate_current_state.py --check-current --root .
PYTHONDONTWRITEBYTECODE=1 python 10-workflow/workflow-assistance/scripts/workflow/run_quality_gate.py verify
git diff --cached --check
```

## 仍需在交付时验证

1. 对最终**精确暂存 tree**完成独立只读复审；任何修改均使旧审查结论失效。
2. 授权提交后，记录本地 commit SHA 和 push 后的 `origin/<branch>` SHA。
3. PR 创建后，只接受该 PR head SHA 的 CI 结论。
4. squash merge 后，分别回读 GitHub `main`、`origin/main`、本地 `main` 的 commit 与 tree；SHA 相同不替代工作树状态检查。
5. 最后确认工作树干净、分支已同步；不将本机验证外推为其它电脑的 runtime 验收。

## 2026-08-13 本机续交接（未上传）

> 本节记录工作树事实，不是远端交付声明。写入时 `HEAD` 与 `origin/main`
> 均为 `72d55c12271d9d711118d7ea16586b19465b897b`；本地分支为
> `fix/audit-prevention-controls-20260813`。候选尚未 commit、push 或创建 PR。

旧的严格只读审查发现两个与当前实现路径相关的 High，已在本机工作树做最小
修复，但这批修复尚未暂存，因此早前的 tree、质量门和独立审查均不得外推：

1. `scripts/ci/verify_supply_chain.py` 现在递归发现所有非 `.git` / `.hermes`
   子树中的 `.github/workflows/*.yml|*.yaml`；模块内
   `10-workflow/workflow-assistance/.github/workflows/governance.yml` 两处 Python
   安装改为使用唯一 canonical hash lock。
2. Hermes `plugins` 已按 ownership registry 的 `OBSERVE` 合同收敛：移除 portable
   config 的 plugins 声明、兼容 recipe 的 `plugins.enabled` 管理策略，以及同步器的
   plugin merge、enable/disable 和 retirement 写入路径；用户现有 plugins 必须原样保留。
3. 增加两个回归：嵌套项目 workflow 的无 hash pip 安装必须被 verifier 拒绝；隔离
   Hermes config merge 后用户 `plugins` 字段保持不变。

本机对上述未暂存修复实际运行并通过：

```text
PYTHONDONTWRITEBYTECODE=1 python tests/ci/test_supply_chain.py
# 11 tests OK; SUPPLY_CHAIN_PASS workflows=2 actions=10 source=pinned-sha
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover \
  -s 10-workflow/workflow-assistance/tests -p 'test_action_plan_sync.py'
# 10 tests OK
PYTHONDONTWRITEBYTECODE=1 python 10-workflow/workflow-assistance/tests/test_config_ownership.py
# 10 tests OK
PYTHONDONTWRITEBYTECODE=1 python 10-workflow/workflow-assistance/scripts/workflow/verify_config_ownership.py
# CONFIG_OWNERSHIP_PASS
```

移交者必须在自己的工作树先确认这些改动已实际存在，再显式暂存所有预期文件，
重新生成 `CURRENT_STATE`，运行完整质量门，记录新的 `git write-tree`，并对该精确
tree 进行独立只读审查。仅在审查 GO 后，才可按单独授权执行 commit、push、PR 与
exact-SHA CI。另一台电脑不会因本文件或本机本地工作树自动获得这些未上传改动。

## 后续维护约束

- 全局 guidance/rules 保持轻量；项目专属规则进入项目自身的 `AGENTS.md`、rules 或 Skills。
- 全量质量门用于合同、安全、同步器和交付；日常低风险变更先运行受影响模块检查。
- 环境未配备的 canary root 或 Rust/Tauri 工具链应报告为 `PENDING`，不得为了绿灯扫描其它项目或默认安装软件。
- 不读取、输出、归档或同步凭据、`.env` 正文、Token、私有会话、memory、prompt/response 正文。
