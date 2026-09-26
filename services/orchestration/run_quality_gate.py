from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, NamedTuple

ROOT = Path(__file__).resolve().parents[2]
RETIRED_ORDINARY_TESTS = {
    "test_design_token_compliance.py",
    "test_figma_sync.py",
    "test_fixture_separation.py",
    "test_renderer_contract.py",
}

# Converged module roots exposed on PYTHONPATH for unittest imports (WL-DIR migration).
MODULE_PYTHONPATH = os.pathsep.join(
    [
        str(ROOT / "services" / "authority"),
        str(ROOT / "services" / "orchestration"),
        str(ROOT / "services" / "policy"),
        str(ROOT / "services" / "receipts"),
        str(ROOT / "packages" / "client-neutral-core" / "scripts"),
        str(ROOT / "packages" / "client-neutral-core" / "bin"),
        str(ROOT / "integrations" / "executors" / "codex"),
        str(ROOT / "integrations" / "executors" / "hermes"),
        str(ROOT / "integrations" / "executors" / "dsh"),
        str(ROOT / "tests" / "workflow-assistance"),
        str(ROOT / "tests" / "ci"),
        str(ROOT / "tests" / "contracts"),
    ]
)
REQUIRED_PYTHON_MODULES = {
    "yaml": "PyYAML>=6,<7",
    "jsonschema": "jsonschema>=4,<5",
}


class Gate(NamedTuple):
    name: str
    description: str
    runner: Callable[[], int]


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def dependency_preflight() -> int:
    missing = [
        requirement
        for module, requirement in REQUIRED_PYTHON_MODULES.items()
        if importlib.util.find_spec(module) is None
    ]
    if missing:
        print(
            "QUALITY_GATE_DEPENDENCY_FAIL missing="
            + ",".join(missing)
            + " install=python -m pip install -r requirements.txt"
        )
        return 2
    print("QUALITY_GATE_DEPENDENCY_PASS modules=" + ",".join(REQUIRED_PYTHON_MODULES))
    return 0


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
    # WL-010/020/030: Runtime Boundary V2 — .project-local/ is the single runtime root
    runtime = (root / ".project-local" / "runs").resolve()
    paths = {
        "tmp": runtime / "tmp",
        "cache": runtime / "cache",
        "logs": runtime / "logs",
        "artifacts": root / ".project-local" / "artifacts",
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
            "HERMES_KANBAN_HOME": str(root / ".project-local" / "kanban"),
        }
    )
    return env


def run(argv: list[str], *, cwd: Path = ROOT, env_updates: dict[str, str] | None = None) -> int:
    printable = " ".join(argv)
    print(f"\n=== {printable} ===")
    env = project_runtime_environment(cwd)
    if env_updates:
        env.update(env_updates)
    result = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    print(f"=== exit {result.returncode}: {printable} ===")
    return result.returncode


def run_python(args: list[str], *, env_updates: dict[str, str] | None = None) -> int:
    return run([sys.executable, *args], env_updates=env_updates)


def tracked_python_files() -> list[str]:
    roots = [
        ROOT / "packages" / "client-neutral-core" / "bin",
        ROOT / "packages" / "client-neutral-core" / "scripts",
        ROOT / "services" / "orchestration",
        ROOT / "scripts" / "security",
        ROOT / "tests" / "workflow-assistance",
    ]
    return [path.relative_to(ROOT).as_posix() for root in roots for path in sorted(root.glob("*.py"))]


MANDATORY_TEST_GLOBS = ("test_*.py", "nf*.py")


def governance_test_files() -> list[str]:
    """P0-05: unified mandatory discovery — ordinary + negative-control tests.

    Both the ordinary behavior tests (`test_*.py`) and the negative-control
    tests (`nf*.py`) are mandatory and discovered dynamically from disk. There
    is no hard-coded list and no hard-coded count, so adding a new negative
    control can never silently drop out of the gate (the "compile PASS !=
    behavior PASS" gap this closes).
    """
    selected: set[str] = set()
    for glob in MANDATORY_TEST_GLOBS:
        for path in (ROOT / "tests" / "workflow-assistance").glob(glob):
            if path.name in RETIRED_ORDINARY_TESTS:
                continue
            selected.add(path.relative_to(ROOT).as_posix())
    return sorted(selected)


def mandatory_discovery_modules() -> list[str]:
    """Importable module stems for the mandatory discovery set (P0-05).

    `unittest discover` resolves `nf*` modules by name only; module-style
    (plain assert, no unittest.TestCase) files are executed as a module and
    are NOT importable as dotted test names. For those, run the file as a
    script (it self-executes via `if __name__ == "__main__"`). The runner
    therefore returns dotted stems for unittest modules and file paths for
    module-style files; `_run_governance_batch` mixes both.
    """
    members: list[str] = []
    for path in governance_test_files():
        full = ROOT / path
        stem = Path(path).stem
        module_style = not full.read_text(encoding="utf-8").find("unittest") >= 0
        if module_style:
            members.append(path)  # script-style execution
        else:
            members.append(stem)
    return members


def _run_governance_batch(members: list[str]) -> tuple[int, str]:
    """Run the mandatory test modules as one fail-closed batch.

    Returns (process exit code, combined stdout+stderr). Members that are
    dotted module names run through `python -m unittest`; members that are
    repository-relative file paths (module-style `nf*` files without
    unittest.TestCase) run as standalone scripts. A failing script fails the
    whole batch: hollow or not-run outcomes are detectable and fail closed.
    """
    pythonpath = MODULE_PYTHONPATH
    existing = os.environ.get("PYTHONPATH")
    if existing:
        pythonpath += os.pathsep + existing
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath
    unittest_modules = [member for member in members if not (ROOT / member).is_file()]
    script_files = [member for member in members if (ROOT / member).is_file()]
    combined: list[str] = []
    overall = 0
    if unittest_modules:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "-v", *unittest_modules],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        overall = result.returncode
        combined.append(result.stdout + result.stderr)
    for script in script_files:
        result = subprocess.run(
            [sys.executable, script],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0 and overall == 0:
            overall = result.returncode
        combined.append(result.stdout + result.stderr)
    return overall, "\n".join(combined)


def _git_head_identity() -> tuple[str, str]:
    """Best-effort (head commit, head tree) for failure provenance. Never raises."""
    def _git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=ROOT, capture_output=True, text=True
            ).stdout.strip()
        except Exception:
            return ""
    commit = _git("rev-parse", "HEAD") or "unknown"
    tree = _git("rev-parse", "HEAD^{tree}") or "unknown"
    return commit, tree


