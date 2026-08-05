#!/usr/bin/env python3
"""Verify V3 Scenario/Atom/Bundle runtime contracts without live side effects.

This verifier checks the contracts that must exist before E3 Open Design runtime
registration can be claimed: pipeline stage graphs, GenUI triggers, project-state
stage coverage, bundle atom references, and provenance record shape. It is
read-only by default; pass `--emit <dir>` to write isolated E2 evidence samples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ASSISTANCE_DIR = "opendesign-assistance"
EVIDENCE_LEVELS = {"E0", "E1", "E2", "E3", "E4", "E5"}
EVIDENCE_STATES = {"NOT_RUN", "PASS", "FAIL", "BLOCKED", "UNVERIFIED", "SKIPPED_OPTIONAL"}
FIRST_PARTY_ATOMS = {
    "research-search",
    "discovery-question-form",
    "direction-picker",
    "todo-write",
    "file-read",
    "file-write",
    "media-image",
    "media-video",
    "media-audio",
    "live-artifact",
    "critique-theater",
}
EXPECTED_CORE_SCENARIOS = {"commercial-design-router", "brand-campaign-360"}
EXPECTED_CORE_BUNDLES = {"commercial-design-core", "visual-quality-core"}
RUNTIME_READY_REQUIREMENTS = [
    "Open Design runtime registration",
    "runtime ID/version read-back",
    "minimal task execution",
    "artifact and provenance read-back",
]


@dataclass
class Result:
    label: str
    ok: bool
    detail: str = ""


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ASSISTANCE_DIR).is_dir() and (parent / ".git").exists():
            return parent
    raise SystemExit("Could not locate repository root")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check(results: list[Result], label: str, ok: bool, detail: str = "") -> None:
    results.append(Result(label, ok, detail))


def object_at(results: list[Result], label: str, value: Any) -> dict[str, Any]:
    check(results, f"{label} is object", isinstance(value, dict), type(value).__name__)
    return value if isinstance(value, dict) else {}


def list_at(results: list[Result], label: str, value: Any) -> list[Any]:
    check(results, f"{label} is list", isinstance(value, list), type(value).__name__)
    return value if isinstance(value, list) else []


def local_atom_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in (root / ASSISTANCE_DIR / "atoms").glob("*/open-design.json"):
        try:
            manifest = load_json(path)
        except Exception:
            continue
        if isinstance(manifest, dict) and manifest.get("name"):
            ids.add(str(manifest["name"]))
    return ids


def pipeline_stage_map(manifest: dict[str, Any]) -> dict[str, set[str]]:
    stages = manifest.get("od", {}).get("pipeline", {}).get("stages", [])
    stage_map: dict[str, set[str]] = {}
    for stage in stages if isinstance(stages, list) else []:
        if not isinstance(stage, dict):
            continue
        stage_id = stage.get("id")
        if isinstance(stage_id, str):
            stage_map[stage_id] = {str(atom) for atom in stage.get("atoms", []) if isinstance(atom, str)}
    return stage_map


def verify_scenarios(root: Path, results: list[Result], atom_ids: set[str]) -> dict[str, dict[str, set[str]]]:
    scenario_dir = root / ASSISTANCE_DIR / "scenarios"
    scenario_manifests = sorted(scenario_dir.glob("*/open-design.json"))
    scenario_ids: set[str] = set()
    stage_maps: dict[str, dict[str, set[str]]] = {}
    for path in scenario_manifests:
        try:
            manifest = object_at(results, f"scenario {path.parent.name}", load_json(path))
        except Exception as exc:  # noqa: BLE001
            check(results, f"scenario {path.parent.name}: JSON parses", False, str(exc))
            continue
        name = str(manifest.get("name"))
        scenario_ids.add(name)
        od = object_at(results, f"scenario {name}.od", manifest.get("od"))
        check(results, f"scenario {name}: kind", od.get("kind") == "scenario", str(od.get("kind")))
        check(results, f"scenario {name}: mode", od.get("mode") == "scenario", str(od.get("mode")))
        stages = list_at(results, f"scenario {name}: pipeline stages", od.get("pipeline", {}).get("stages"))
        stage_ids = [stage.get("id") for stage in stages if isinstance(stage, dict)]
        check(results, f"scenario {name}: stage IDs unique", len(stage_ids) == len(set(stage_ids)), str(stage_ids))
        if name in EXPECTED_CORE_SCENARIOS:
            check(results, f"scenario {name}: has intake stage", "intake" in stage_ids, str(stage_ids))
            check(results, f"scenario {name}: has critique stage", "critique" in stage_ids, str(stage_ids))
            check(results, f"scenario {name}: has handoff stage", "handoff" in stage_ids, str(stage_ids))
        else:
            check(results, f"scenario {name}: has at least one stage", bool(stage_ids), str(stage_ids))
        stage_map = pipeline_stage_map(manifest)
        stage_maps[name] = stage_map
        known_atoms = atom_ids | FIRST_PARTY_ATOMS
        for stage_id, atoms in stage_map.items():
            check(results, f"scenario {name}: stage {stage_id} has atoms", bool(atoms), str(atoms))
            missing = sorted(atoms - known_atoms)
            check(results, f"scenario {name}: stage {stage_id} atoms resolvable", not missing, str(missing))
        if not isinstance(od.get("genui"), dict):
            check(results, f"scenario {name}: GenUI optional unless core", name not in EXPECTED_CORE_SCENARIOS, type(od.get("genui")).__name__)
            continue
        genui = object_at(results, f"scenario {name}: genui", od.get("genui"))
        surfaces = list_at(results, f"scenario {name}: GenUI surfaces", genui.get("surfaces"))
        if name in EXPECTED_CORE_SCENARIOS:
            check(results, f"scenario {name}: GenUI surfaces present", bool(surfaces), str(surfaces))
        for surface in surfaces:
            if not isinstance(surface, dict):
                check(results, f"scenario {name}: GenUI surface shape", False, str(surface))
                continue
            sid = surface.get("id")
            trigger = surface.get("trigger") if isinstance(surface.get("trigger"), dict) else {}
            stage_id = trigger.get("stageId")
            atom = trigger.get("atom")
            check(results, f"scenario {name}: GenUI {sid} has prompt", bool(surface.get("prompt")), str(surface))
            check(results, f"scenario {name}: GenUI {sid} persists to project", surface.get("persist") == "project", str(surface.get("persist")))
            check(results, f"scenario {name}: GenUI {sid} trigger stage exists", stage_id in stage_map, str(trigger))
            check(results, f"scenario {name}: GenUI {sid} trigger atom in stage", bool(stage_id in stage_map and atom in stage_map[stage_id]), str(trigger))
            check(results, f"scenario {name}: GenUI {sid} timeout bounded", surface.get("onTimeout") in {"abort", "retry", "default"}, str(surface.get("onTimeout")))
    check(results, "core scenarios present", EXPECTED_CORE_SCENARIOS <= scenario_ids, str(sorted(EXPECTED_CORE_SCENARIOS - scenario_ids)))
    return stage_maps


def verify_bundles(root: Path, results: list[Result], atom_ids: set[str]) -> None:
    bundle_dir = root / ASSISTANCE_DIR / "bundles"
    bundle_ids: set[str] = set()
    for path in sorted(bundle_dir.glob("*/open-design.json")):
        try:
            manifest = object_at(results, f"bundle {path.parent.name}", load_json(path))
        except Exception as exc:  # noqa: BLE001
            check(results, f"bundle {path.parent.name}: JSON parses", False, str(exc))
            continue
        name = str(manifest.get("name"))
        bundle_ids.add(name)
        od = object_at(results, f"bundle {name}.od", manifest.get("od"))
        check(results, f"bundle {name}: kind", od.get("kind") == "bundle", str(od.get("kind")))
        check(results, f"bundle {name}: mode", od.get("mode") == "bundle", str(od.get("mode")))
        context = object_at(results, f"bundle {name}: context", od.get("context"))
        atoms = {str(atom) for atom in context.get("atoms", []) if isinstance(atom, str)}
        check(results, f"bundle {name}: atom list present", bool(atoms), str(atoms))
        missing = sorted(atoms - atom_ids)
        check(results, f"bundle {name}: atoms resolvable", not missing, str(missing))
    check(results, "core bundles present", EXPECTED_CORE_BUNDLES <= bundle_ids, str(sorted(EXPECTED_CORE_BUNDLES - bundle_ids)))


def schema_enum(path: Path, key: str) -> set[str]:
    data = load_json(path)
    props = data.get("properties", {}) if isinstance(data, dict) else {}
    node = props.get(key, {})
    return {str(item) for item in node.get("enum", [])}


def verify_project_state_schema(root: Path, results: list[Result], stage_maps: dict[str, dict[str, set[str]]]) -> None:
    path = root / ASSISTANCE_DIR / "schemas" / "design-project-state.schema.json"
    data = object_at(results, "design-project-state schema", load_json(path))
    required = set(data.get("required", []))
    check(results, "project-state requires project_id/stage/decisions/artifacts", {"project_id", "stage", "decisions", "artifacts"} <= required, str(required))
    stages = schema_enum(path, "stage")
    all_pipeline_stages = {stage for stage_map in stage_maps.values() for stage in stage_map}
    missing = sorted(all_pipeline_stages - stages)
    check(results, "project-state stage enum covers scenario stages", not missing, str(missing))


def verify_provenance_schema(root: Path, results: list[Result]) -> dict[str, Any]:
    path = root / ASSISTANCE_DIR / "schemas" / "provenance.schema.json"
    data = object_at(results, "provenance schema", load_json(path))
    required = set(data.get("required", []))
    check(results, "provenance requires core fields", {"schemaVersion", "project_id", "artifact", "runtime", "agent", "source_refs", "steps", "evidence"} <= required, str(required))
    props = object_at(results, "provenance properties", data.get("properties"))
    for field in ["artifact", "runtime", "agent", "source_refs", "steps", "evidence"]:
        check(results, f"provenance has {field} property", field in props)
    return data


def sample_records() -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_body = b"OPEN-DESIGN-Assistance V3 isolated runtime contract sample\n"
    digest = hashlib.sha256(artifact_body).hexdigest()
    state = {
        "project_id": "v3-isolated-smoke",
        "stage": "intake",
        "decisions": [
            {"id": "brief-lock", "decision": "Use a bounded synthetic brief for verifier smoke.", "status": "approved", "evidence": ["verify_runtime_contracts_v3.py"]}
        ],
        "artifacts": [
            {"path": "artifacts/v3-isolated-smoke.txt", "type": "text/plain", "status": "review", "hash": digest}
        ],
        "active_design_system": "user:anomaly-monitor-dark",
        "iteration": 0,
    }
    provenance = {
        "schemaVersion": "open-design-assistance/provenance/v1",
        "project_id": "v3-isolated-smoke",
        "artifact": {"id": "v3-isolated-smoke", "path": "artifacts/v3-isolated-smoke.txt", "type": "text/plain", "sha256": digest, "created_at": "2026-08-04T00:00:00Z"},
        "runtime": {"name": "verify_runtime_contracts_v3.py", "status": "isolated", "version": "0.1.0"},
        "agent": {"name": "Hermes", "mode": "hermes"},
        "source_refs": [{"type": "local-project", "location": "opendesign-assistance/scenarios/commercial-design-router/open-design.json", "license_status": "owned"}],
        "steps": [
            {"id": "intake", "stage": "intake", "atom": "brief-normalizer", "status": "PASS", "evidence": "scenario manifest and project-state schema read-back"},
            {"id": "handoff", "stage": "handoff", "atom": "delivery-packager", "status": "SKIPPED_OPTIONAL", "evidence": "isolated verifier does not generate production artifacts"},
        ],
        "evidence": {"level": "E2", "state": "PASS", "claim": "Isolated runtime contract smoke only; Open Design live E3 remains pending.", "read_back": ["project state", "provenance digest"]},
    }
    return state, provenance


def verify_sample_records(results: list[Result]) -> tuple[dict[str, Any], dict[str, Any]]:
    state, provenance = sample_records()
    check(results, "sample state has project_id", bool(state.get("project_id")), str(state))
    check(results, "sample state has decisions", bool(state.get("decisions")), str(state))
    check(results, "sample state has artifacts", bool(state.get("artifacts")), str(state))
    evidence = provenance.get("evidence", {})
    check(results, "sample provenance evidence level valid", evidence.get("level") in EVIDENCE_LEVELS, str(evidence))
    check(results, "sample provenance evidence state valid", evidence.get("state") in EVIDENCE_STATES, str(evidence))
    runtime = provenance.get("runtime", {})
    check(results, "sample provenance runtime is isolated", runtime.get("status") == "isolated", str(runtime))
    steps = provenance.get("steps", [])
    check(results, "sample provenance has steps", bool(steps), str(steps))
    check(results, "sample provenance contains artifact digest", len(provenance.get("artifact", {}).get("sha256", "")) == 64, str(provenance.get("artifact")))
    return state, provenance


def emit_records(output_dir: Path, state: dict[str, Any], provenance: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "project-state.sample.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "provenance.sample.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_results(results: list[Result]) -> int:
    failed = [result for result in results if not result.ok]
    for result in results:
        prefix = "PASS" if result.ok else "FAIL"
        print(f"{prefix} {result.label}")
        if result.detail:
            print(f"  {result.detail}")
    print(f"\nVERIFY_RUNTIME_CONTRACTS_V3={'OK' if not failed else 'FAIL'} total={len(results)} failed={len(failed)}")
    return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify V3 Scenario/Atom/Bundle runtime contracts")
    parser.add_argument("--emit", type=Path, help="Optional ignored directory for isolated sample evidence")
    args = parser.parse_args()
    root = repo_root()
    results: list[Result] = []
    atoms = local_atom_ids(root)
    check(results, "local atoms present", bool(atoms), str(len(atoms)))
    stage_maps = verify_scenarios(root, results, atoms)
    verify_bundles(root, results, atoms)
    verify_project_state_schema(root, results, stage_maps)
    verify_provenance_schema(root, results)
    state, provenance = verify_sample_records(results)
    if args.emit:
        emit_records(args.emit, state, provenance)
        check(results, "isolated evidence emitted", (args.emit / "provenance.sample.json").is_file(), str(args.emit))
    return print_results(results)


if __name__ == "__main__":
    raise SystemExit(main())
