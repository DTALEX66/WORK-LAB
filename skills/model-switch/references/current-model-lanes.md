# Current curated Hermes model lanes

## Purpose

Use this when the user asks to clean up or switch the Hermes model list. The user's active picker is intentionally limited to three provider-family rows, but each row includes the useful version series ("几点几") for that family.

## Lanes

Hermes picker is customized via `config.yaml`:

```yaml
model_picker:
  custom_lanes:
    enabled: true
    lanes:
      - label: KIMI 系列
        provider: kimi-coding
        models:
          - kimi-k3
          - kimi-k2.7-code
          - kimi-k2.6
          - kimi-k2.5
          - kimi-for-coding
          - kimi-k2-thinking
          - kimi-k2-thinking-turbo
          - kimi-k2-turbo-preview
          - kimi-k2-0905-preview
      - label: DEEPSEEK 系列
        provider: deepseek
        models:
          - deepseek-v4-pro
          - deepseek-v4-flash
          - deepseek-chat
          - deepseek-reasoner
      - label: CHATGPT 系列
        provider: openai-codex
        models:
          - gpt-5.6-sol
          - gpt-5.6-terra
          - gpt-5.6-luna
          - gpt-5.5
          - gpt-5.3-codex-spark
          - gpt-5.6-sol-pro
          - gpt-5.6-terra-pro
          - gpt-5.6-luna-pro
```

| User-facing lane | Slash command | Hermes provider | Default model | Series shown in picker | Notes |
|---|---|---|---|---|---|
| KIMI 系列 | `/切换KIMI` | `kimi-coding` | `kimi-k3` | K3, K2.7, K2.6, K2.5, K2 thinking/turbo variants | Uses Kimi/Moonshot API key imported from CC Switch and `https://api.moonshot.cn/v1`. |
| DEEPSEEK 系列 | `/切换DP` | `deepseek` | `deepseek-v4-flash` | V4 Pro, V4 Flash, Chat, Reasoner | Direct DeepSeek official provider. |
| CHATGPT 系列 | `/切换GPT` | `openai-codex` | `gpt-5.6-sol` | 5.6 Sol/Terra/Luna, 5.5, 5.3 Codex Spark, 5.6 Pro variants | ChatGPT/Codex OAuth lane via OpenAI Codex route; requires fresh session after switch. |

## Slash quick commands

The user-facing slash forms are uppercase for readability:

```text
/切换KIMI
/切换DP
/切换GPT
```

Hermes lowercases slash command names before matching, so the stored `quick_commands` config keys are the lowercase canonical forms:

```yaml
quick_commands:
  切换kimi:
    type: alias
    target: /model kimi-k3 --provider kimi-coding
    description: 切换到 KIMI K3
  切换dp:
    type: alias
    target: /model deepseek-v4-flash --provider deepseek
    description: 切换到 DEEPSEEK V4 Flash
  切换gpt:
    type: alias
    target: /model gpt-5.6-sol --provider openai-codex
    description: 切换到 CHATGPT 5.6 Sol
```

Do not implement these as `exec` quick commands. They should be `alias` commands that route into Hermes' own `/model` handler so in-place session switching, persistence behavior, confirmation, model guardrails, and UI state all stay consistent.

## Script fallback

Run from `D:/All projects/Workflow-assistance`:

```bash
python scripts/workflow/switch_model.py status
python scripts/workflow/switch_model.py kimi
python scripts/workflow/switch_model.py deepseek
python scripts/workflow/switch_model.py gpt
```

Aliases currently supported by the script:

- `k3` → Kimi K3
- `dp` → DeepSeek V4
- `chatgpt` → ChatGPT 5.6

## Verification contract

After each switch, do not claim success from config alone. Run a small `hermes chat -q` marker through the selected lane and report the marker plus the resulting provider/model/base_url summary. The current conversation confirmed all three default lanes with markers:

- `lane-kimi-k3-ok`
- `lane-deepseek-v4-ok`
- `lane-chatgpt-56-ok`

Treat these as examples of the pattern, not permanent proof for future sessions. Re-run fresh markers when asked to verify.

## Picker caveat

Hermes `/model` and Desktop model picker are filtered by `model_picker.custom_lanes`, but the official provider/model registry is not deleted. Typed `/model <model> --provider <provider>` remains available for non-listed models when needed.