_GOVERNANCE_SECRET_RE = re.compile(
    r"(?:api[_-]?key|secret|password|authorization|cookie|private[_-]?key)\s*[:=]\s*\S+"
    r"|\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}"
    r"|\b(?:sk-|gh[pousr]_|xox[baprs]-)[A-Za-z0-9_-]{8,}",
    re.I,
)


def _redact_governance_text(text: str) -> str:
    """Bounded credential redaction so a failure log never carries secrets."""
    return _GOVERNANCE_SECRET_RE.sub("[REDACTED]", text)


def _governance_failure_markers(output: str) -> list[str]:
    """Which test/command failed — bounded, deduped, so a batch failure is diagnosable."""
    markers: list[str] = []
    for line in output.splitlines():
        s = line.strip()
        if (
            s.startswith("FAIL: ")
            or s.startswith("ERROR: ")
            or re.match(r"^FAILED \((?:failures|errors)=", s)
            or "AssertionError" in s
            or "ModuleNotFoundError" in s
            or "No module named" in s
        ):
            markers.append(s)
    seen: set[str] = set()
    out: list[str] = []
    for m in markers:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out[:60]


def _report_governance_failure(members: list[str], exit_code: int, output: str) -> None:
    """A3: make a governance-batch failure diagnosable without leaking secrets.

    Surfaces (1) the failing test/command names, (2) a bounded redacted error
    summary, (3) where the full redacted log was written, (4) the actual exit
    code, and (5) the commit/tree under test. The full environment is never
    dumped and credential-like values are redacted.
    """
    commit, tree = _git_head_identity()
    log_dir = ROOT / ".project-local" / "runs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "quality-gate-governance-fail.log"
        log_path.write_text(_redact_governance_text(output), encoding="utf-8")
        log_rel = log_path.relative_to(ROOT).as_posix()
    except Exception:
        log_rel = "(could not write log)"
    markers = _governance_failure_markers(output)
    print(f"QUALITY_GATE_GOVERNANCE_FAIL exit={exit_code}")
    print(f"  failing_members=[{'; '.join(markers) if markers else 'unknown-see-log'}]")
    print(f"  modules_run={len(members)}")
    print(f"  head_commit={commit} head_tree={tree}")
    print(f"  full_log={log_rel}")
    for line in _redact_governance_text(output).splitlines()[-25:]:
        print(f"    | {line}")


def _governance_execution_truth(output: str, has_unittest: bool) -> tuple[bool, str]:
    """C4: required tests ACTUALLY ran, per the tool's real semantics.

    A ``Ran N tests`` banner with N == 0, or all N skipped, is NOT execution.
    The old single-regex check (``^Ran \\d+ tests?``) matched ``Ran 0 tests``
    and reported a hollow batch as executed; every hollow outcome here fails
    closed with a named state: not-run / zero-tests / all-skipped.
    """
    if not has_unittest:
        return True, "script-only-batch(all-exit-0)"
    m = re.search(r"^Ran (\d+) tests? in", output, flags=re.MULTILINE)
    if not m:
        return False, "not-run (no unittest execution banner found)"
    total = int(m.group(1))
    if total == 0:
        return False, "zero-tests (Ran 0 tests: required tests did not execute)"
    skipped_matches = re.findall(r"skipped=(\d+)", output)
    skipped = int(skipped_matches[-1]) if skipped_matches else 0
    executed = total - skipped
    if executed <= 0:
        return False, f"all-skipped (Ran {total} tests, skipped={skipped}: nothing actually executed)"
    return True, f"executed={executed} ran={total} skipped={skipped}"


def gate_governance() -> int:
    """P0-05 + C4: run the mandatory tests, fail-closed on any hollow outcome.

    missing        != PASS  (empty mandatory set is a red flag, not a clean pass)
    not-run        != PASS  (clean exit but no execution banner)
    zero-tests     != PASS  (C4: ``Ran 0 tests`` is a hollow outcome)
    all-skipped    != PASS  (C4: skips are not executions)
    cancelled/failed != PASS (non-zero batch exit; subcommand failures presented)
    """
    members = mandatory_discovery_modules()
    if not members:
        print("QUALITY_GATE_GOVERNANCE_FAIL empty-mandatory-set")
        return 1
    exit_code, output = _run_governance_batch(members)
    has_unittest = any(not (ROOT / m).is_file() for m in members)
    executed_ok, execution = _governance_execution_truth(output, has_unittest)
    if not executed_ok:
        print(f"QUALITY_GATE_GOVERNANCE_FAIL {execution}")
        return 1
    if exit_code != 0:
        _report_governance_failure(members, exit_code, output)
        return exit_code
    print(f"QUALITY_GATE_GOVERNANCE_PASS modules={len(members)} {execution}")
    return 0


def gate_compile() -> int:
    return run_python(["-m", "py_compile", *tracked_python_files()])


def gate_security() -> int:
    return run_python(
        [
            "packages/client-neutral-core/scripts/security/scan_agent_rules.py",
            "packages/client-neutral-core/templates",
            "packages/client-neutral-core/skills",
            "integrations/executors/codex",
            "docs",
            "scripts",
            "README.md",
        ]
    )


def gate_skill_provenance() -> int:
    return run_python(
        [
            "packages/client-neutral-core/scripts/security/check_skill_provenance.py",
            "--manifest",
            "config/skill-provenance.yaml",
        ]
    )


def gate_context_pack() -> int:
    return run_python(["packages/client-neutral-core/scripts/build_context_pack.py", "--max-chars", "30000"])


def gate_portable_install() -> int:
    return run_python(["packages/client-neutral-core/scripts/verify_portable_install.py"])


def gate_client_neutral_manifest() -> int:
    return run_python(["packages/client-neutral-core/scripts/verify_client_neutral_manifest.py"])


def gate_core_schemas() -> int:
    return run_python(["packages/client-neutral-core/scripts/verify_core_schemas.py", "--schema-dir", "packages/contracts/schemas/workflow"])


