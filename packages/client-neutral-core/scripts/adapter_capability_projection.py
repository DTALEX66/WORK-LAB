"""Adapter capability projection: one card per managed client, seven layers per card (P1-03 / F1).

The blueprint's capability ladder (WORK-LAB-BLUEPRINT-20261006.md §6) names seven layers that are each a
different claim, and none of them proves the next one:

    Registered -> Installed -> Loaded/Connected -> Qualified -> Enabled for Task
                 -> Native Projection -> Observed in Execution

Before this module the ladder existed only in prose, so a UI could call a manifest entry "installed" or an
adapter "native verified". This module is the single place that decides a layer's state, and the rules that
keep it honest are:

* a layer is MET only from a named source that carries that layer's own evidence; anything else is
  NOT_PROBED with the reason that says what is missing — never blank, never inherited from the layer
  below, never promoted because a sibling succeeded;
* `INSTALLED` never follows from a version string. It follows only from a software install-identity row
  whose location status is RESOLVED (U17), and the card says which status it read;
* the registry's own `detection.evidence_state` is carried through unchanged. A version readback is not a
  package-hash check, so an UNVERIFIED declaration must not be laundered into a pass by projection;
* per-client facts come from `config/capability-matrix.json#clients[]` (status, write policy, risk,
  runtime adapter, config-ownership default). `config/capability-conformance.json` describes PROTOCOLS, so
  it is attached as protocol status and never renamed into a per-client capability list;
* where the registry and the matrix state different verb sets for the same client, both are shown and the
  drift is named. Choosing one as truth is an owner decision, not a projection's.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LAYER_ORDER: tuple[str, ...] = (
    "REGISTERED",
    "INSTALLED",
    "LOADED_CONNECTED",
    "QUALIFIED",
    "ENABLED_FOR_TASK",
    "NATIVE_PROJECTION",
    "OBSERVED_IN_EXECUTION",
)

CONFORMANCE_PROTOCOLS = ("acp", "skills", "mcp")

# Why the upper layers are unprobed, stated once so every card says the same thing about the same gap.
UNPROBED_REASON = {
    "LOADED_CONNECTED": "没有已接通的原生会话读回：adapter 的 invoke/observe 动词仍返回 NOT_IMPLEMENTED（AG-06/G06）",
    "QUALIFIED": "没有逐能力资格判定：资格需要真实调用与产物，目前没有可引用的判定记录",
    "ENABLED_FOR_TASK": "没有任务级启用记录：派发未实现，没有任何任务把该客户端启用为执行器",
    "NATIVE_PROJECTION": "没有原生投影：原生侧状态（会话/模型/子代理）尚未进入 v3 快照合同",
    "OBSERVED_IN_EXECUTION": "没有执行中观察：需要真实执行链上的 receipt/readback 关联到该客户端",
}


def _layer(layer: str, state: str, *, evidence_level: str, source: str | None, reason: str) -> dict[str, Any]:
    return {
        "layer": layer,
        "state": state,
        "evidenceLevel": evidence_level,
        "source": source,
        "reason": reason,
    }


# `location_status` is the fail-closed enum of workflow/software-installation-identity/v1 (U17/P0-07).
# Each value means something different for the INSTALLED layer, and conflating them is how a card starts
# claiming an installation that was never measured — or reporting "unprobed" for a real measured absence.
INSTALLED_MET_STATUSES = frozenset({"SINGLE_VERIFIED"})
INSTALLED_ABSENT_STATUSES = frozenset({"NOT_INSTALLED"})
# `scripts/audit/executor_live_probe.py` answers on this machine. Both of these prove an entry point
# exists and ran (VERSION_MOVED proves existence while showing the registry's version string is stale —
# that is drift to display, not a reason to call the client uninstalled).
ENTRY_LIVE_STATUSES = frozenset({"LIVE_VERIFIED", "VERSION_MOVED"})


def _card_probe(client_id: str, live_probe: dict[str, Any] | None, probed_at: str | None) -> dict[str, Any] | None:
    """The entry-point readback as its own fact: an executable answered, which is not a live session.

    Field names follow `scripts/audit/executor_live_probe.py`'s record (`state`, `command`, `detail`,
    `probe.exitCode`, `probe.outputSha256`) — the output is kept as a digest of the version line, not the
    line itself, because a card travels into a read-only projection.
    """
    if not live_probe:
        return None
    inner = live_probe.get("probe") or {}
    command = [str(part) for part in (live_probe.get("command") or [])]
    return {
        "status": str(live_probe.get("state") or "UNKNOWN"),
        "entryPoint": command[0] if command else None,
        "argv": command,
        "exitCode": inner.get("exitCode"),
        "outputDigest": inner.get("outputSha256"),
        "detail": live_probe.get("detail"),
        "probedAt": probed_at,
    }


def _installed_layer(client_id: str, software_rows: list[dict[str, Any]],
                     live_probe: dict[str, Any] | None = None) -> dict[str, Any]:
    """Installed comes from a measured install identity or a live entry readback, never a version string."""
    probe_status = str((live_probe or {}).get("state") or "")
    if probe_status in ENTRY_LIVE_STATUSES:
        entry = (live_probe or {}).get("command") or []
        return _layer("INSTALLED", "MET", evidence_level="INTEGRATED",
                      source=f"executor_live_probe[{client_id}] {probe_status} "
                             f"entry={entry[0] if entry else 'UNKNOWN'}",
                      reason="本机对该入口做过一次版本读回并成功返回（版本漂移另列，不影响「存在且可执行」）")
    row = next((item for item in software_rows
                if str(item.get("softwareId") or "") in (client_id, client_id.replace("-", "_"),
                                                          client_id.replace("_", "-"))), None)
    if row is None:
        return _layer("INSTALLED", "NOT_PROBED", evidence_level="NO_EVIDENCE", source=None,
                      reason="软件安装身份投影里没有该客户端的行（发现模块不可用或未登记）")
    location_status = str(row.get("locationStatus") or "UNKNOWN")
    handle = (f"software[{client_id}] locationStatus={location_status} "
              f"root={row.get('installRoot') or 'UNKNOWN'}")
    if location_status in INSTALLED_MET_STATUSES and row.get("installRoot"):
        return _layer("INSTALLED", "MET", evidence_level="INTEGRATED", source=handle,
                      reason="身份发现实测到唯一已验证安装位置")
    if location_status in INSTALLED_ABSENT_STATUSES:
        return _layer("INSTALLED", "NOT_SUPPORTED", evidence_level="INTEGRATED", source=handle,
                      reason="身份发现实测本机未安装（这是测出来的缺失，不是没测）")
    return _layer("INSTALLED", "NOT_PROBED", evidence_level="NO_EVIDENCE", source=handle,
                  reason=f"安装位置状态为 {location_status}：未落到已验证位置，所以不声称已安装")


def _matrix_client(matrix: dict[str, Any], client_id: str) -> dict[str, Any] | None:
    for entry in matrix.get("clients") or []:
        if str(entry.get("id") or "") == client_id:
            return entry
    for entry in matrix.get("manifest_only_clients") or []:
        if str(entry.get("id") or "") == client_id:
            return entry
    return None


def project_adapter_capabilities(*, registry: dict[str, Any], conformance: dict[str, Any],
                                matrix: dict[str, Any],
                                software_rows: list[dict[str, Any]] | None = None,
                                live_probe_rows: list[dict[str, Any]] | None = None,
                                live_probe_at: str | None = None,
                                observed_at: str | None = None) -> list[dict[str, Any]]:
    """Build one card per declared adapter. Absent evidence stays NOT_PROBED with its reason."""
    software_rows = software_rows or []
    probes = {str(row.get("adapter") or row.get("clientId") or ""): row for row in (live_probe_rows or [])}
    cards: list[dict[str, Any]] = []
    for entry in registry.get("entries") or []:
        client_id = str(entry.get("id") or "")
        if not client_id:
            continue
        provenance = entry.get("provenance") or {}
        readback = provenance.get("version_readback") or {}
        detection = entry.get("detection") or {}
        matrix_entry = _matrix_client(matrix, client_id)
        probe = probes.get(client_id)
        probe_card = _card_probe(client_id, probe, live_probe_at)

        registry_operations = sorted(str(op) for op in entry.get("operations") or [])
        matrix_operations = sorted(str(op) for op in (matrix_entry or {}).get("operations") or [])

        layers = [
            _layer("REGISTERED", "MET", evidence_level="SYNTHETIC",
                   source=f"config/adapter-registry.json#entries[id={client_id}]",
                   reason="登记来自仓库声明文件，是声明不是探测"),
            _installed_layer(client_id, software_rows, probe),
        ]
        layers += [
            _layer(name, "NOT_PROBED", evidence_level="NO_EVIDENCE", source=None,
                   reason=UNPROBED_REASON[name])
            for name in LAYER_ORDER[2:]
        ]

        cards.append({
            "clientId": client_id,
            "displayName": entry.get("display_name") or client_id,
            "supportLevel": entry.get("support_level") or "UNKNOWN",
            "declaredOperations": registry_operations,
            "matrixOperations": matrix_operations,
            "operationsDrift": bool(matrix_entry) and registry_operations != matrix_operations,
            "registryStatus": (matrix_entry or {}).get("registry_status") or "NOT_IN_MATRIX",
            "writePolicy": (matrix_entry or {}).get("writes") or "UNKNOWN",
            "risk": (matrix_entry or {}).get("risk") or "UNKNOWN",
            "runtimeAdapter": (matrix_entry or {}).get("runtime_adapter"),
            "configOwnershipDefault": (matrix_entry or {}).get("config_ownership_default"),
            "clientNote": (matrix_entry or {}).get("note") or entry.get("note"),
            "declaredVersion": provenance.get("version") or None,
            "versionReadbackMethod": readback.get("method"),
            "versionObservedAt": readback.get("observed_at"),
            "versionSource": readback.get("source"),
            "detectionMode": detection.get("mode"),
            "entryProbe": probe_card,
            # the registry is not the truth and a stale note about it is not either: when the live entry
            # answers with a different version, both strings stay visible as drift.
            "versionDrift": bool(probe and probe.get("state") == "VERSION_MOVED"),
            "detectionEvidenceState": detection.get("evidence_state") or "UNKNOWN",
            "protocolConformance": {
                protocol: (conformance.get(protocol) or {}).get("status") or "ABSENT"
                for protocol in CONFORMANCE_PROTOCOLS
            },
            "observedAt": observed_at,
            "layers": layers,
            "nativeStatus": "NOT_IMPLEMENTED",
        })
    return cards


LIVE_PROBE_RECORD = "docs/audits/EXECUTOR_LIVE_PROBE_2026-10-08.json"


def load_live_probe(root: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Read the executor live probe record if this checkout has one.

    The probe is run by hand (`scripts/audit/executor_live_probe.py`) and its output is a tracked audit
    file, so an absent record is normal and means "not probed", never "not installed". A broken record is
    reported by raising: silently treating a corrupt probe as no-evidence would hide the run that produced it.
    """
    path = root / LIVE_PROBE_RECORD
    if not path.is_file():
        return [], None
    record = json.loads(path.read_text(encoding="utf-8"))
    return list(record.get("results") or []), record.get("at")


def load_inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Read the three tracked sources. A missing file raises: a card with no source is not a card."""
    registry = json.loads((root / "config/adapter-registry.json").read_text(encoding="utf-8"))
    conformance = json.loads((root / "config/capability-conformance.json").read_text(encoding="utf-8"))
    matrix = json.loads((root / "config/capability-matrix.json").read_text(encoding="utf-8"))
    return registry, conformance, matrix
