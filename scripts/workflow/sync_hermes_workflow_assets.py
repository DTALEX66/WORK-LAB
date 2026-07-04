#!/usr/bin/env python
"""Synchronize portable Workflow-assistance assets with the active Hermes home.

This script intentionally avoids copying secrets or runtime state:
- never copies .env, auth.json, state.db, logs, sessions, caches
- preserves the live model/provider in Hermes config.yaml
- only merges portable MCP/plugin entries from the repo config into live config

Usage:
  python scripts/workflow/sync_hermes_workflow_assets.py --apply
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import os
import shutil
from pathlib import Path
from typing import Iterable

try:
    import yaml
except Exception as exc:  # pragma: no cover - environment guard
    raise SystemExit(f"PyYAML is required: {exc}")


def default_repo_root() -> Path:
    """Return the repository root from this script location."""
    return Path(__file__).resolve().parents[2]


def default_hermes_home() -> Path:
    """Resolve the active Hermes home without hardcoding a Windows username."""
    if os.environ.get("HERMES_HOME"):
        return Path(os.environ["HERMES_HOME"])
    if os.name == "nt":
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            return Path(localappdata) / "hermes"
        return Path.home() / "AppData" / "Local" / "hermes"
    return Path.home() / ".hermes"


def sha_tree(path: Path) -> tuple[str | None, int]:
    if not path.exists():
        return None, 0
    h = hashlib.sha256()
    count = 0
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        if any(part in {".git", "__pycache__", ".cache", "logs", "sessions"} for part in file.parts):
            continue
        h.update(file.relative_to(path).as_posix().encode("utf-8") + b"\0")
        h.update(file.read_bytes())
        count += 1
    return h.hexdigest()[:16], count


def copytree(src: Path, dst: Path, *, apply: bool) -> None:
    if not src.exists():
        print(f"skip missing tree: {src}")
        return
    print(f"copy tree: {src} -> {dst}")
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)


def copyfile(src: Path, dst: Path, *, apply: bool) -> None:
    if not src.exists():
        print(f"skip missing file: {src}")
        return
    print(f"copy file: {src} -> {dst}")
    if apply:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def backup_paths(home: Path, rels: Iterable[str], *, apply: bool) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = home / "backups" / f"workflow-assistance-sync-{stamp}"
    print(f"backup root: {backup}")
    if not apply:
        return backup
    backup.mkdir(parents=True, exist_ok=True)
    for rel in rels:
        src = home / rel
        if not src.exists():
            continue
        dst = backup / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    return backup


MERGED_MODEL_SWITCH = r'''---
name: model-switch
description: 在 Hermes 的 GPT(openai-codex OAuth + CC Switch) 与 DeepSeek 官方 Provider 之间安全切换，并诊断 Codex/CC Switch/MCP/视觉能力基线。
tags: [hermes, provider, routing, deepseek, openai, codex, proxy, cc-switch, mcp, vision]
---

# Hermes Provider 路由切换

## 触发条件

| 用户说 | 动作 |
|---|---|
| 切DP / 切换DP / 换DP / 切换到DeepSeek | 切到 DeepSeek 直连 |
| 切GPT / 切换GPT / 换GPT / 切换到GPT | 切到 GPT via openai-codex OAuth |
| 检查模型 / 工作流体检 / CC Switch 诊断 / Codex 诊断 | 运行 workflow doctor |
| 需要解释图片 / 截图 / 图表 / 视觉内容 | 优先确认或切到 GPT，因为 DeepSeek 当前视觉不可用 |

## 优先使用脚本

在 `Workflow-assistance` 仓库内，优先使用已审计脚本：

```bash
# 查看当前配置与前提
python scripts/workflow/switch_model.py status

# 切到 GPT via ChatGPT OAuth + CC Switch
python scripts/workflow/switch_model.py gpt

# 切到 DeepSeek 官方 Provider
python scripts/workflow/switch_model.py deepseek

# 全链路体检：Hermes / GPT / DeepSeek / CC Switch / Codex / MCP / Node
python scripts/workflow/hermes_workflow_doctor.py
```

切换后必须 `/reset` 或重启 Hermes；`.env` 代理变量变更必须完全重启 Hermes。

## 路由方案

### A. GPT via openai-codex OAuth + CC Switch

```text
Hermes → CC Switch(:7890) → chatgpt.com/backend-api/codex → gpt-5.5
```

前提：

- `127.0.0.1:7890` 监听；
- `hermes auth list` 中有 `openai-codex` OAuth；
- `.env` 中有：
  - `HTTPS_PROXY=http://127.0.0.1:7890`
  - `HTTP_PROXY=http://127.0.0.1:7890`

CLI 等效：

```bash
hermes config set model.provider openai-codex
hermes config set model.default gpt-5.5
hermes config set model.base_url ''
hermes config set model.api_key ''
```

### B. DeepSeek 直连

```text
Hermes → api.deepseek.com/v1 → deepseek-v4-flash
```

前提：`.env` 中有 `DEEPSEEK_API_KEY`。

CLI 等效：

```bash
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.default deepseek-v4-flash
hermes config set model.api_key ''
```

### C. Codex 本地生态

Codex 当前可作为独立编码 Agent/插件生态使用；本机常见路径：

```text
~/.codex/plugins/.plugin-appserver/codex.exe
```

如果 `codex` 不在 PATH，不要判定为未安装；先查上述路径：

```bash
~/.codex/plugins/.plugin-appserver/codex.exe --version
```

Codex 配置中可能存在 bearer token；诊断输出必须脱敏，不要复制 `auth.json` 或 `config.toml` 中的密钥字段。

### D. MCP Node wrapper

当前系统 PATH 可能有旧 Node；MCP 默认走 `bin/hermes-npx*` wrapper，优先使用 Hermes bundled Node v22：

```bash
bin/hermes-npx -y @upstash/context7-mcp@3.2.2 --help
bin/hermes-npx -y @modelcontextprotocol/server-sequential-thinking@2025.12.18 --help
bin/hermes-npx -y public-apis-mcp@0.0.10 --help
```

## 功能差异

| 功能 | DeepSeek | GPT |
|------|----------|-----|
| 文本对话 | ✅ | ✅ |
| 视觉/图片分析 | ❌ 不可用 | ✅ |
| 代码生成 | ✅ | ✅ |
| 认证方式 | `.env` 里的 `DEEPSEEK_API_KEY` | ChatGPT/Codex 订阅 OAuth（不是 `OPENAI_API_KEY`） |
| 网络要求 | 可直连或走代理 | 需 CC Switch/本地代理出海 |

**当用户需要分析图片、截图、图表时，必须切换到 GPT。** 这是切换的常见触发场景。

## CC Switch + Codex 订阅定位

用户的 GPT 通道通常是 `openai-codex` OAuth/device-code 订阅登录，不是 OpenAI API Key。排查时不要要求 `OPENAI_API_KEY`；应检查：

```bash
hermes auth list openai-codex
hermes chat -Q --provider openai-codex -m gpt-5.5 -q '只回复 OK_GPT_SUBSCRIPTION'
```

CC Switch 可能同时承担两类角色，必须区分：

1. **网络代理层**：`HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7890`，让 Hermes/Codex 访问 ChatGPT/Codex 后端。
2. **API Router/模型中转层**：本地端口如 `15721`/`5101`/`7575`，用于让 Hermes/Codex 统一路由到 GPT 订阅、DeepSeek API、Claude/Gemini 等。只有端口实际监听且 proxy enabled 时才算接管模型路由。

快速判断：

```bash
# GPT 订阅是否通
hermes chat -Q --provider openai-codex -m gpt-5.5 -q '只回复 OK_GPT_SUBSCRIPTION'

# DeepSeek API 是否通
hermes chat -Q --provider deepseek -m deepseek-v4-flash -q '只回复 OK_DEEPSEEK_API'

# CC Switch API Router 是否真的在接管，而不是只做 7890 网络代理
for port in 15721 5101 7575; do
  curl --noproxy '*' -sS --max-time 3 "http://127.0.0.1:$port/" || true
done
```

如果 GPT 与 DeepSeek 测试都通，但 API Router 端口不通，则当前结构是：Hermes 自己切换 GPT/DeepSeek，CC Switch 只负责网络代理/配置日志导入；不是统一模型路由器。

更多现场排查记录见 `references/cc-switch-codex-hermes.md`。

## 图片/视觉能力排查

当用户为了看截图/图片而切换 GPT 后：

1. 明确提醒：`/reset` 或新会话后才会使用新的 provider/model。
2. 如果用户已经发了图片但当前对话未能直接解析，先不要断言“看不了”；可以用独立 Hermes CLI 单次查询验证图片管线：

```bash
hermes chat -Q --provider openai-codex -m gpt-5.5 --image "C:\\path\\to\\image.png" -q "请说明这张截图内容，读出关键文字和状态。"
```

3. 若 CLI `--image` 能读图，说明 GPT 视觉链路可用；问题可能只在当前会话工具暴露/附件路径处理上。把 CLI 的真实输出反馈给用户，并继续处理原问题。
4. 对 UI 截图类问题，优先读取截图上的关键文字、状态、路径/按钮，再结合文件系统或配置结果判断，不要只凭界面显示下结论。

## 排查顺序

1. 运行 `python scripts/workflow/hermes_workflow_doctor.py`。
2. GPT 不通：先查 `127.0.0.1:7890`，再查代理访问 `chatgpt.com` / `auth.openai.com`。
3. DeepSeek 不通：查 `DEEPSEEK_API_KEY` 和 `api.deepseek.com`。
4. MCP 不通：查 `hermes-npx` 是否使用 Hermes bundled Node v22。
5. Codex 不通：查 `.codex/plugins/.plugin-appserver/codex.exe` 和 `127.0.0.1:15721`。

## 对话聚焦 pitfall

当用户要求解释截图/配置现象时，先直接解释图中状态和链路角色；不要跑题到工具失败史或泛泛建议。若需要说明限制，放在结论之后的“补充”。

## 安全规则

- 不输出 API Key、OAuth token、bearer token、auth.json 内容。
- 不把 ChatGPT 订阅当 OpenAI API Key。
- 不把真实 `.env` 上传仓库。
- 切换 Provider 后必须重新开会话验证，不能假装当前会话模型已变。
'''


def normalize_repo_text(repo: Path) -> None:
    for path in [repo / "skills/software-development/windows-development-environment/SKILL.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        legacy_pack_name = "hermes" + "-pack"
        text = text.replace(f'"{legacy_pack_name}"', '"Workflow-assistance"')
        text = text.replace(
            'Some Hermes deployment repos have `$PackDir = Join-Path $RepoRoot "Workflow-assistance"`\n'
            'in their setup.ps1 but the files (config/, skills/, tools/) live at the repo\n'
            'root.',
            'Some older Hermes deployment repos assumed a nested pack directory in `setup.ps1`,\n'
            'but this project keeps config/, skills/, scripts/, templates/, and bin/ at the repo root.',
        )
        path.write_text(text, encoding="utf-8")


def merge_live_config(repo: Path, home: Path, *, apply: bool) -> None:
    repo_cfg = repo / "config/config.yaml"
    live_cfg = home / "config.yaml"
    if not repo_cfg.exists() or not live_cfg.exists():
        print("skip config merge: missing repo or live config")
        return
    live_data = yaml.safe_load(live_cfg.read_text(encoding="utf-8")) or {}
    repo_data = yaml.safe_load(repo_cfg.read_text(encoding="utf-8")) or {}
    if not isinstance(live_data, dict):
        live_data = {}
    cmd_wrapper = home / "bin/hermes-npx.cmd"
    sh_wrapper = home / "bin/hermes-npx"
    wrapper = (cmd_wrapper if cmd_wrapper.exists() else sh_wrapper).as_posix()
    live_mcp = live_data.setdefault("mcp_servers", {})
    for name, cfg in (repo_data.get("mcp_servers") or {}).items():
        if not isinstance(cfg, dict):
            continue
        new = dict(cfg)
        if new.get("command") == "hermes-npx":
            new["command"] = wrapper
        live_mcp[name] = new
    plugins = live_data.setdefault("plugins", {})
    repo_enabled = (repo_data.get("plugins") or {}).get("enabled") or []
    plugins["enabled"] = list(dict.fromkeys((plugins.get("enabled") or []) + repo_enabled))
    plugins.setdefault("disabled", [])
    print("merge live config: preserve provider/model =", (live_data.get("model") or {}).get("provider"), (live_data.get("model") or {}).get("default"))
    print("merge live config: mcp =", list((live_data.get("mcp_servers") or {}).keys()))
    if apply:
        live_cfg.write_text(yaml.safe_dump(live_data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(default_repo_root()), help="Workflow-assistance repo root (default: this script's repo)")
    parser.add_argument("--home", default=str(default_hermes_home()), help="Hermes home (default: HERMES_HOME or platform default)")
    parser.add_argument("--apply", action="store_true", help="Actually write changes. Without this, print intended operations only.")
    args = parser.parse_args()

    repo = Path(args.repo)
    home = Path(args.home)
    if not repo.exists():
        raise SystemExit(f"repo not found: {repo}")
    if not home.exists():
        raise SystemExit(f"Hermes home not found: {home}")

    backup_paths(home, [
        "config.yaml",
        ".env.template",
        "bin",
        "skills/model-switch",
        "skills/software-development/python-testing",
        "skills/software-development/screenlingua",
        "skills/software-development/windows-development-environment",
        "skills/software-development/agent-workflow-fortress",
    ], apply=args.apply)

    # live -> repo for supplemental reference files only.
    # The repo's SKILL.md files are the portable canonical versions; do not
    # blindly overwrite them with shorter/stale live copies.
    for rel in [
        "skills/software-development/python-testing/references",
        "skills/software-development/windows-development-environment/references",
        "skills/software-development/agent-workflow-fortress/references",
        "skills/model-switch/references",
    ]:
        copytree(home / rel, repo / rel, apply=args.apply)

    # Merged repo model-switch wins, preserving useful live notes.
    if args.apply:
        (repo / "skills/model-switch").mkdir(parents=True, exist_ok=True)
        (repo / "skills/model-switch/SKILL.md").write_text(MERGED_MODEL_SWITCH, encoding="utf-8")
        normalize_repo_text(repo)

    # repo -> live for all portable skills + MCP wrapper.
    copytree(repo / "skills", home / "skills", apply=args.apply)
    copytree(repo / "bin", home / "bin", apply=args.apply)
    copyfile(repo / "config/.env.template", home / ".env.template", apply=args.apply)
    merge_live_config(repo, home, apply=args.apply)

    print("\nsummary hashes after planned/applied sync:")
    for label, path in [("repo skills", repo / "skills"), ("live skills", home / "skills"), ("repo bin", repo / "bin"), ("live bin", home / "bin")]:
        print(label, sha_tree(path))


if __name__ == "__main__":
    main()
