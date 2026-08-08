from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, NamedTuple

ROOT = Path(__file__).resolve().parents[2]


class Gate(NamedTuple):
    name: str
    description: str
    runner: Callable[[], int]


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def usable_bash() -> str | None:
    candidates: list[str] = []
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    if os.name == "nt":
        candidates.extend(
            [
                "C:/Program Files/Git/bin/bash.exe",
                "C:/Program Files/Git/usr/bin/bash.exe",
                "C:/Program Files (x86)/Git/bin/bash.exe",
            ]
        )

    seen: set[str] = set()
    for candidate in candidates:
        path = Path(candidate)
        key = str(path).lower()
        if key in seen or not path.exists():
            continue
        seen.add(key)
        if os.name == "nt" and "windows/system32/bash.exe" in key.replace("\\", "/"):
            continue
        result = subprocess.run(
            [str(path), "--version"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if result.returncode == 0 and "GNU bash" in result.stdout:
            return str(path)
    return None


def project_runtime_environment(root: Path) -> dict[str, str]:
    runtime = (root / ".hermes" / "task-runtime").resolve()
    paths = {
        "tmp": runtime / "tmp",
        "cache": runtime / "cache",
        "logs": runtime / "logs",
        "artifacts": root / ".hermes" / "task-artifacts",
        "pip-cache": runtime / "pip-cache",
        "pycache": runtime / "pycache",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "TMP": str(paths["tmp"]),
            "TEMP": str(paths["tmp"]),
            "TMPDIR": str(paths["tmp"]),
            "XDG_CACHE_HOME": str(paths["cache"]),
            "PIP_CACHE_DIR": str(paths["pip-cache"] / "pip"),
            "UV_CACHE_DIR": str(paths["cache"] / "uv"),
            "NPM_CONFIG_CACHE": str(paths["cache"] / "npm"),
            "npm_config_cache": str(paths["cache"] / "npm"),
            "YARN_CACHE_FOLDER": str(paths["cache"] / "yarn"),
            "PLAYWRIGHT_BROWSERS_PATH": str(paths["cache"] / "playwright-browsers"),
            "CARGO_TARGET_DIR": str(paths["cache"] / "cargo-target"),
            "RUFF_CACHE_DIR": str(paths["cache"] / "ruff"),
            "MYPY_CACHE_DIR": str(paths["cache"] / "mypy"),
            "PRE_COMMIT_HOME": str(paths["cache"] / "pre-commit"),
            "PYTHONPYCACHEPREFIX": str(paths["pycache"]),
            "HERMES_PROJECT_RUNTIME_ROOT": str(runtime),
            "HERMES_PROJECT_ARTIFACTS": str(paths["artifacts"]),
            "HERMES_PROJECT_LOGS": str(paths["logs"]),
            "HERMES_KANBAN_HOME": str(root / ".hermes"),
        }
    )
    return env


def run(argv: list[str], *, cwd: Path = ROOT) -> int:
    printable = " ".join(argv)
    print(f"\n=== {printable} ===")
    result = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=project_runtime_environment(cwd),
    )
    print(f"=== exit {result.returncode}: {printable} ===")
    return result.returncode


def run_python(args: list[str]) -> int:
    return run([sys.executable, *args])


def tracked_python_files() -> list[str]:
    roots = [ROOT / "bin", ROOT / "scripts" / "workflow", ROOT / "scripts" / "security", ROOT / "tests"]
    return [path.relative_to(ROOT).as_posix() for root in roots for path in sorted(root.glob("*.py"))]


def gate_governance() -> int:
    return run_python(["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"])


def gate_compile() -> int:
    return run_python(["-m", "py_compile", *tracked_python_files()])


def gate_security() -> int:
    return run_python(
        [
            "scripts/security/scan_agent_rules.py",
            "templates",
            "skills",
            "docs",
            "scripts",
            "README.md",
        ]
    )


def gate_skill_provenance() -> int:
    return run_python(
        [
            "scripts/security/check_skill_provenance.py",
            "--manifest",
            "config/skill-provenance.yaml",
        ]
    )


