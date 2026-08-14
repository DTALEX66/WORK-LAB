"""Codex read-only adapter (WLGM-090).

Correlates local, worktree and remote tasks without depending on Codex private
session stores. Model layers separately:

- local execution (process/worktree presence, level D);
- remote/cloud execution (declared unsupported unless an official surface is
  probed);
- GitHub PR/CI (owned by the CI watcher, not this adapter).

The adapter never modifies Codex config, model routing or approval mode, and
never reads ``~/.codex/sessions`` (or Windows equivalents) as an official
source. A sandbox that denies workspace reads is reported as
``VISIBILITY_DENIED``, never as a stopped project.
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Any

from adapter_sdk import AdapterProbe, AgentAdapter, CapabilityUnsupported


class CodexAdapter(AgentAdapter):
    adapter_id = "codex"

    def __init__(self, *, codex_bin: str | None = None) -> None:
        self.codex_bin = codex_bin if codex_bin is not None else shutil.which("codex")

    def probe(self) -> AdapterProbe:
        installed = bool(self.codex_bin)
        capabilities: set[str] = {"heartbeat"} if installed else set()
        detail = "codex not found on PATH"
        if installed:
            version = self._version()
            if version:
                detail = f"codex CLI present ({version})"
        return AdapterProbe(
            adapter_id=self.adapter_id,
            installed=installed,
            capabilities=capabilities,
            evidence_level="B",
            privacy_surface="process/worktree identity only; private sessions never read",
            detail=detail,
        )

    def _version(self) -> str | None:
        if not self.codex_bin:
            return None
        try:
            result = subprocess.run(
                [self.codex_bin, "--version"],
                text=True, capture_output=True, timeout=15, check=False,
                encoding="utf-8", errors="replace",
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return (result.stdout or result.stderr).strip()[:64] if result.returncode == 0 else None

    def session_list(self) -> list[dict[str, Any]]:
        raise CapabilityUnsupported("codex official session list is not available without a private store; process/worktree fallback only")

    def run_status(self, session_id: str | None = None) -> list[dict[str, Any]]:
        raise CapabilityUnsupported("codex run status requires an official event surface; none probed")

    def heartbeat(self) -> dict[str, Any]:
        return {"adapterId": self.adapter_id, "ts": __import__("adapter_sdk")._now(), "state": "ALIVE" if self.codex_bin else "UNAVAILABLE"}