def gate_adapter_registry() -> int:
    return run_python(
        [
            "packages/client-neutral-core/scripts/verify_adapter_registry.py",
            "--registry",
            "config/adapter-registry.json",
            "--schema",
            "packages/contracts/schemas/workflow/adapter-registry.schema.json",
            "--root",
            ".",
        ]
    )


def gate_capability_matrix() -> int:
    """WL3-100: capability-matrix.json stays consistent with adapter-registry.json."""
    return run_python(["packages/client-neutral-core/scripts/verify_capability_matrix.py"])


def gate_policy_coverage() -> int:
    """U17.7/27: Global Agent Policy coverage + freshness.

    Fail-closed check that the derived policy-coverage surfaces (loss reports,
    the capability-matrix coverage block, the golden projections) are fresh with
    respect to their sources (the policy SSOT + per-software extensions).
    Hand-editing a generated artifact without moving the source policy is drift.
    """
    return run_python(["scripts/ci/verify_policy_coverage.py"])


def gate_context_control_plane() -> int:
    """Context Control Plane: stable prefix, cache truth, drift guard tests."""
    return run_python(["tests/workflow-assistance/test_context_control_plane.py"])


def gate_external_libraries_index() -> int:
    """External libraries index: JSON valid + sharedRoots resolve + assets present."""
    return run_python(["packages/client-neutral-core/scripts/verify_external_libraries_index.py"])


def gate_protected_drives_consistency() -> int:
    """WS-3: E/F protected-drive truth consistent across all three governed surfaces.

    The user standing rule protects BOTH data drives (E: and F:). The gate reads the
    SSOT (config/global-agent-policy.yaml protected_drives), projects.json forbiddenRoots,
    and project-data-boundary.json (forbiddenExternalRoots + protectedDataVolume.roots)
    and fails if any surface drops a drive. In-script runner (not a test file) mirrors
    gate_external_libraries_index: deterministic, offline, stdlib-only.
    """
    return run_python(
        ["packages/client-neutral-core/scripts/verify_protected_drives_consistency.py"]
    )


def gate_three_project_boundary() -> int:
    """V2: control-plane / knowledge / design ownership split — boundary marked + gated.

    Fail-closed: proves every three-project boundary split is recorded in the SSOT,
    has a dir marker (BOUNDARY.md), an ArcheAxis seam, and a migration-manifest entry.
    In-script runner, deterministic, offline, stdlib-only.
    """
    return run_python(["scripts/ci/verify_three_project_boundary.py"])


def gate_github_delivery() -> int:
    """GitHub delivery accelerator: upload/review contracts (offline tests)."""
    return run_python(["tests/workflow-assistance/test_github_delivery.py"])


def gate_adapter_conformance() -> int:
    return run_python(["tests/workflow-assistance/test_adapter_conformance.py"])


def gate_acp_conformance() -> int:
    """NX-200: ACP protocol/capability conformance + Qwen Code pilot probe."""
    code = run_python(["packages/client-neutral-core/scripts/verify_acp_conformance.py"])
    if code != 0:
        return code
    return run_python(["tests/workflow-assistance/test_acp_adapter.py"])


def gate_otel_mapping() -> int:
    """NX-300: OTel/OpenInference semantic mapping + privacy negative control."""
    code = run_python(["packages/client-neutral-core/scripts/verify_otel_mapping.py"])
    if code != 0:
        return code
    return run_python(["tests/workflow-assistance/test_otel_mapping.py"])


def gate_usage_ingestion() -> int:
    """NX-310: cross-agent usage ingestion + coverage matrix."""
    code = run_python(["packages/client-neutral-core/scripts/verify_usage_ingestion.py"])
    if code != 0:
        return code
    return run_python(["tests/workflow-assistance/test_usage_ingestion.py"])


def gate_memory_contamination() -> int:
    """NX-400: memory contamination adversarial negative controls."""
    code = run_python(["packages/client-neutral-core/scripts/verify_memory_contamination.py"])
    if code != 0:
        return code
    return run_python(["tests/workflow-assistance/test_memory_contamination.py"])


def gate_task_ledger_replay() -> int:
    """NX-410: Task Ledger replay + side-effect consistency harness."""
    code = run_python(["packages/client-neutral-core/scripts/verify_task_ledger_replay.py"])
    if code != 0:
        return code
    return run_python(["tests/workflow-assistance/test_task_ledger_replay.py"])


def gate_portable_install_runtime() -> int:
    if not command_exists("hermes"):
        print("\n=== FAIL portable-install-runtime: hermes CLI not found; runtime compatibility is required ===")
        return 1
    return run_python(["packages/client-neutral-core/scripts/verify_portable_install.py", "--runtime"])


def gate_provider_inventory() -> int:
    return run_python(
        [
            "packages/client-neutral-core/scripts/provider_health.py",
            "--config",
            "config/config.yaml",
            "--output",
            ".project-local/artifacts/provider-health.json",
        ]
    )


def gate_mcp_audit() -> int:
    return run_python(
        [
            "packages/client-neutral-core/scripts/mcp_candidate_audit.py",
            "--write-template",
            ".project-local/artifacts/mcp-candidate-template.yaml",
        ]
    )


def gate_shell() -> int:
    bash = usable_bash()
    if not bash:
        print("\n=== SKIP shell: Git Bash / GNU bash not found ===")
        return 0
    return run([bash, "-n", "scripts/setup-workflow.sh"])


