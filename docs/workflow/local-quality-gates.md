# Local Quality Gates

Workflow-assistance uses a small Python runner as the canonical local quality gate. The optional `Justfile` is only a convenience wrapper; just is not a required dependency for the portable pack.

## Canonical command

```bash
python scripts/workflow/run_quality_gate.py verify
```

`verify` runs, in order:

1. `governance` — `python tests/test_workflow_governance.py -v`
2. `compile` — `python -m py_compile` for workflow scripts, security scripts and governance tests
3. `security` — `python scripts/security/scan_agent_rules.py templates skills docs scripts README.md`
4. `context-pack` — `python scripts/workflow/build_context_pack.py --max-chars 30000`
5. `shell` — `bash -n setup.sh` when Git Bash / GNU bash is available
6. `powershell` — parse `setup.ps1` with PowerShell AST when `pwsh` or `powershell.exe` is available

The runner stops at the first failing gate and prints:

```text
QUALITY_GATE_FAIL gate=<name> exit_code=<code>
```

When every gate passes it prints:

```text
QUALITY_GATE_PASS gates=governance,compile,security,context-pack,shell,powershell
```

## Individual gates

```bash
python scripts/workflow/run_quality_gate.py list
python scripts/workflow/run_quality_gate.py governance
python scripts/workflow/run_quality_gate.py compile
python scripts/workflow/run_quality_gate.py security
python scripts/workflow/run_quality_gate.py context-pack
python scripts/workflow/run_quality_gate.py shell
python scripts/workflow/run_quality_gate.py powershell
```

## Optional Justfile shortcuts

If `just` is installed:

```bash
just verify
just governance
just compile
just security
just context-pack
just shell
just powershell
```

If `just` is missing, use the Python runner directly. Do not install `just` automatically from setup scripts or CI just to run this pack.

## Platform behavior

- `shell` skips cleanly when Git Bash / GNU bash is unavailable. On Windows it avoids the `C:\Windows\System32\bash.exe` WSL shim because that can fail on machines without a WSL distro.
- `powershell` prefers `pwsh` when present and falls back to `powershell.exe`; it only parses `setup.ps1`, it does not execute setup.
- `context-pack` writes to the Git-ignored project artifact path `.hermes/task-artifacts/context-pack.md`.
- No gate reads `.env`, `auth.json`, session DBs, logs, caches or live Hermes secrets.

## CI relationship

GitHub Actions should call the same runner instead of duplicating local commands. This keeps the visible local command and CI gate aligned while still allowing platform-specific skips for unavailable shell tooling.
