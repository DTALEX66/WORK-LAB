# 用户环境画像（User Environment Profile）

## 目的

跨机器保留 Hermes 与 Codex 的用户级配置与技能清单，避免换电脑后从零积攒。本画像以**中立、无密**形态随增强模块仓库留存：只记录非密配置值与技能清单，所有凭据值统一为 `[REDACTED]`。

## 内容

机器可读画像：`config/user-environment-profile.json`（tracked，由导出器生成）：

```text
hermes:
  config_yaml      Hermes config.yaml 的非密键值（秘密键值脱敏为 [REDACTED]）
  env_key_names    ~/.env 的键名清单（绝不含值）
  skills           用户级 skills 清单（143 个：名称 + description + 路径）
codex:
  config_toml      Codex config.toml 的非密键值（provider/model 名保留，base_url/凭据脱敏）
  rules            $CODEX_HOME/rules/*.rules 清单
  agents_skills    ~/.agents/skills 技能清单（10 个 workflow-assistance-*）
paths              hermes_home / codex_home / agents_skills_root
```

技能内容本身不入画像 —— 技能文件随各自运行时存在；增强模块的 10 个 skill 已随本模块仓库携带。

## 刷新

```bash
python 10-workflow/workflow-assistance/scripts/workflow/user_profile_export.py
```

导出器读取真实用户 Home，重写 `config/user-environment-profile.json`（脱敏 fail-closed：发现未脱敏秘密值则拒绝写入）。生成后 `git diff --check` + 提交。

## 新机器恢复

1. 克隆 WORK-LAB → `python 10-workflow/workflow-assistance/scripts/workflow/sync_codex_global_assets.py apply`（部署 10 个 skill + 规则 + guidance + 3 个 config 缺省字段）；
2. 读取画像：`config/user-environment-profile.json` 对照各运行时配置（键名 + 脱敏值，提示哪些位置需要重新填写凭据）；
3. Hermes：按画像重建非密配置项（display/terminal 等），凭据按 `env_key_names` 键名重新填入；
4. Codex：provider/model 名照画像；base_url/密钥等 [REDACTED] 项重新配置。

## 安全边界

- 导出器只读用户 Home，绝不读取会话库、记忆库、keychain、auth 存储；
- 任何键名含 api_key/token/secret/password/credential/auth/connection/base_url 等 → 值 `[REDACTED]`；值匹配 sk-/gh_/AKIA/私钥/Bearer/URL 内嵌凭据 → `[REDACTED]`；
- 画像可安全提交（无凭据值）；发现未脱敏值导出器直接失败。