def gate_runtime_convergence() -> int:
    """WL3-400/410/500/510/600: canonical store, durable worker, collectors, SSE."""
    tests = (
        "tests/workflow-assistance/test_canonical_store.py",
        "tests/workflow-assistance/test_canonical_store_v2.py",
        "tests/workflow-assistance/test_durable_worker.py",
        "tests/workflow-assistance/test_project_registry.py",
        "tests/workflow-assistance/test_collectors.py",
        "tests/workflow-assistance/test_sse_hub.py",
        "tests/workflow-assistance/test_snapshot_sse_live.py",
        "tests/workflow-assistance/test_platform_discovery.py",
        "tests/workflow-assistance/test_skill_package_digest.py",
        "tests/workflow-assistance/test_config_ownership.py",
        "tests/workflow-assistance/test_config_coordinator.py",
        "tests/workflow-assistance/test_memory_governance.py",
        "tests/workflow-assistance/test_skill_plugin_scan.py",
        "tests/workflow-assistance/test_controlled_repro.py",
        "tests/workflow-assistance/test_model_lane_billing.py",
        "tests/workflow-assistance/test_real_adapters.py",
        "tests/workflow-assistance/test_tiered_adapters.py",
        "tests/workflow-assistance/test_swap_and_size.py",
        "tests/workflow-assistance/test_growth_watcher_collector.py",
        "tests/workflow-assistance/test_active_projects.py",
        "tests/workflow-assistance/test_product_project.py",
        "tests/workflow-assistance/test_project_identity_resolver.py",
        "tests/workflow-assistance/test_execution_anchor.py",
        "tests/workflow-assistance/test_project_candidate_discovery.py",
        "tests/workflow-assistance/test_execution_evidence.py",
        "tests/workflow-assistance/test_collector_scheduler.py",
        "tests/workflow-assistance/test_adapter_sdk.py",
        "tests/workflow-assistance/test_agent_adapters.py",
        "tests/workflow-assistance/test_fallback_collectors.py",
        "tests/workflow-assistance/test_evidence_aggregator.py",
        "tests/workflow-assistance/test_wlgm_privacy.py",
    )
    pythonpath = MODULE_PYTHONPATH
    existing = os.environ.get("PYTHONPATH")
    if existing:
        pythonpath += os.pathsep + existing
    code = run_python(
        ["-m", "unittest", "-v", *(Path(test).stem for test in tests)],
        env_updates={"PYTHONPATH": pythonpath},
    )
    if code != 0:
        return code
    # GATE-RUNTIME-CONVERGENCE acceptance (9/10 locally; #9 Tauri PENDING by toolchain).
    return run_python(
        ["packages/client-neutral-core/scripts/verify_gate_runtime_convergence.py"],
        env_updates={"PYTHONPATH": pythonpath},
    )


def gate_powershell() -> int:
    pwsh = shutil.which("pwsh") or shutil.which("powershell.exe")
    if not pwsh:
        print("\n=== SKIP powershell: pwsh/powershell.exe not found ===")
        return 0
    script = (
        "$tokens = $null; $errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path ./scripts/setup-workflow.ps1), [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    return run([pwsh, "-NoProfile", "-Command", script])


# ---------- WLGM §7 named quality gates ----------

def _run_wlgm_tests(test_names: tuple[str, ...]) -> int:
    pythonpath = MODULE_PYTHONPATH
    existing = os.environ.get("PYTHONPATH")
    if existing:
        pythonpath += os.pathsep + existing
    return run_python(
        ["-m", "unittest", "-v", *(Path(t).stem for t in test_names)],
        env_updates={"PYTHONPATH": pythonpath},
    )


def gate_project_identity_contract() -> int:
    """§7: product project identity + resolver contracts."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_product_project.py", "tests/workflow-assistance/test_project_identity_resolver.py"))


def gate_agent_adapter_readonly_contract() -> int:
    """§7: adapters are read-only; missing capabilities are explicit."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_adapter_sdk.py", "tests/workflow-assistance/test_agent_adapters.py"))


def gate_execution_state_machine() -> int:
    """§7: execution state machine has no illegal transitions."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_evidence_aggregator.py",))


def gate_collector_noninterference() -> int:
    """§7: collectors never block the writer; bounded, breakered."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_collector_scheduler.py", "tests/workflow-assistance/test_fallback_collectors.py"))


def gate_canonical_single_writer() -> int:
    """§7: canonical SQLite is the single writer; migrations recoverable."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_canonical_store_v2.py",))


def gate_observer_no_business_write() -> int:
    """§7: observer surface has no business-write path."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_wlgm_privacy.py",))


def gate_snapshot_schema_v3() -> int:
    """§7: snapshot v3 schema validation + projection contract."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_snapshot_validator.py", "tests/workflow-assistance/test_snapshot_sse_live.py"))


def gate_sse_browser_reconnect() -> int:
    """§7: persistent SSE revision + reconnect recovery semantics."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_snapshot_sse_live.py",))


def gate_field_quality_no_fabrication() -> int:
    """§7: unknown/unsupported never fabricated as 0/LIVE/exact."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_wlgm_privacy.py", "tests/workflow-assistance/test_evidence_aggregator.py"))


def gate_privacy_redaction() -> int:
    """§7: credentials/prompt bodies never enter canonical or snapshot."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_execution_evidence.py", "tests/workflow-assistance/test_wlgm_privacy.py"))


def gate_windows_project_resolution() -> int:
    """§7: Windows path case/slash containment + space-path resolution."""
    return _run_wlgm_tests(("tests/workflow-assistance/test_project_identity_resolver.py", "tests/workflow-assistance/test_project_terminal_guard.py"))


def gate_tauri_readonly_shell() -> int:
    """§7 (static): Tauri shell accepts only loopback v3 snapshot; strict CSP.

    Rust compilation requires a toolchain; this gate verifies the contract
    statically (endpoint validation source + CSP config).
    """
    errors: list[str] = []
    # The Tauri shell lives at apps/observer/src-tauri under the repository root.
    # ROOT already IS that root; the previous ROOT.parent.parent was written when
    # ROOT meant the workflow-assistance module root, and after the directory
    # migration it resolved to the parent of the repository.
    repo_root = ROOT
    tauri_root = repo_root / "apps" / "observer" / "src-tauri"
    lib = tauri_root / "src" / "lib.rs"
    if lib.is_file():
        source = lib.read_text(encoding="utf-8")
        if "/api/v1/snapshot" not in source:
            errors.append("lib.rs does not accept /api/v1/snapshot")
        if "is_loopback()" not in source:
            errors.append("lib.rs lacks loopback-only validation")
        if "url.query().is_none()" not in source or "url.fragment().is_none()" not in source:
            errors.append("lib.rs does not reject query/fragment endpoints")
        # R2 third batch: the retired /api/dashboard entry must be rejected
        # (production allow-list pattern; test assertions on .is_none() are fine).
        if re.search(r'url\.path\(\)\s*==\s*"/api/dashboard"', source):
            errors.append("lib.rs still tolerates the retired /api/dashboard entry")
    else:
        errors.append("Tauri lib.rs missing")
    conf = tauri_root / "tauri.conf.json"
    if conf.is_file():
        import json as _json

        data = _json.loads(conf.read_text(encoding="utf-8"))
        csp = data.get("app", {}).get("security", {}).get("csp")
        if not isinstance(csp, str) or "script-src" not in csp or "connect-src" not in csp:
            errors.append("tauri.conf.json CSP is not strict")
    else:
        errors.append("Tauri tauri.conf.json missing")
    if errors:
        print("TAURI_READONLY_SHELL_FAIL " + "; ".join(errors))
        return 1
    print("TAURI_READONLY_SHELL_PASS (static contract; Rust compile requires toolchain)")
    return 0


