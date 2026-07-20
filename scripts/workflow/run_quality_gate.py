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
            capture_output=True,
        )
        if result.returncode == 0 and "GNU bash" in result.stdout:
            return str(path)
    return None


def run(argv: list[str], *, cwd: Path = ROOT) -> int:
    printable = " ".join(argv)
    print(f"\n=== {printable} ===")
    result = subprocess.run(argv, cwd=cwd, text=True)
    print(f"=== exit {result.returncode}: {printable} ===")
    return result.returncode


def run_python(args: list[str]) -> int:
    return run([sys.executable, *args])


def tracked_python_files() -> list[str]:
    roots = [ROOT / "scripts" / "workflow", ROOT / "scripts" / "security"]
    files = [path.relative_to(ROOT).as_posix() for root in roots for path in sorted(root.glob("*.py"))]
    files.append("tests/test_workflow_governance.py")
    return files


def gate_governance() -> int:
    return run_python(["tests/test_workflow_governance.py", "-v"])


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


def gate_context_pack() -> int:
    return run_python(["scripts/workflow/build_context_pack.py", "--max-chars", "30000"])


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
    "governance": Gate("governance", "Run WorkflowGovernanceTests.", gate_governance),
    "compile": Gate("compile", "Compile repository Python workflow/security/test files.", gate_compile),
    "security": Gate("security", "Scan templates, skills, docs, scripts and README for prompt/security hazards.", gate_security),
    "context-pack": Gate("context-pack", "Generate the safe ignored Context Pack smoke artifact.", gate_context_pack),
    "shell": Gate("shell", "Parse setup.sh with bash -n when bash is available.", gate_shell),
    "powershell": Gate("powershell", "Parse setup.ps1 with PowerShell AST when pwsh/powershell.exe is available.", gate_powershell),
}

VERIFY_ORDER = ("governance", "compile", "security", "context-pack", "shell", "powershell")


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