def gate_context_pack() -> int:
    return run_python(["scripts/workflow/build_context_pack.py", "--max-chars", "30000"])


def gate_portable_install() -> int:
    return run_python(["scripts/workflow/verify_portable_install.py"])


def gate_client_neutral_manifest() -> int:
    return run_python(["scripts/workflow/verify_client_neutral_manifest.py"])


def gate_core_schemas() -> int:
    return run_python(["scripts/workflow/verify_core_schemas.py", "--schema-dir", "schemas/workflow"])


def gate_adapter_registry() -> int:
    return run_python(
        [
            "scripts/workflow/verify_adapter_registry.py",
            "--registry",
            "config/adapter-registry.json",
            "--schema",
            "schemas/workflow/adapter-registry.schema.json",
            "--root",
            ".",
        ]
    )


def gate_adapter_conformance() -> int:
    return run_python(["tests/test_adapter_conformance.py"])


def gate_acp_conformance() -> int:
    """NX-200: ACP protocol/capability conformance + Qwen Code pilot probe."""
    code = run_python(["scripts/workflow/verify_acp_conformance.py"])
    if code != 0:
        return code
    return run_python(["tests/test_acp_adapter.py"])


def gate_otel_mapping() -> int:
    """NX-300: OTel/OpenInference semantic mapping + privacy negative control."""
    code = run_python(["scripts/workflow/verify_otel_mapping.py"])
    if code != 0:
        return code
    return run_python(["tests/test_otel_mapping.py"])


def gate_usage_ingestion() -> int:
    """NX-310: cross-agent usage ingestion + coverage matrix."""
    code = run_python(["scripts/workflow/verify_usage_ingestion.py"])
    if code != 0:
        return code
    return run_python(["tests/test_usage_ingestion.py"])


def gate_memory_contamination() -> int:
    """NX-400: memory contamination adversarial negative controls."""
    code = run_python(["scripts/workflow/verify_memory_contamination.py"])
    if code != 0:
        return code
    return run_python(["tests/test_memory_contamination.py"])


def gate_task_ledger_replay() -> int:
    """NX-410: Task Ledger replay + side-effect consistency harness."""
    code = run_python(["scripts/workflow/verify_task_ledger_replay.py"])
    if code != 0:
        return code
    return run_python(["tests/test_task_ledger_replay.py"])


def gate_portable_install_runtime() -> int:
    if not command_exists("hermes"):
        print("\n=== FAIL portable-install-runtime: hermes CLI not found; runtime compatibility is required ===")
        return 1
    return run_python(["scripts/workflow/verify_portable_install.py", "--runtime"])


def gate_provider_inventory() -> int:
    return run_python(
        [
            "scripts/workflow/provider_health.py",
            "--config",
            "config/config.yaml",
            "--output",
            ".hermes/task-artifacts/provider-health.json",
        ]
    )


def gate_mcp_audit() -> int:
    return run_python(
        [
            "scripts/workflow/mcp_candidate_audit.py",
            "--write-template",
            ".hermes/task-artifacts/mcp-candidate-template.yaml",
        ]
    )


def gate_shell() -> int:
    bash = usable_bash()
    if not bash:
        print("\n=== SKIP shell: Git Bash / GNU bash not found ===")
        return 0
    return run([bash, "-n", "setup.sh"])