def gate_work_lab_os_canary() -> int:
    """§7: WORK-LAB self-canary; external OS-project canary stays PENDING.

    P0-7: the canary runner's exit code IS the gate verdict — a failing
    self-canary must fail the gate (no more print-FAIL-but-exit-0).

    The runner lives under services/orchestration (it moved in the directory
    migration) and imports from several module roots, so the gate supplies the
    project's standard module PYTHONPATH rather than a single directory.
    """
    return run_python([str(ROOT / "services" / "orchestration" / "canary_runner.py")],
                      env_updates={"PYTHONPATH": MODULE_PYTHONPATH})


_EXACT_SHA_CI_PROVIDER_OK = {"github-actions", "gh-actions", "github_actions", "actions"}
_EXACT_SHA_CI_LOCAL_SELF = {"local", "self", "self-filled", "manually-authored", ""}


def _is_git_sha(value: object) -> bool:
    import re as _re
    return isinstance(value, str) and bool(_re.fullmatch(r"[0-9a-fA-F]{40}", value))


def exact_sha_ci_evidence_digest(evidence: dict) -> str:
    """C3: canonical identity digest over the tamper-bearing fields of an
    exact-SHA CI evidence object. A reader recomputes this over the same core
    fields and compares to the recorded ``content_sha256`` — that is the
    integrity + read-back check, so a locally self-filled / edited success is
    detectable, not trusted on presence alone.
    """
    import hashlib
    import json as _json
    core = {
        "repository": evidence.get("repository"),
        "commit": evidence.get("commit"),
        "tree": evidence.get("tree"),
        "ci_identity": {
            "provider": str(evidence.get("ci", {}).get("provider", "")),
            "run_id": evidence.get("ci", {}).get("run_id"),
            "head_sha": evidence.get("ci", {}).get("head_sha"),
        },
        "required_checks": sorted(evidence.get("required_checks", [])),
        "jobs": sorted(
            (
                {"name": j.get("name"), "conclusion": j.get("conclusion")}
                for j in evidence.get("ci", {}).get("jobs", [])
            ),
            key=lambda d: _json.dumps(d, ensure_ascii=False, sort_keys=True),
        ),
    }
    canonical = _json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_exact_sha_ci_evidence(
    evidence: dict,
    *,
    expected_repo: str,
    expected_commit: str,
    expected_tree: str,
) -> list[str]:
    """C3: structural + truth checks an exact-SHA CI evidence object must pass
    before it counts as valid CI evidence. Returns a list of issues (empty =
    valid). Fails closed on every hollow outcome; a locally self-filled success
    is refused.
    """
    issues: list[str] = []
    if not isinstance(evidence, dict):
        return ["evidence root is not an object"]

    # schema / provenance fields
    if not evidence.get("schema_version"):
        issues.append("schema_version missing")
    if not evidence.get("observed_at"):
        issues.append("observed_at missing")
    produced_by = str(evidence.get("produced_by", "")).strip().lower()
    if produced_by in _EXACT_SHA_CI_LOCAL_SELF:
        issues.append("evidence source unverifiable (locally/self-filled success is not CI evidence)")

    # repository identity
    if str(evidence.get("repository", "")).strip() != expected_repo:
        issues.append(f"repository mismatch (evidence={evidence.get('repository')!r} expected={expected_repo!r})")

    # subject commit/tree under validation (exact-SHA binding)
    if not _is_git_sha(evidence.get("commit")):
        issues.append("commit not a 40-hex git SHA")
    elif evidence["commit"] != expected_commit:
        issues.append(f"commit mismatch (evidence={evidence['commit']} expected={expected_commit})")
    if not _is_git_sha(evidence.get("tree")):
        issues.append("tree not a 40-hex git tree")
    elif evidence["tree"] != expected_tree:
        issues.append(f"tree mismatch (evidence={evidence['tree']} expected={expected_tree})")

    # CI run/job identity
    ci = evidence.get("ci") or {}
    provider = str(ci.get("provider", "")).strip().lower()
    if provider not in _EXACT_SHA_CI_PROVIDER_OK:
        issues.append(f"ci.provider not a recognized hosted CI provider (got {provider!r})")
    if not str(ci.get("run_id", "")).strip():
        issues.append("ci.run_id missing")
    head_sha = ci.get("head_sha")
    if not _is_git_sha(head_sha):
        issues.append("ci.head_sha not a 40-hex git SHA")
    elif _is_git_sha(evidence.get("commit")) and head_sha != evidence["commit"]:
        issues.append("ci.head_sha does not equal the subject commit")

    # required checks: each must have an actual success conclusion (skipped != pass)
    required = evidence.get("required_checks") or []
    if not isinstance(required, list) or not required:
        issues.append("required_checks missing or empty")
    else:
        jobs = ci.get("jobs") or []
        by_name: dict[str, str] = {}
        for j in jobs:
            if isinstance(j, dict) and j.get("name"):
                by_name[str(j["name"]).lower()] = str(j.get("conclusion", "")).strip().lower()
        for check in required:
            key = str(check).lower()
            if key not in by_name:
                issues.append(f"required check missing in CI jobs: {check}")
            elif by_name[key] != "success":
                issues.append(f"required check not success: {check} (conclusion={by_name[key]})")

    # integrity / read-back digest
    recorded = evidence.get("content_sha256")
    recomputed = exact_sha_ci_evidence_digest(evidence)
    if not recorded or recorded != recomputed:
        issues.append("content_sha256 missing or does not match recomputed identity digest")

    return issues


