# Hermes Provider + MCP Workflow Hardening Pattern

Use this reference when upgrading the portable Hermes/Codex/CC Switch workflow pack or similar agent runtime repos.

## Durable pattern

1. **Do not trust system Node for MCP packages.** If Hermes ships a bundled Node runtime, prefer a small wrapper such as `hermes-npx` that calls the bundled `npx` first and falls back to PATH only when unavailable. This prevents default MCP config from depending on whatever Node version happens to be installed globally.
2. **Default-enable only low-permission MCPs after real connection tests.** A package `--help` smoke test is not enough once it enters live config; also run `hermes mcp test <server>` and verify tool discovery.
3. **Browser automation MCPs are candidates, not defaults, when Hermes already has native `browser` / `computer_use`.** Default enabling should be reserved for clear net-new value because it broadens the permission surface.
4. **Provider switching must be verified both ways.** After adding a switcher script, run a real one-shot model call on the fallback provider and then switch back to the preferred provider with a second real one-shot call. Finish with a status readout proving the desired provider is restored.
5. **Doctor scripts should be redacted and runnable by users.** They may report provider/config/auth presence, ports, MCP health, and tool versions, but must not print API keys, OAuth tokens, bearer tokens, raw `.env`, or `auth.json` contents.
6. **Deployment scripts should rewrite portable placeholders into local absolute commands.** Repo config may use a portable placeholder like `command: hermes-npx`; setup scripts should copy the wrapper into Hermes home and rewrite live config to the local executable path.

## Verification matrix

Run, at minimum:

```bash
python3 -m py_compile scripts/workflow/*.py scripts/security/*.py
python3 - <<'PY'
from pathlib import Path
import yaml
yaml.safe_load(Path('config/config.yaml').read_text(encoding='utf-8'))
print('yaml OK')
PY
bash -n setup.sh
python3 scripts/security/scan_agent_rules.py templates skills docs scripts bin
hermes mcp list
hermes mcp test public-apis
hermes mcp test sequential-thinking
hermes mcp test context7
python3 scripts/workflow/hermes_workflow_doctor.py
python3 scripts/workflow/switch_model.py deepseek
hermes chat -q 'Reply exactly: deepseek-ok' --provider deepseek -m deepseek-v4-flash
python3 scripts/workflow/switch_model.py gpt
hermes chat -q 'What model are you? Reply model name only.' --provider openai-codex -m gpt-5.5
python3 scripts/workflow/switch_model.py status
git diff --check
```

Adjust provider names/models to the target deployment, but preserve the two-way switch verification and final restoration step.
