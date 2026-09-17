# Local Quality Gates

Workflow-assistance uses the Python runner as the canonical local quality gate.
The optional `Justfile` is only a convenience wrapper; just is not a required dependency.

## Canonical command

```bash
python services/orchestration/run_quality_gate.py verify
```

The runner first performs a fail-fast dependency preflight from
`requirements.txt`, then runs these client-neutral gates in order. CI resolves
the same direct constraints through hash-locked `requirements.lock` with
`--require-hashes`; regenerate the lock deliberately when direct constraints
change.

1. `governance`
2. `compile`
3. `skill-provenance`
4. `security`
5. `context-pack`
6. `client-neutral-manifest`
7. `core-schemas`
8. `adapter-registry`
9. `adapter-conformance`
10. `acp-conformance`
11. `otel-mapping`
12. `usage-ingestion`
13. `memory-contamination`
14. `task-ledger-replay`
15. `portable-install`
16. `provider-inventory`
17. `mcp-audit`
18. `shell`
19. `runtime-convergence`
20. `powershell`

`portable-install-runtime` remains registered as an explicit optional Adapter
compatibility gate. It is not part of default `verify`, and core CI must not
install or pin Hermes solely to make it run.

The runner stops on the first failure with
`QUALITY_GATE_FAIL gate=<name> exit_code=<code>` and prints the complete gate
list only after every required gate passes as
`QUALITY_GATE_PASS gates=<ordered-required-gates>`.

## Individual gates

Use `python services/orchestration/run_quality_gate.py list` to discover the current
registry, then run a gate by name, for example:

```bash
python services/orchestration/run_quality_gate.py adapter-conformance
python services/orchestration/run_quality_gate.py runtime-convergence
python services/orchestration/run_quality_gate.py portable-install-runtime
```

## Platform and data boundaries

- `shell` and `powershell` perform syntax/AST checks and explicitly skip when
  their supported tool is unavailable.
- Generated reports stay under ignored `.project-local/artifacts/` or
  `.project-local/runs/` paths.
- `portable-install` uses only an isolated empty Home.
- `portable-install-runtime` requires an already capability-discovered runtime.
- No gate reads `.env`, auth stores, session databases, prompts/responses,
  private memory bodies, credentials, or live secrets.

GitHub Actions invokes the same runner after installing `requirements.txt` so
local and CI contracts remain aligned. Local PASS is not exact-SHA CI evidence.
