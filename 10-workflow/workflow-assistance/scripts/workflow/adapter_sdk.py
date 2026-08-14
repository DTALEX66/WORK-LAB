"""Generic Agent Adapter SDK (WLGM-100).

A version-agnostic adapter interface for agent platforms (Hermes, Codex, Claude
Code, OpenCode, Aider, Cursor, Qwen Code, ...). Adapters declare capabilities;
a missing capability returns ``unsupported``, never an empty success. Adapters
never write the canonical SQLite store directly — the evidence normalizer does
that. The SDK ships a mock adapter, a generic process adapter and a generic
heartbeat adapter.

Privacy: adapters must not read prompt/response bodies, full command lines,
environment values, credentials, or private session stores.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

CAPABILITY_NAMES = {
    "session_list",
    "run_status",
    "event_stream",
    "working_directory",
    "worktree_identity",
    "token_usage",
    "approval_state",
    "remote_execution",
    "heartbeat",
}


class CapabilityUnsupported(NotImplementedError):
    """Raised when an adapter does not implement a capability."""


@dataclass
class AdapterProbe:
    """Result of probing a platform's capabilities."""

    adapter_id: str
    installed: bool
    capabilities: set[str] = field(default_factory=set)
    evidence_level: str = "B"
    latency_seconds: float = 10.0
    privacy_surface: str = "run/session metadata only"
    detail: str = ""

    def has(self, capability: str) -> bool:
        return capability in self.capabilities

    def to_record(self) -> dict[str, Any]:
        return {
            "adapterId": self.adapter_id,
            "installed": self.installed,
            "capabilities": sorted(self.capabilities),
            "evidenceLevel": self.evidence_level,
            "latencySeconds": self.latency_seconds,
            "privacySurface": self.privacy_surface,
            "detail": self.detail,
        }


class AgentAdapter(ABC):
    """Adapter interface. Implementations must be read-only."""

    adapter_id: str = "base"

    @abstractmethod
    def probe(self) -> AdapterProbe:
        """Declare installed state and supported capabilities."""

    @abstractmethod
    def session_list(self) -> list[dict[str, Any]]:
        """Return session metadata (ids/status/times only)."""

    @abstractmethod
    def run_status(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """Return run status metadata."""

    def event_stream(self, after: str | None = None) -> list[dict[str, Any]]:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support event_stream")

    def working_directory(self, session_id: str | None = None) -> str | None:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support working_directory")

    def worktree_identity(self, session_id: str | None = None) -> dict[str, Any] | None:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support worktree_identity")

    def token_usage(self, session_id: str | None = None) -> dict[str, Any] | None:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support token_usage")

    def approval_state(self, session_id: str | None = None) -> dict[str, Any] | None:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support approval_state")

    def remote_execution(self, session_id: str | None = None) -> dict[str, Any] | None:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support remote_execution")

    def heartbeat(self) -> dict[str, Any] | None:
        raise CapabilityUnsupported(f"{self.adapter_id} does not support heartbeat")


class MockAdapter(AgentAdapter):
    """Deterministic mock for tests and offline development."""

    adapter_id = "mock"

    def __init__(self, *, capabilities: set[str] | None = None, installed: bool = True) -> None:
        self._capabilities = capabilities if capabilities is not None else {"session_list", "run_status", "heartbeat"}
        self._installed = installed

    def probe(self) -> AdapterProbe:
        return AdapterProbe(
            adapter_id=self.adapter_id,
            installed=self._installed,
            capabilities=set(self._capabilities),
            evidence_level="C",
        )

    def _require(self, capability: str) -> None:
        if capability not in self._capabilities:
            raise CapabilityUnsupported(f"{self.adapter_id} does not support {capability}")

    def session_list(self) -> list[dict[str, Any]]:
        self._require("session_list")
        return [{"sessionId": "mock-session-1", "status": "active", "updatedAt": _now()}]

    def run_status(self, session_id: str | None = None) -> list[dict[str, Any]]:
        self._require("run_status")
        return [{"executionId": "mock-exec-1", "state": "RUNNING", "sessionId": session_id or "mock-session-1"}]

    def heartbeat(self) -> dict[str, Any]:
        self._require("heartbeat")
        return {"adapterId": self.adapter_id, "ts": _now(), "state": "ALIVE"}


class GenericHeartbeatAdapter(MockAdapter):
    """Heartbeat-only adapter for platforms without run metadata."""

    adapter_id = "generic-heartbeat"

    def __init__(self, *, installed: bool = True) -> None:
        super().__init__(capabilities={"heartbeat"}, installed=installed)


class GenericProcessAdapter(AgentAdapter):
    """Process-presence adapter (evidence level D). Never fabricates RUNNING."""

    adapter_id = "generic-process"

    def __init__(self, *, image_patterns: tuple[str, ...] = (), installed: bool = True) -> None:
        self.image_patterns = image_patterns
        self._installed = installed

    def probe(self) -> AdapterProbe:
        return AdapterProbe(
            adapter_id=self.adapter_id,
            installed=self._installed,
            capabilities={"heartbeat"} if self._installed else set(),
            evidence_level="D",
            privacy_surface="process image name only",
        )

    def session_list(self) -> list[dict[str, Any]]:
        return []

    def run_status(self, session_id: str | None = None) -> list[dict[str, Any]]:
        return []

    def heartbeat(self) -> dict[str, Any] | None:
        if not self._installed:
            return None
        found: list[str] = []
        for image in self.image_patterns:
            if shutil.which(image) or _process_present(image):
                found.append(image)
        if not found:
            return None
        return {"adapterId": self.adapter_id, "ts": _now(), "processes": sorted(found), "state": "INSTANCE_PRESENT"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _process_present(image_name: str) -> bool:
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True, capture_output=True, timeout=20, check=False,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return False
    lowered = image_name.lower()
    for line in (result.stdout or "").splitlines():
        fields = [f.strip().strip('"') for f in line.split(",")]
        if fields and lowered in fields[0].lower():
            return True
    return False


def negotiate(adapter: AgentAdapter, requested: set[str]) -> dict[str, bool]:
    """Negotiate capabilities: requested -> supported? Unsupported is explicit."""
    probe = adapter.probe()
    return {capability: probe.has(capability) for capability in requested}