def _git_origin_repo_identity() -> str:
    """Owner/name of the origin remote, or '' when it cannot be resolved.

    Accepts both ``https://host/owner/name.git`` and scp-like
    ``git@host:owner/name.git`` URL forms; anything else (no remote, local
    path remote) yields '' — an unverifiable identity fails the content check
    rather than being guessed.
    """
    try:
        out = subprocess.run(["git", "config", "--get", "remote.origin.url"],
                             cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        out = ""
    if not out:
        return ""
    url = out
    if "://" in url:
        url = url.split("://", 1)[1]
    url = url.replace(":", "/")  # scp-like git@host:owner/name
    parts = [p for p in url.split("/") if p]
    if len(parts) < 3:
        return ""
    owner, name = parts[-2], parts[-1]
    if name.endswith(".git"):
        name = name[: -4]
    return f"{owner}/{name}"


def gate_exact_sha_ci() -> int:
    """§7 + C3: exact-SHA CI evidence. required=true verifies the evidence
    file's CONTENT, not just its existence.

    P0-7: only a required context (WLGM_EXACT_SHA_CI_REQUIRED=1) fails on
    missing evidence; the ordinary local structural check stays PENDING=0.
    C3: when required, the evidence is parsed and content-validated —
    repository identity, subject commit/tree, CI run/job identity, the actual
    conclusion of every required check, a verifiable (non-self-filled)
    source, and a recomputable integrity digest. Empty file / bad JSON /
    wrong repo / wrong SHA / a failed-or-missing required check / an
    unverifiable source all fail closed.
    """
    import json as _json
    required = os.environ.get("WLGM_EXACT_SHA_CI_REQUIRED", "").strip().lower() in ("1", "true", "yes")
    if not required:
        print("EXACT_SHA_CI PENDING (requires GitHub Actions run; local gate cannot verify)")
        return 0
    evidence_path = ROOT / ".project-local" / "artifacts" / "exact-sha-ci.json"
    if not evidence_path.is_file():
        print(f"EXACT_SHA_CI_FAIL required=true evidence_missing={evidence_path}")
        return 1
    try:
        evidence = _json.loads(evidence_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"EXACT_SHA_CI_FAIL required=true evidence_invalid_json ({exc})")
        return 1
    commit, tree = _git_head_identity()
    repo = _git_origin_repo_identity()
    issues = validate_exact_sha_ci_evidence(
        evidence, expected_repo=repo, expected_commit=commit, expected_tree=tree
    )
    if issues:
        print("EXACT_SHA_CI_FAIL required=true content_invalid:")
        for item in issues:
            print(f"  - {item}")
        print(f"  (subject commit={commit[:12]} tree={tree[:12]} repo={repo or 'unresolved'})")
        return 1
    print(
        f"EXACT_SHA_CI_PASS required=true evidence={evidence_path} "
        f"commit={commit[:12]} tree={tree[:12]} checks={len(evidence.get('required_checks', []))}"
    )
    return 0


GATES: dict[str, Gate] = {
    "governance": Gate("governance", "Run all mandatory workflow + negative-control (nf*) tests in one fail-closed batch.", gate_governance),
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
    "capability-matrix": Gate(
        "capability-matrix",
        "WL3-100: verify capability-matrix.json stays consistent with the adapter registry.",
        gate_capability_matrix,
    ),
    "policy-coverage": Gate(
        "policy-coverage",
        "U17.7/27: verify Global Agent Policy coverage + freshness (loss reports, matrix block, golden projections).",
        gate_policy_coverage,
    ),
    "context-control-plane": Gate(
        "context-control-plane",
        "Context Control Plane: stable prefix + cache truth + drift guard.",
        gate_context_control_plane,
    ),
    "external-libraries-index": Gate(
        "external-libraries-index",
        "External libraries index: JSON valid + roots resolve + assets listed (content stays local).",
        gate_external_libraries_index,
    ),
    "protected-drives-consistency": Gate(
        "protected-drives-consistency",
        "WS-3: E/F protected-drive truth consistent across policy SSOT, projects.json, and project-data-boundary.json.",
        gate_protected_drives_consistency,
    ),
    "three-project-boundary": Gate(
        "three-project-boundary",
        "V2: WORK-LAB control-plane vs ArcheAxis knowledge vs DESIGN-LAB design ownership split — "
        "boundary SSOT + dir markers + ArcheAxis seams + migration manifest, fail-closed.",
        gate_three_project_boundary,
    ),
    "github-delivery": Gate(
        "github-delivery",
        "GitHub delivery accelerator: upload/review contracts (offline tests).",
        gate_github_delivery,
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
    "runtime-convergence": Gate(
        "runtime-convergence",
        "WL3 Wave 1: canonical store, durable worker, registry, collectors, SSE.",
        gate_runtime_convergence,
    ),
    "powershell": Gate("powershell", "Parse setup.ps1 with PowerShell AST when pwsh/powershell.exe is available.", gate_powershell),
    # WLGM §7 named gates.
    "project-identity-contract": Gate("project-identity-contract", "WLGM §7: product project identity + resolver contracts.", gate_project_identity_contract),
    "agent-adapter-readonly-contract": Gate("agent-adapter-readonly-contract", "WLGM §7: adapters read-only, capabilities explicit.", gate_agent_adapter_readonly_contract),
    "execution-state-machine": Gate("execution-state-machine", "WLGM §7: execution state machine transitions.", gate_execution_state_machine),
    "collector-noninterference": Gate("collector-noninterference", "WLGM §7: collectors never block the writer.", gate_collector_noninterference),
    "canonical-single-writer": Gate("canonical-single-writer", "WLGM §7: single canonical writer + recoverable migration.", gate_canonical_single_writer),
    "observer-no-business-write": Gate("observer-no-business-write", "WLGM §7: observer has no business-write path.", gate_observer_no_business_write),
    "snapshot-schema-v3": Gate("snapshot-schema-v3", "WLGM §7: snapshot v3 schema validation.", gate_snapshot_schema_v3),
    "sse-browser-reconnect": Gate("sse-browser-reconnect", "WLGM §7: persistent SSE revision + reconnect.", gate_sse_browser_reconnect),
    "field-quality-no-fabrication": Gate("field-quality-no-fabrication", "WLGM §7: unknown never fabricated.", gate_field_quality_no_fabrication),
    "privacy-redaction": Gate("privacy-redaction", "WLGM §7: credentials never enter canonical/snapshot.", gate_privacy_redaction),
    "windows-project-resolution": Gate("windows-project-resolution", "WLGM §7: Windows path resolution contract.", gate_windows_project_resolution),
    "tauri-readonly-shell": Gate("tauri-readonly-shell", "WLGM §7 (static): Tauri loopback-only + strict CSP.", gate_tauri_readonly_shell),
    "work-lab-os-canary": Gate("work-lab-os-canary", "WLGM §7: WORK-LAB self-canary (external PENDING).", gate_work_lab_os_canary),
    "exact-sha-ci": Gate("exact-sha-ci", "WLGM §7: exact-SHA CI evidence (PENDING locally).", gate_exact_sha_ci),
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
    "capability-matrix",
    "policy-coverage",
    "context-control-plane",
    "external-libraries-index",
    "protected-drives-consistency",
    "three-project-boundary",
    "github-delivery",
    "adapter-conformance",
    "acp-conformance",
    "otel-mapping",
    "usage-ingestion",
    "memory-contamination",
    "task-ledger-replay",
    "portable-install",
    "provider-inventory",
    "mcp-audit",
    "shell",
    "runtime-convergence",
    "powershell",
    # WLGM §7 named gates (after core gates).
    "project-identity-contract",
    "agent-adapter-readonly-contract",
    "execution-state-machine",
    "collector-noninterference",
    "canonical-single-writer",
    "observer-no-business-write",
    "snapshot-schema-v3",
    "sse-browser-reconnect",
    "field-quality-no-fabrication",
    "privacy-redaction",
    "windows-project-resolution",
    "tauri-readonly-shell",
    "work-lab-os-canary",
    "exact-sha-ci",
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
    # P1-3: never present an environment-limited local pass as full completion.
    print(
        "GATE_SEMANTICS STRUCTURAL_LOCAL_PASS=yes "
        "RUNTIME_CANARY_PENDING=yes(without WORKLAB_CANARY_PROJECT_ROOTS) "
        "TAURI_WINDOWS_PENDING=yes(without Rust toolchain) "
        "EXACT_SHA_CI_UNVERIFIED=yes(local only, no exact-SHA Actions run)"
    )
    return 0


# WLOSS-700: changed-files -> relevant gates.
#
# C5: this table is the LOCAL convenience mapping for `--changed` quick runs.
# The canonical gate-selection authority is the project profile consumed by
# impact_planner.build_plan / scripts/ci/emit_gate_plan.py — CI consumes the
# canonical planner, never this table. The table's path scopes are kept in
# lock-step with the current repository tree (dead paths fixed in C5); when
# the canonical planner fully retires local `--changed`, this table follows.
# Unknown (unscoped) changed paths fail safe to the full VERIFY_ORDER so a
# local convenience mapping can never drop a necessary check to save CI.
GATE_PATH_SCOPES: dict[str, tuple[str, ...]] = {
    "governance": ("tests/workflow-assistance/", "packages/client-neutral-core/scripts/", "config/"),
    "compile": ("scripts/", "packages/client-neutral-core/scripts/", "apps/observer/src/"),
    "skill-provenance": ("packages/client-neutral-core/skills/", "integrations/executors/codex/skills/", "config/skill-provenance.yaml"),
    "security": ("config/", "integrations/executors/codex/", "README.md", "docs/"),
    "context-pack": ("packages/client-neutral-core/scripts/build_context_pack.py",),
    "client-neutral-manifest": ("packages/client-neutral-core/workflow-manifest.yaml",),
    "core-schemas": ("packages/contracts/schemas/", "config/"),
    "adapter-registry": ("config/adapter-registry.json", "packages/client-neutral-core/scripts/verify_adapter_registry.py"),
    "capability-matrix": ("config/capability-matrix.json", "packages/client-neutral-core/scripts/verify_capability_matrix.py"),
    "policy-coverage": ("config/global-agent-policy.yaml", "config/loss-reports/", "config/capability-matrix.json", "config/adapter-registry.json", "services/policy/policy_projection.py", "integrations/executors/codex/codex_policy_renderer.py", "integrations/executors/hermes/hermes_policy_renderer.py", "integrations/executors/codex/codex-policy-extension.yaml", "integrations/executors/hermes/hermes-policy-extension.yaml", "integrations/executors/codex/global-guidance.md", "config/SOUL.md", "scripts/ci/verify_policy_coverage.py", "tests/workflow-assistance/test_policy_projection.py"),
    "context-control-plane": ("packages/client-neutral-core/scripts/context_control_plane.py", "packages/client-neutral-core/scripts/context_bundle.py", "packages/client-neutral-core/scripts/context_drift_guard.py"),
    "external-libraries-index": (".project/governance/external-libraries-index.json", "packages/client-neutral-core/scripts/verify_external_libraries_index.py"),
    "github-delivery": ("packages/client-neutral-core/scripts/github_common.py", "packages/client-neutral-core/scripts/github_upload_accelerator.py", "packages/client-neutral-core/scripts/github_review_accelerator.py"),
    "adapter-conformance": ("packages/client-neutral-core/scripts/adapter_conformance.py", "tests/workflow-assistance/test_adapter_conformance.py"),
    "acp-conformance": ("integrations/executors/codex/acp_adapter.py", "tests/workflow-assistance/test_acp_adapter.py"),
    "otel-mapping": ("services/receipts/otel_mapper.py", "tests/workflow-assistance/test_otel_mapping.py"),
    "usage-ingestion": ("services/receipts/usage_ingestion.py", "tests/workflow-assistance/test_usage_ingestion.py"),
    "memory-contamination": ("packages/client-neutral-core/scripts/memory_contamination.py",),
    "task-ledger-replay": ("packages/client-neutral-core/scripts/task_ledger_replay.py",),
    "portable-install": ("packages/client-neutral-core/scripts/verify_portable_install.py",),
    "provider-inventory": ("config/config.yaml",),
    "mcp-audit": ("packages/client-neutral-core/scripts/mcp_candidate_audit.py",),
    "shell": ("scripts/setup-workflow.sh",),
    "runtime-convergence": ("packages/client-neutral-core/scripts/canonical_store.py", "services/orchestration/durable_worker.py", "packages/client-neutral-core/scripts/collectors.py", "services/orchestration/sse_hub.py", "tests/workflow-assistance/"),
    "powershell": ("scripts/setup-workflow.ps1",),
    "project-identity-contract": ("packages/client-neutral-core/scripts/product_project.py", "packages/client-neutral-core/scripts/project_identity_resolver.py", "tests/workflow-assistance/test_product_project.py", "tests/workflow-assistance/test_project_identity_resolver.py"),
    "agent-adapter-readonly-contract": ("packages/client-neutral-core/scripts/adapter_sdk.py", "integrations/executors/hermes/hermes_adapter.py", "integrations/executors/codex/codex_adapter.py"),
    "execution-state-machine": ("services/receipts/evidence_aggregator.py",),
    "collector-noninterference": ("services/orchestration/collector_scheduler.py", "packages/client-neutral-core/scripts/process_collector.py", "packages/client-neutral-core/scripts/git_collector.py"),
    "canonical-single-writer": ("packages/client-neutral-core/scripts/canonical_store.py", "tests/workflow-assistance/test_canonical_store_v2.py"),
    "observer-no-business-write": ("services/receipts/execution_evidence.py", "apps/observer/web/", "tests/workflow-assistance/test_wlgm_privacy.py"),
    "snapshot-schema-v3": ("packages/client-neutral-core/scripts/snapshot_api.py", "packages/client-neutral-core/scripts/snapshot_validator.py", "tests/workflow-assistance/test_snapshot_validator.py", "tests/workflow-assistance/test_snapshot_sse_live.py"),
    "sse-browser-reconnect": ("services/orchestration/sse_revision.py", "services/orchestration/live_gate.py", "tests/workflow-assistance/test_snapshot_sse_live.py"),
    "field-quality-no-fabrication": ("services/orchestration/live_gate.py", "services/receipts/evidence_aggregator.py", "tests/workflow-assistance/test_evidence_aggregator.py"),
    "privacy-redaction": ("services/receipts/execution_evidence.py", "packages/client-neutral-core/scripts/canonical_store.py", "tests/workflow-assistance/test_execution_evidence.py", "tests/workflow-assistance/test_wlgm_privacy.py"),
    "windows-project-resolution": ("packages/client-neutral-core/scripts/project_identity_resolver.py", "packages/client-neutral-core/bin/hermes-project-terminal-guard.py", "tests/workflow-assistance/test_project_identity_resolver.py", "tests/workflow-assistance/test_project_terminal_guard.py"),
    "tauri-readonly-shell": ("apps/observer/src-tauri/", "services/orchestration/sidecar_endpoint.py", "tests/workflow-assistance/test_sidecar_endpoint.py"),
    "work-lab-os-canary": ("services/orchestration/canary_runner.py",),
    "exact-sha-ci": (),
}


# C5: recognized fast-gate-only surface prefixes. A change that ONLY hits
# these runs the always-on fast sanity gate (``compile``) and nothing else.
# These are surfaces with no dedicated gate of their own: the fast compile
# scope plus the workflow-definition surface (``.github``), whose contract is
# covered by the fast compile check. A change that hits NEITHER a gate's
# scope NOR any fast-only prefix is genuinely unknown and must fail safe to
# the full canonical verify (never skip necessary checks to save CI).
_FAST_GATE_ONLY_PREFIXES: frozenset[str] = frozenset(
    {
        "scripts/",
        "packages/client-neutral-core/scripts/",
        "apps/observer/src/",
        ".github/",
    }
)


def _is_known_fast_gate_only(scope: str) -> bool:
    s = scope.replace("\\", "/")
    return any(s == p or s.startswith(p) for p in _FAST_GATE_ONLY_PREFIXES)


def _is_uncovered(path: str) -> bool:
    """True when the path matches no gate's scope (genuinely unknown)."""
    s = path.replace("\\", "/")
    for gate, scopes in GATE_PATH_SCOPES.items():
        if gate not in GATES:
            continue
        for scope in scopes:
            scope_n = scope.replace("\\", "/")
            if s == scope_n or s.startswith(scope_n.rstrip("/") + "/"):
                return False
    return True


def select_gates_for_changed(changed_paths: list[str]) -> tuple[str, ...]:
    """Return the gates relevant to the changed paths (WLOSS-700).

    Paths may be monorepo-relative (packages/client-neutral-core/...) or
    module-relative (scripts/...); both forms are matched.

    C5 safety fallback: a change that matches no gate's scope at all is
    unknown — instead of silently running nothing we escalate to the full
    canonical verify (``VERIFY_ORDER``) so necessary checks are never
    dropped. Changes that only hit the fast-gate-only surface (``.github``
    workflows, the fast ``compile`` sanity scope) keep their pinned fast
    selection.
    """
    variants: list[str] = []
    for raw in changed_paths:
        path = raw.replace("\\", "/")
        variants.append(path)
        # Module-relative variant (strip the monorepo module prefix).
        for prefix in ("packages/client-neutral-core/", "apps/observer/"):
            if path.startswith(prefix):
                variants.append(path[len(prefix):])
    selected: set[str] = set()
    for gate, scopes in GATE_PATH_SCOPES.items():
        if gate not in GATES:
            continue
        for scope in scopes:
            scope_n = scope.replace("\\", "/")
            if any(v == scope_n or v.startswith(scope_n.rstrip("/") + "/") for v in variants):
                selected.add(gate)
                break
    # Always include the fast sanity gates for any change.
    selected |= {"compile"}
    # C5: unknown changes (no recognized scope) fail safe to the full suite.
    # Pinned fast-gate-only surface (.github workflows) is NOT unknown.
    if not all(
        not _is_uncovered(v) or _is_known_fast_gate_only(v)
        for v in variants
    ):
        return tuple(VERIFY_ORDER)
    order = [name for name in VERIFY_ORDER if name in selected]
    return tuple(order)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Workflow-assistance local quality gate runner.")
    parser.add_argument(
        "gate",
        nargs="?",
        default="verify",
        choices=("verify", *GATES.keys(), "list"),
        help="Gate to run. 'verify' runs the canonical local suite.",
    )
    parser.add_argument(
        "--changed",
        default=None,
        metavar="PATHS",
        help="Comma-separated changed file paths; runs only the relevant gates (WLOSS-700).",
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
    preflight = dependency_preflight()
    if preflight != 0:
        return preflight
    if args.changed:
        changed = [p.strip() for p in args.changed.split(",") if p.strip()]
        selected = select_gates_for_changed(changed)
        print(f"WLOSS_700 changed={len(changed)} files -> gates={','.join(selected) or 'none'}")
        if not selected:
            return 0
        return run_gate_sequence(selected)
    if args.gate == "verify":
        return run_gate_sequence(VERIFY_ORDER)
    return run_gate_sequence((args.gate,))


if __name__ == "__main__":
    raise SystemExit(main())
