# Hermes Token Monitor Desktop

Windows-first Tauri 2 desktop dashboard for local token usage observability.

## What it measures

The app reads user-selected local `.json` and `.jsonl` files/directories and only counts explicit usage fields such as `input_tokens`, `output_tokens`, `prompt_tokens`, `completion_tokens`, `cached_input_tokens`, `reasoning_tokens`, and `total_tokens`.

It does not estimate tokens from text length, read credentials, call provider APIs, or upload logs.

## Provider display

Models and explicit provider/source labels are grouped as:

- `GPT / Codex`
- `DeepSeek`
- `Kimi`
- `Other`

The default dashboard is **本次新增**: after monitoring starts, it subtracts the initial historical snapshot and shows only usage added while the monitor is running. Use **历史累计** to inspect all recognized records in the selected sources.

The window uses an Apple-inspired light desktop surface (SF Pro/system font stack, white translucent cards, quiet gray hierarchy, blue primary action) and can be hidden to the Windows notification area. Closing the window hides it; use the tray menu to show it again or exit.

## Development

```powershell
npm install
npm run build
npm run tauri dev
```

The source field accepts multiple paths separated by semicolons. Use only local session or usage exports; do not select credential, OAuth, Cookie, or `.env` files.

`dist/`, `node_modules/`, `src-tauri/target/`, and generated `src-tauri/gen/` files are ignored by the repository. `package-lock.json` and `src-tauri/Cargo.lock` are source dependency locks and may be reviewed for submission.
