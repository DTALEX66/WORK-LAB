---
name: model-switch
description: 在 DeepSeek 和 GPT 之间一键切换模型方案。用户说"切换DP"切到DeepSeek，"切换GPT"切到GPT。
---

# 模型方案切换

## 触发条件
用户说 **切换DP** / **切DP** / **换DP** / **切换到DeepSeek** → 切换到 DeepSeek
用户说 **切换GPT** / **切GPT** / **换GPT** / **切换到GPT** → 切换到 GPT

## 切换到 DeepSeek（用户说"切换DP"）

```bash
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.default deepseek-v4-flash
```

前提：`~/.hermes/.env` 中有 `DEEPSEEK_API_KEY`

## 切换到 GPT（用户说"切换GPT"）

```bash
hermes config set model.provider openai-codex
hermes config set model.base_url ''
hermes config set model.default gpt-5.5
```

前提：
- OpenAI Codex OAuth 已认证（`hermes auth list` 确认有 openai-codex）
- CC Switch 代理运行中（端口 7890）
- `.env` 中有 `HTTPS_PROXY=http://127.0.0.1:7890`

## 重要

切换后**必须 `/reset` 或重启 Hermes** 才能生效，当前会话不变。

## 切换后验证

```bash
hermes config | head -10   # 确认 provider 和 model
```