def gate_powershell() -> int:
    pwsh = shutil.which("pwsh") or shutil.which("powershell.exe")
    if not pwsh:
        print("\n=== SKIP powershell: pwsh / powershell.exe not found ===")
        return 0
    script = (
        "$tokens = $null; $errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path ./setup.ps1), [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    return run([pwsh, "-NoProfile", "-Command", script])


GATES: dict[str, Gate] = {
    "governance": Gate("governance", "Run all portable workflow and project-boundary tests.", gate_governance),
    "compile": Gate("compile", "Compile repository Python workflow/security/test files.", gate_compile),
    "skill-provenance": Gate("skill-provenance", "Validate source skill metadata, references, and provenance hashes.", gate_skill_provenance),
    "security": Gate("security", "Scan templates, skills, docs, scripts and README for prompt/security hazards.", gate_security),
    "context-pack": Gate("context-pack", "Generate the safe ignored Context Pack smoke artifact.", gate_context_pack),
    "client-neutral-manifest": Gate(
        "client-neutral-manifest",
        "Verify the client-neutral product and adapter manifest without a Hermes runtime.",
        gate_client_neutral_manifest,
    ),
    "core-schemas": Gate(
        "core-schemas",
        "Verify client-neutral ActionPlan, Domain Pack, Adapter, and evidence schemas.",
        gate_core_schemas,
    ),
    "adapter-registry": Gate(
        "adapter-registry",
        "Verify adapter provenance, risk, status, and package hash evidence.",
        gate_adapter_registry,
    ),
    "adapter-conformance": Gate(
        "adapter-conformance",
        "Run adapter conformance checks.",
        gate_adapter_conformance,
    ),
    "acp-conformance": Gate(
        "acp-conformance",
        "NX-200: ACP protocol/capability conformance + Qwen Code pilot.",
        gate_acp_conformance,
    ),
    "otel-mapping": Gate(
        "otel-mapping",
        "NX-300: OTel/OpenInference semantic mapping + privacy negative control.",
        gate_otel_mapping,
    ),
    "usage-ingestion": Gate(
        "usage-ingestion",
        "NX-310: cross-agent usage ingestion + coverage matrix.",
        gate_usage_ingestion,
    ),
    "memory-contamination": Gate(
        "memory-contamination",
        "NX-400: memory contamination adversarial negative controls.",
        gate_memory_contamination,
    ),
    "task-ledger-replay": Gate(
        "task-ledger-replay",
        "NX-410: Task Ledger replay + side-effect consistency harness.",
        gate_task_ledger_replay,
    ),
    "portable-install": Gate("portable-install", "Verify an isolated empty Hermes home can receive the package.", gate_portable_install),
    "portable-install-runtime": Gate(
        "portable-install-runtime",
        "Run the real Hermes config check against an isolated portable home.",
        gate_portable_install_runtime,
    ),
    "provider-inventory": Gate("provider-inventory", "Generate the secret-free configured provider/model inventory.", gate_provider_inventory),
    "mcp-audit": Gate("mcp-audit", "Smoke the MCP candidate audit template generator.", gate_mcp_audit),
    "shell": Gate("shell", "Parse setup.sh with bash -n when bash is available.", gate_shell),
    "powershell": Gate("powershell", "Parse setup.ps1 with PowerShell AST when pwsh/powershell.exe is available.", gate_powershell),
}

VERIFY_ORDER = (
    "governance",
    "compile",
    "skill-provenance",
    "security",
    "context-pack",
    "client-neutral-manifest",
    "core-schemas",
    "adapter-registry",
    "adapter-conformance",
    "acp-conformance",
    "otel-mapping",
    "usage-ingestion",
    "memory-contamination",
    "task-ledger-replay",
    "portable-install",
    "portable-install-runtime",
    "provider-inventory",
    "mcp-audit",
    "shell",
    "powershell",
)


def run_gate_sequence(names: tuple[str, ...]) -> int:
    for name in names:
        gate = GATES[name]
        print(f"\n### gate: {gate.name} — {gate.description}")
        exit_code = gate.runner()
        if exit_code != 0:
            print(f"\nQUALITY_GATE_FAIL gate={gate.name} exit_code={exit_code}")
            return exit_code
    print("\nQUALITY_GATE_PASS gates=" + ",".join(names))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Workflow-assistance local quality gate runner.")
    parser.add_argument(
        "gate",
        nargs="?",
        default="verify",
        choices=("verify", *GATES.keys(), "list"),
        help="Gate to run. 'verify' runs the canonical local suite.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.gate == "list":
        for name in VERIFY_ORDER:
            gate = GATES[name]
            print(f"{name}: {gate.description}")
        print("verify: Run " + ", ".join(VERIFY_ORDER))
        return 0
    if args.gate == "verify":
        return run_gate_sequence(VERIFY_ORDER)
    return run_gate_sequence((args.gate,))


if __name__ == "__main__":
    raise SystemExit(main())
