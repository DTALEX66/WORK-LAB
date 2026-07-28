# 2026-07-28 全局 GitHub 工作流描述更新与错误总结

## 文档目的

本记录汇总本轮将 GitHub 工作流能力纳入 `Workflow-assistance` 全局治理层时发现的错误、根因、修复和真实证据。

项目定位保持为：

> **Hermes Agent + CC Switch + Codex + GitHub 的全局、可迁移、可审计工作流增强项目。**

本仓库是 portable source of truth；live Hermes Home 是运行时落点；GitHub `main` 是跨设备源代码、发布和 exact-SHA CI 证据面。

## 错误与修复

### 1. 五个 GitHub skill 原先没有仓库 source ownership

**问题：**

`github-auth`、`github-code-review`、`github-issues`、`github-pr-workflow` 和 `github-repo-management` 原先被当作 profile-live-only 能力，仓库无法完整复现、审计和 portable 部署。

**修复：**

- 将五个 `SKILL.md` 纳入 `skills/github/`；
- 移除 provenance 的 live-only 特殊排除；
- 纳入 `config/skill-provenance.yaml`；
- 纳入同步 backup、atomic apply、portable install 和治理测试；
- README 明确 13 个 skill 都是 repository-controlled portable source。

### 2. GitHub skill 的凭据指导存在不安全或不真实路径

**问题：**

复审发现旧指导可能暗示 plaintext credential store、process-local token helper、未认证 curl 写操作或从凭据文件提取 token。

**修复：**

- GitHub API 未通过已认证 `gh` 或用户批准客户端时 fail-closed；
- 不读取、复制、打印或持久化 token、`.env`、auth store、OAuth 数据库或私钥；
- 不把 token 放进 URL、命令参数、日志、Issue 或 PR body；
- one-shot HTTPS 凭据明确标为用户自行交互，不能假设会持久化；
- remote 和 commit identity 改为 repository-local，并要求用户单独授权；
- PR comment/review 使用 authenticated `gh`，不提供未认证 curl fallback。

### 3. PR review 的 changed-files 示例只读取第一页

**问题：**

默认 REST response 可能只包含前 30 个 changed files，较大的 PR 会被错误地当成完整审查。

**修复：**

改为使用 authenticated `gh api --paginate` 获取完整 changed-file 集合；单页公共 curl 只允许作为 metadata convenience，不能作为完整 review 证据。

### 4. SSH key 示例会无授权写入用户 profile

**问题：**

旧示例可能在没有确认外部路径、没有冲突检查、使用空 passphrase 的情况下写入 `~/.ssh`。

**修复：**

- 生成步骤改为 user-operated only；
- 先检查私钥和公钥是否已存在；
- 禁止覆盖现有 key；
- 不再传递空 passphrase 参数；
- 要求用户明确授权 exact path 并交互输入 passphrase；
- Agent 不读取或处理私钥。

### 5. Windows 文档混用 POSIX 命令

**问题：**

`GIT_CONFIG_GLOBAL=/dev/null`、`sed` 和 `cut` 在标准 PowerShell 中不可直接执行。

**修复：**

- clone 隔离配置补充 POSIX 与 Windows PowerShell 两套命令；
- GitHub owner/repo parsing 补充 PowerShell 版本；
- curl 示例明确要求 Git Bash，Windows 优先使用跨平台 `gh`。

### 6. 项目描述曾弱化 GitHub 的全局角色

**问题：**

仓库简介、README 和 PR 描述没有完全同步“GitHub skill ownership、provenance、portable sync、exact-SHA CI”这套定位。

**修复：**

统一更新：

- GitHub repository description；
- README 项目定位和发布状态；
- `docs/workflow/project-definition.md`；
- `TROUBLESHOOTING.md`；
- 已合并 PR #4 描述。

### 7. CI Node.js 20 弃用提示被误解为项目必须写死 Node 版本

**事实：**

GitHub Actions 曾报告 checkout/setup-python action 的 Node.js 20 runtime 弃用提示，但 Linux/Windows quality gate 均成功。

**处理原则：**

- 不在项目 workflow 中硬编码 `node-version: 24`；
- 不为了消除提示随意替换或取消 action SHA；
- 将其记录为 GitHub Actions 上游的非阻断维护提示；
- 后续若处理，应采用审阅后的自动依赖更新策略，而不是手工写死版本。

## 最终证据

- 本地全量测试：`Ran 111 tests; OK (skipped=1)`；
- 本地 quality gate：`QUALITY_GATE_PASS`；
- source/live provenance：`SKILL_PROVENANCE_PASS skills=13 live_checked=True`；
- Codex exact-tree review：GO；
- PR #4：已合并；
- feature commit：`8c96189e793c539c276cd8ed8c7927378fd312d0`；
- merge commit：`cbaa58ba93de6f776afd4bb47d02314f6aa7055a`；
- PR head Linux/Windows checks：通过；
- merge-SHA workflow `30358439937`：通过；
- merge-SHA Linux job：`90272026936`；
- merge-SHA Windows job：`90272026975`；
- merge commit tree 与 review tree：一致；
- 当前 `main == origin/main`，工作树干净；
- 未读取、输出或提交任何凭据、token、私钥或 auth store。

## 验证边界

这些证据证明本仓库、portable install、项目 bootstrap、live sync、Linux/Windows CI 和当前发布闭环通过；不等于对未来所有未知业务项目作出无条件保证。新项目仍应先执行 bootstrap、项目 runtime check、定向测试和 quality gate。
