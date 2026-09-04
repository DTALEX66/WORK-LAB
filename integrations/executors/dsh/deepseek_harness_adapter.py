"""DeepSeek Harness (DSH) agent-runtime adapter (WL-DSH-001).

DSH is an *agent runtime*, not a config-layer manager. It executes agent tasks
in an isolated, task-scoped Git worktree. It never applies client config, never
completes a Task Ledger task, and never lets credentials enter the repository.

This module is the project-local contract + validation surface. It does NOT
install DSH, start a server, or touch any Hermes/Codex Home — apply is
UNSUPPORTED unless an explicit `--approved-runtime-install` task contract is
supplied (WL-DSH-030), and even then it only performs the isolated checkout.

Deployment-identity note (2026-09-02): the machine DSH switched from the
0.1.x source-checkout lineage (`deepseek-ai/deepseek-harness`, pinned commit,
`.hermes/task-runtime/deepseek-harness`) to the 2.0.x community desktop build
(`anywhere-labs/dsh-desktop`, Electron + bundled harness, web port 43120,
D-drive single entry). The legacy UPSTREAM_* pin below remains
as the HISTORICAL governance target of the retired 0.1.x isolated-checkout
contract; COMMUNITY_DESKTOP_* constants below describe the currently deployed
identity and are what detect()/observe() report against.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Immutable upstream pin (WL-DSH-010 discovery, 2026-08-15). Never float master.
# This pin is a GOVERNANCE TARGET for the retired 0.1.x isolated runtime
# checkout, NOT a claim about what is currently installed. Detected local
# installs are reported separately (WL-DLC-060: rc.5 was misreported as the
# running version). Superseded on this machine by the 2.0.x community desktop
# build (see COMMUNITY_DESKTOP_* below); kept as the historical audit record.
# ---------------------------------------------------------------------------
UPSTREAM_REPO = "deepseek-ai/deepseek-harness"
UPSTREAM_COMMIT = "47f943859bef60e4160492346772ded9b24f765a"
UPSTREAM_VERSION = "0.1.0-rc.5"  # governance target pin (historical)
UPSTREAM_LICENSE = "MIT"
# Detected on this machine (2026-08-23): local package 0.1.1-rc.2 == npm public;
# local git 4446888d (master, no origin) - source-equivalence + eligibility UNVERIFIED.
DETECTED_LOCAL_VERSION = "0.1.1-rc.2"
DETECTED_LOCAL_COMMIT = "4446888d222d8a3eb052f949e1025e5e9e69e203"
DETECTED_LOCAL_STATE = "DETECTED_LOCAL"
REQUIRED_PACKAGE_MANAGER = "pnpm@11.7.0"
REQUIRED_NODE_RANGE = "^22.19.0 || >=24.0.0"

# ---------------------------------------------------------------------------
# Community desktop build (2.0.x, deployed 2026-08-24 → 2026-08-30 verified).
# anywhere-labs/dsh-desktop = Electron shell + bundled full harness
# (dsh-plugin-desktop). This is what runs on the machine today; detect() reports
# against this identity when the legacy isolated source checkout is absent.
# ---------------------------------------------------------------------------
COMMUNITY_REPO = "anywhere-labs/dsh-desktop"
COMMUNITY_PACKAGE = "dsh-plugin-desktop"
COMMUNITY_VERSION = "2.0.5"
COMMUNITY_RELEASE_TAG = "v2.0.5"
COMMUNITY_RELEASE_TRACK = "stable"
COMMUNITY_UPSTREAM_VERSION = "0.1.2-rc.1"
COMMUNITY_BINARY_SIGNATURE = "UNSIGNED"
COMMUNITY_SOURCE_EQUIVALENCE = "UNVERIFIED"
COMMUNITY_INSTALL_DIR = Path("D:/All projects/DSH")
COMMUNITY_EXE = COMMUNITY_INSTALL_DIR / "DSH Desktop.exe"
COMMUNITY_VERSION_FILE = COMMUNITY_INSTALL_DIR / "resources" / "app.asar.unpacked" / "package.json"
COMMUNITY_WEB_PORT = 43120

# ---------------------------------------------------------------------------
# Agent-runtime contract (taskpack §4.1). These are the auditable invariants.
# ---------------------------------------------------------------------------
ADAPTER_ID = "deepseek-harness"
ADAPTER_KIND = "agent_runtime"
INSTALL_MODE = "community_desktop_release"
ENTRYPOINTS = ("desktop", "web", "headless")
NETWORK_POLICY = "loopback_only"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 43120  # community desktop web port (2.0.x); legacy 0.1.x used 3080
WORKSPACE_SCOPE = "task_scoped_git_worktree_only"
SECRETS_POLICY = "runtime_secret_only"
EXECUTION_AUTHORITY = "execute_only_no_task_completion_authority"
EXTERNAL_MUTATION = "approval_required"
PLUGIN_POLICY = "builtins_only"
UPGRADE_POLICY = "verified_release_digest + explicit_upgrade_task + compatibility_evidence"

# Forbidden host patterns: anything but loopback is rejected fail-closed.
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def runtime_root(project: Path) -> Path:
    """DSH runtime directory — git-ignored, never committed."""
    return project / ".hermes/task-runtime/deepseek-harness"


def source_dir(project: Path) -> Path:
    return runtime_root(project) / "source"


def home_dir(project: Path) -> Path:
    return runtime_root(project) / "dsh-home"


def community_version() -> str | None:
    """Read the installed community desktop version (no side effects).

    Returns e.g. \"2.0.4\" from resources/app.asar.unpacked/package.json, or
    None when the community desktop build is not present.
    """
    try:
        data = json.loads(COMMUNITY_VERSION_FILE.read_text(encoding="utf-8"))
        version = data.get("version")
        return str(version) if version else None
    except (OSError, ValueError):
        return None


def community_detected() -> dict[str, Any]:
    """Probe public application metadata without touching user DSH state."""
    exe_present = COMMUNITY_EXE.is_file()
    version = community_version()
    return {
        "present": exe_present and version is not None,
        "install": str(COMMUNITY_EXE) if exe_present else None,
        "package": COMMUNITY_PACKAGE if version else None,
        "version": version,
        "release_track": COMMUNITY_RELEASE_TRACK,
        "upstream_authority": UPSTREAM_REPO,
        "upstream_version": COMMUNITY_UPSTREAM_VERSION,
        "binary_signature": COMMUNITY_BINARY_SIGNATURE,
        "source_equivalence": COMMUNITY_SOURCE_EQUIVALENCE,
        "user_config_access": "NOT_ACCESSED",
        "web_port": COMMUNITY_WEB_PORT,
    }


# ---------------------------------------------------------------------------
# Contract validation (fail-closed). Each returns (ok, detail).
# ---------------------------------------------------------------------------
def validate_commit_pin(actual_commit: str | None) -> tuple[bool, str]:
    if not actual_commit:
        return False, "missing source commit (no checkout present)"
    if actual_commit != UPSTREAM_COMMIT:
        return False, f"commit drift: expected {UPSTREAM_COMMIT}, got {actual_commit}"
    return True, "commit pinned"


def validate_loopback(host: str, port: int) -> tuple[bool, str]:
    if host not in _LOOPBACK_HOSTS:
        return False, f"non-loopback host rejected: {host!r}"
    if not (1 <= int(port) <= 65535):
        return False, f"invalid port: {port}"
    return True, "loopback bound"


def validate_workspace_scope(workspace: Path, project: Path) -> tuple[bool, str]:
    if not workspace:
        return False, "workspace not selected"
    ws = workspace.resolve()
    proj = project.resolve()
    # The workspace must be a real Git worktree under the project, never the
    # project root itself, never a home dir, never a drive root.
    if ws == proj:
        return False, "workspace must not be the project root"
    if not ws.is_dir():
        return False, "workspace is not a directory"
    if not (ws / ".git").exists():
        return False, "workspace is not a Git worktree"
    try:
        ws.relative_to(proj)
    except ValueError:
        return False, "workspace escapes the project root"
    home = Path.home().resolve()
    try:
        home.relative_to(ws)  # workspace must not contain the user home
        return False, "workspace overlaps the user home"
    except ValueError:
        pass
    return True, "task-scoped git worktree"


def validate_receipt(receipt: dict[str, Any]) -> tuple[bool, str]:
    forbidden = (
        "api_key", "secret", "token", "password", "credential",
        "prompt", "response", "session_id", "auth",
    )
    for key, value in receipt.items():
        if any(f in key.lower() for f in forbidden):
            return False, f"receipt carries forbidden field: {key!r}"
        if isinstance(value, str) and len(value) > 4096:
            return False, f"receipt field too large: {key!r}"
    allowed = {
        "task_id", "adapter_id", "upstream_commit", "started_at", "ended_at",
        "workspace_rel", "command_kind", "approval_result", "exit_code",
        "test_summary", "file_changes", "error_kind", "evidence_hash",
    }
    unknown = set(receipt) - allowed
    if unknown:
        return False, f"receipt has unknown fields: {sorted(unknown)}"
    return True, "receipt schema ok"


def validate_secret_redaction(config_dump: dict[str, Any]) -> tuple[bool, str]:
    """A config dump must not serialize any secret-like value."""
    serialized = json.dumps(config_dump, ensure_ascii=False).lower()
    for marker in ("api_key", "api-key", "token", "password", "credential", "secret"):
        if marker in serialized:
            return False, f"config dump contains secret marker: {marker!r}"
    return True, "config dump redacted"


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------
class DeepSeekHarnessAdapter:
    adapter_id = ADAPTER_ID
    kind = ADAPTER_KIND

    def __init__(self, project: Path) -> None:
        self.project = project.resolve()

    def contract(self) -> dict[str, Any]:
        """Auditable field contract (taskpack §4.1)."""
        return {
            "schema_version": "workflow/agent-runtime-adapter/v1",
            "adapter_id": ADAPTER_ID,
            "kind": ADAPTER_KIND,
            "upstream": UPSTREAM_REPO + "@" + UPSTREAM_COMMIT,
            "upstream_version": UPSTREAM_VERSION,  # governance target pin (historical, 0.1.x retired)
            "detected_local": {
                "deployment": "community-desktop",
                "package": COMMUNITY_PACKAGE,
                "version": COMMUNITY_VERSION,
                "release_tag": COMMUNITY_RELEASE_TAG,
                "release_track": COMMUNITY_RELEASE_TRACK,
                "upstream_authority": UPSTREAM_REPO,
                "upstream_version": COMMUNITY_UPSTREAM_VERSION,
                "binary_signature": COMMUNITY_BINARY_SIGNATURE,
                "source_equivalence": COMMUNITY_SOURCE_EQUIVALENCE,
                "user_config_access": "NOT_ACCESSED",
                "install": str(COMMUNITY_EXE),
                "web_port": COMMUNITY_WEB_PORT,
                "state": "COMMUNITY_DESKTOP_VERIFIED",
                "legacy_0_1_x": {
                    "version": DETECTED_LOCAL_VERSION,
                    "commit": DETECTED_LOCAL_COMMIT,
                    "state": DETECTED_LOCAL_STATE,
                    "source_equivalence": "UNVERIFIED",
                    "eligibility": "UNVERIFIED",
                    "behavioral_verification": "NOT_EXECUTED",
                },
            },
            "license": UPSTREAM_LICENSE,
            "maturity": "developer_preview",
            "install_mode": INSTALL_MODE,
            "entrypoints": list(ENTRYPOINTS),
            "network": NETWORK_POLICY,
            "default_host": DEFAULT_HOST,
            "default_port": DEFAULT_PORT,
            "workspace_scope": WORKSPACE_SCOPE,
            "secrets": SECRETS_POLICY,
            "execution_authority": EXECUTION_AUTHORITY,
            "external_mutation": EXTERNAL_MUTATION,
            "plugin_policy": PLUGIN_POLICY,
            "upgrade_policy": UPGRADE_POLICY,
            "rollback": "stop_preserve_quarantine",
        }

    def detect(self) -> dict[str, Any]:
        """Report which DSH deployment is present (no side effects).

        Legacy 0.1.x isolated source checkout (project-local) is detected
        first; the community desktop build (2.0.x, D-drive) is the current
        deployment and is always probed alongside. User `.dsh` state is never
        read.
        """
        src = source_dir(self.project)
        installed = src.is_dir() and (src / ".git").exists()
        commit = None
        if installed:
            commit = self._git_rev_parse(src)
        ok, detail = validate_commit_pin(commit)
        community = community_detected()
        if community["present"]:
            deployment, detected_version = "community-desktop", community["version"]
        elif installed:
            deployment, detected_version = "isolated-source-checkout", UPSTREAM_VERSION
        else:
            deployment, detected_version = "none", None
        return {
            "status": "DETECTED",
            "adapter_id": self.adapter_id,
            "kind": self.kind,
            "installed": installed,
            "source_dir": str(src),
            "pinned_commit": UPSTREAM_COMMIT,
            "actual_commit": commit,
            "pin_ok": ok,
            "pin_detail": detail,
            "deployment": deployment,
            "detected_version": detected_version,
            "community_desktop": community,
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "status": "CAPABILITIES_READ",
            "adapter_id": self.adapter_id,
            "kind": self.kind,
            "entrypoints": list(ENTRYPOINTS),
            "operations": ["detect", "capabilities", "observe"],
            "unsupported_operations": ["apply", "invoke"],
            "apply": "UNSUPPORTED_WITHOUT_APPROVED_RUNTIME_INSTALL",
            "invoke": "AGENT_RUNTIME_EXECUTION_ONLY",
        }

    def observe(self) -> dict[str, Any]:
        """Read-only health/version/port readback; never reads credentials."""
        src = source_dir(self.project)
        commit = self._git_rev_parse(src) if src.is_dir() else None
        community = community_detected()
        deployment = "community-desktop" if community["present"] else "isolated-source-checkout"
        return {
            "status": "OBSERVED",
            "adapter_id": self.adapter_id,
            "kind": self.kind,
            "observed_at": None,
            "source": deployment,
            "upstream_commit": commit,
            "detected_version": community["version"],
            "health": "NOT_RUNNING",
            "port": COMMUNITY_WEB_PORT if community["present"] else None,
            "events": [],
        }

    def plan(self, request: dict[str, Any]) -> dict[str, Any]:
        """Any install/start is approval-gated; return WAITING_APPROVAL."""
        return {
            "status": "WAITING_APPROVAL",
            "plan_id": f"{self.adapter_id}-plan-{request.get('task_id', 'unknown')}",
            "task_id": request.get("task_id"),
            "approval": {"required": True, "status": "PENDING"},
            "steps": [{"action": request.get("action"), "external_mutation": True}],
            "rollback": {"available": True, "status": "READY"},
        }

    def apply(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Default: refuse. Only an approved runtime-install task may install."""
        if plan.get("approved_runtime_install") is not True:
            return {
                "status": "UNSUPPORTED",
                "plan_id": plan.get("plan_id"),
                "adapter_id": self.adapter_id,
                "reason": "apply requires an approved runtime-install task contract",
            }
        return {
            "status": "BLOCKED",
            "plan_id": plan.get("plan_id"),
            "adapter_id": self.adapter_id,
            "reason": "isolated checkout is WL-DSH-030 (approval-gated); not performed by this adapter",
        }

    def invoke(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "UNSUPPORTED",
            "adapter_id": self.adapter_id,
            "reason": "invoke is agent-runtime execution, gated by workspace scope + approval",
        }

    # --- Harness Adapter 统一接口（调研报告 Module04） ---
    def start(self, *, workspace: str | None = None, task: str | None = None) -> dict[str, Any]:
        return {
            "status": "WAITING_APPROVAL",
            "adapter_id": self.adapter_id,
            "reason": "DSH runtime start is approval-gated (external mutation)",
            "workspace": workspace,
            "task": task,
        }

    def stop(self, session_id: str | None = None) -> dict[str, Any]:
        return {
            "status": "WAITING_APPROVAL",
            "adapter_id": self.adapter_id,
            "reason": "DSH runtime stop is approval-gated",
            "session_id": session_id,
        }

    def send(self, session_id: str | None, message: str) -> dict[str, Any]:
        return {
            "status": "UNSUPPORTED",
            "adapter_id": self.adapter_id,
            "reason": "send into DSH runtime requires an approved interaction contract",
            "session_id": session_id,
        }

    def get_logs(self, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """读取项目隔离 runtime 的元数据；绝不访问用户 `.dsh` 会话。"""
        sessions_dir = home_dir(self.project) / "sessions"
        if not sessions_dir.is_dir():
            return []
        entries: list[dict[str, Any]] = []
        try:
            for sub in sorted(sessions_dir.iterdir())[:20]:
                for sfile in sub.glob("*/session.jsonl.zstd") if sub.is_dir() else []:
                    entries.append({
                        "session": sfile.parent.name,
                        "log": str(sfile),
                        "size_bytes": sfile.stat().st_size,
                        "readable": sfile.is_file(),
                    })
                    if len(entries) >= limit:
                        break
                if len(entries) >= limit:
                    break
        except OSError:
            pass
        return entries

    def export_trace(self, session_id: str | None = None) -> dict[str, Any]:
        """导出会话活动元数据 Trace（供 Observer 消费；不含 prompt/response body）。"""
        logs = self.get_logs(session_id, limit=20)
        return {
            "adapter_id": self.adapter_id,
            "kind": self.kind,
            "trace": [{"session": e["session"], "log": e["log"]} for e in logs],
            "schema": "dsh/adapter-trace/v1",
            "privacy": "metadata-only",
        }

    def rollback(self, plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "READY",
            "plan_id": plan.get("plan_id"),
            "adapter_id": self.adapter_id,
            "strategy": "stop recorded PID, preserve read-only evidence, quarantine runtime; restore previous verified commit",
        }

    def _git_rev_parse(self, src: Path) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(src), "rev-parse", "HEAD"],
                text=True, capture_output=True, timeout=15, check=False,
                encoding="utf-8", errors="replace",
            )
            if result.returncode == 0:
                return result.stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            pass
        return None


def conformance_report(project: Path) -> dict[str, Any]:
    adapter = DeepSeekHarnessAdapter(project)
    contract = adapter.contract()
    detect = adapter.detect()
    return {
        "schema_version": "workflow/agent-runtime-adapter-report/v1",
        "adapter_id": ADAPTER_ID,
        "kind": ADAPTER_KIND,
        "contract": contract,
        "detect": detect,
        "pin_ok": detect["pin_ok"],
        "loopback_policy": NETWORK_POLICY,
    }


if __name__ == "__main__":
    print(json.dumps(conformance_report(Path.cwd()), ensure_ascii=False, indent=2, default=str))
