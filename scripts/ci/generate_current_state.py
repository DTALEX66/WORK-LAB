#!/usr/bin/env python3
"""Generate and verify WORK-LAB's current canonical state.

The generator is repository-local and secret-free. It reads canonical registries,
repository-managed skill metadata, the Stage 3 graph/baseline, the root CI
workflow, and optional explicit CI evidence. It never reads Hermes Home, auth
stores, provider configuration, sessions, or prompt/response bodies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


DEFAULT_CI_EVIDENCE = Path(".hermes/task-artifacts/current-state-ci.json")
CANONICAL_FILES = (
    "00-governance/PROJECT_POSITIONING.md",
    "00-governance/projects.json",
    "00-governance/module-ownership.json",
    "00-governance/contracts/contract-catalog.json",
    "00-governance/contracts/source-ledger.schema.json",
    "00-governance/contracts/capability-conformance.schema.json",
    "00-governance/source-ledger.json",
    "00-governance/work-lab.project-profile.yaml",
    "00-governance/generated/STAGE3_BASELINE.json",
    "README.md",
    "40-knowledge/README.md",
    "50-taskpacks/TASKPACK_SUMMARY.md",
    "50-taskpacks/WORK-LAB-STAGE-3-TASK-GRAPH.json",
    "10-workflow/workflow-assistance/workflow-manifest.yaml",
    "10-workflow/workflow-assistance/config/capability-conformance.json",
    "10-workflow/workflow-assistance/schemas/workflow/ci-observation.schema.json",
    "10-workflow/workflow-assistance/schemas/workflow/model-policy.schema.json",
    "10-workflow/workflow-assistance/schemas/workflow/memory-record.schema.json",
    "10-workflow/workflow-assistance/schemas/workflow/rule-drift.schema.json",
    "10-workflow/workflow-assistance/schemas/workflow/project-profile.schema.json",
    "10-workflow/workflow-assistance/scripts/workflow/ci_watcher.py",
    "10-workflow/workflow-assistance/scripts/workflow/model_policy.py",
    "10-workflow/workflow-assistance/scripts/workflow/growth_candidates.py",
    "10-workflow/workflow-assistance/scripts/workflow/growth_watcher.py",
    "10-workflow/workflow-assistance/scripts/workflow/impact_planner.py",
    "10-workflow/workflow-assistance/scripts/workflow/run_taskpack_agent.py",
    "10-workflow/workflow-assistance/scripts/workflow/task_ledger.py",
    "30-observer/work-lab-observer/schemas/observer-event.schema.json",
    "30-observer/work-lab-observer/src/observer_runtime.py",
    "30-observer/work-lab-observer/src/observer_evidence.py",
    "30-observer/work-lab-observer/src/observer_store.py",
    "10-workflow/workflow-assistance/config/skill-provenance.yaml",
    ".github/workflows/work-lab-gate.yml",
)
SUPPORT_AREAS = (
    ("governance", "00-governance"),
    ("knowledge", "40-knowledge"),
    ("taskpacks", "50-taskpacks"),
    ("archive_manifests", "90-archive-manifests"),
    ("root_delivery", ".github"),
)
STALE_WORKFLOW = "workflow-governance"


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {relative}")
    return value


def _read_yaml(root: Path, relative: str) -> dict[str, Any]:
    value = yaml.safe_load((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping: {relative}")
    return value


def _canonical_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_files(root: Path) -> list[tuple[str, Path]]:
    paths: dict[str, Path] = {}
    for relative in CANONICAL_FILES:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"canonical source missing: {relative}")
        paths[relative] = path
    workflow_root = root / "10-workflow/workflow-assistance"
    provenance = _read_yaml(root, "10-workflow/workflow-assistance/config/skill-provenance.yaml")
    for entry in provenance.get("entries", []):
        if not isinstance(entry, dict):
            raise ValueError("skill provenance entry must be a mapping")
        relative = entry.get("source")
        if not isinstance(relative, str):
            raise ValueError("skill provenance source must be a string")
        path = workflow_root / relative
        if not path.is_file():
            raise ValueError(f"skill source missing: {relative}")
        paths[f"10-workflow/workflow-assistance/{relative}"] = path
    return sorted(paths.items())


def source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative, path in _source_files(root):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_canonical_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def content_digest(state: dict[str, Any]) -> str:
    payload = {key: value for key, value in state.items() if key != "generated_at"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode:
        return "unknown"
    return result.stdout.strip()


def _registry_count(root: Path, relative: str, key: str) -> int:
    value = _read_json(root, relative).get(key)
    if not isinstance(value, (list, dict)):
        raise ValueError(f"registry key is not countable: {relative}#{key}")
    return len(value)


def _workflow_identity(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    workflow = _read_yaml(root, ".github/workflows/work-lab-gate.yml")
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict):
        raise ValueError("root workflow jobs must be a mapping")
    display_names: dict[str, str] = {}
    for key, value in jobs.items():
        if isinstance(value, dict):
            display_names[str(key)] = str(value.get("name", key))
    declared = manifest.get("delivery", {}).get("required_workflows", [])
    if not isinstance(declared, list):
        declared = []
    return {
        "workflow_file": ".github/workflows/work-lab-gate.yml",
        "workflow_name": str(workflow.get("name", "unknown")),
        "job_names": sorted(display_names),
        "job_display_names": display_names,
        "aggregate_job": "aggregate" if "aggregate" in jobs else None,
        "manifest_declared_required_workflows": [str(item) for item in declared],
    }


def _compact_ci(evidence: Path | None) -> dict[str, Any]:
    if evidence is None or not evidence.is_file():
        return {"status": "unknown", "evidence": "not-provided"}
    value = json.loads(evidence.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("CI evidence must be a JSON object")
    jobs = value.get("jobs", [])
    compact_jobs: list[dict[str, Any]] = []
    if isinstance(jobs, list):
        for job in jobs:
            if isinstance(job, dict):
                compact_jobs.append(
                    {
                        "name": str(job.get("name", "unknown")),
                        "status": str(job.get("status", "unknown")),
                        "conclusion": str(job.get("conclusion", "unknown")),
                    }
                )
    return {
        "run_id": value.get("databaseId", value.get("run_id")),
        "workflow_name": value.get("workflowName", value.get("workflow_name")),
        "status": value.get("status", "unknown"),
        "conclusion": value.get("conclusion", "unknown"),
        "head_sha": value.get("headSha", value.get("head_sha")),
        "url": value.get("url"),
        "attempt": value.get("attempt", value.get("runAttempt")),
        "jobs": sorted(compact_jobs, key=lambda item: item["name"]),
    }


def _compact_portable_readback(evidence: Path | None) -> dict[str, Any]:
    if evidence is None or not evidence.is_file():
        return {"status": "not-provided"}
    value = json.loads(evidence.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("portable readback evidence must be a JSON object")
    return {
        "status": str(value.get("status", "unknown")),
        "skill_count": value.get("skill_count"),
        "structural_checks": str(value.get("structural_checks", "unknown")),
        "runtime_compatibility": str(value.get("runtime_compatibility", "unknown")),
        "live_home_touched": bool(value.get("live_home_touched", False)),
    }


def build_state(
    root: Path,
    *,
    ci_evidence: Path | None = None,
    portable_readback: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    projects = _read_json(root, "00-governance/projects.json")
    ownership = _read_json(root, "00-governance/module-ownership.json")
    catalog = _read_json(root, "00-governance/contracts/contract-catalog.json")
    manifest = _read_yaml(root, "10-workflow/workflow-assistance/workflow-manifest.yaml")
    provenance = _read_yaml(root, "10-workflow/workflow-assistance/config/skill-provenance.yaml")
    stage3_graph = _read_json(root, "50-taskpacks/WORK-LAB-STAGE-3-TASK-GRAPH.json")
    stage3_baseline = _read_json(root, "00-governance/generated/STAGE3_BASELINE.json")
    modules = projects.get("modules", [])
    if not isinstance(modules, list):
        raise ValueError("projects.modules must be a list")
    skills = provenance.get("entries", [])
    if not isinstance(skills, list):
        raise ValueError("skill provenance entries must be a list")
    skill_items = []
    workflow_root = root / "10-workflow/workflow-assistance"
    for entry in skills:
        if not isinstance(entry, dict):
            raise ValueError("skill provenance entry must be a mapping")
        source = str(entry["source"])
        skill_items.append(
            {
                "name": str(entry["name"]),
                "source": source,
                "version": str(entry.get("version", "unknown")),
                "source_sha256": sha256_bytes(_canonical_bytes(workflow_root / source)),
                "trust": str(entry.get("trust", "unknown")),
                "enabled": bool(entry.get("enabled", False)),
                "live_readback": "not-run",
            }
        )
    state: dict[str, Any] = {
        "schema_version": "work-lab-current-state/v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_digest": source_digest(root),
        "git": {
            "head": _git(root, "rev-parse", "HEAD"),
            "branch": _git(root, "branch", "--show-current"),
        },
        "modules": [
            {
                "id": str(item.get("id")),
                "path": str(item.get("path")),
                "role": str(item.get("role", "unknown")),
            }
            for item in modules
            if isinstance(item, dict)
        ],
        "module_ownership": {
            "single_writer": bool(ownership.get("singleWriter", False)),
            "cross_module_writes": ownership.get("crossModuleWrites", "unknown"),
        },
        "support_areas": [
            {"id": identifier, "path": path, "present": (root / path).is_dir()}
            for identifier, path in SUPPORT_AREAS
        ],
        "contracts": {
            "count": len(catalog.get("contracts", [])),
            "schema_version": catalog.get("schemaVersion", "unknown"),
        },
        "skills": {
            "count": len(skill_items),
            "items": sorted(skill_items, key=lambda item: item["name"]),
            "isolated_portable_readback": _compact_portable_readback(portable_readback),
        },

        "workflow_identity": _workflow_identity(root, manifest),
        "stage3": {
            "taskpack_id": stage3_graph.get("taskpackId", "unknown"),
            "task_count": len(stage3_graph.get("tasks", [])),
            "initial_state": stage3_graph.get("initialState", "unknown"),
            "baseline_candidate_tree": stage3_baseline.get("git", {}).get("incomingCandidateTree", "unknown"),
            "incoming_dirty_count": sum(
                len(items)
                for items in stage3_baseline.get("dirtyClassification", {}).values()
                if isinstance(items, list)
            ),
            "writer_state": stage3_baseline.get("writer", {}).get("state", "unknown"),
        },
        "ci": _compact_ci(ci_evidence),
        "unverified_capabilities": [
            "hermes_live_apply",
            "paid_provider_smoke",
            "transferred_visual_calibration",
            "real_device_validation",
            "commercial_release",
        ],
    }
    state["content_digest"] = content_digest(state)
    return state


def check_stale_references(paths: Iterable[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lowered = text.lower()
        if STALE_WORKFLOW in lowered:
            findings.append(f"{path}: stale-workflow-name={STALE_WORKFLOW}")
        if "not committed/pushed" in lowered or "not committed or pushed" in lowered:
            findings.append(f"{path}: stale-publication-status")
        if re.search(r"active module[^\n]*(minigame|fourth)", lowered):
            findings.append(f"{path}: fourth-active-module")
    return findings


def _canonical_doc_paths(root: Path) -> list[Path]:
    relative = [
        "00-governance/PROJECT_POSITIONING.md",
        "00-governance/projects.json",
        "00-governance/module-ownership.json",
        "00-governance/contracts/contract-catalog.json",
        "README.md",
        "40-knowledge/README.md",
        "50-taskpacks/TASKPACK_SUMMARY.md",
        "50-taskpacks/WORK-LAB-EXECUTION-EFFICIENCY-REPAIR-HANDOFF.md",
        "10-workflow/workflow-assistance/workflow-manifest.yaml",
        "10-workflow/workflow-assistance/README.md",
    ]
    return [root / item for item in relative if (root / item).is_file()]


def render_markdown(state: dict[str, Any]) -> str:
    modules = "\n".join(f"- `{item['id']}` — `{item['path']}`" for item in state["modules"])
    jobs = state["ci"].get("jobs", [])
    job_lines = "\n".join(
        f"- `{job['name']}`: {job['conclusion']} ({job['status']})" for job in jobs
    ) or "- unavailable"
    unverified = "\n".join(f"- `{item}`" for item in state["unverified_capabilities"])
    return f"""# WORK-LAB current state

Generated at: `{state['generated_at']}`  \\
Source digest: `{state['source_digest']}`  \\
Content digest: `{state['content_digest']}`

## Git

- HEAD: `{state['git']['head']}`
- Branch: `{state['git']['branch']}`

## Active modules

{modules}

## Governance

- Contracts: `{state['contracts']['count']}`
- Repository skills: `{state['skills']['count']}`
- Single writer: `{state['module_ownership']['single_writer']}`
- Cross-module writes: `{state['module_ownership']['cross_module_writes']}`

## Workflow identity

- Workflow file: `{state['workflow_identity']['workflow_file']}`
- Workflow name: `{state['workflow_identity']['workflow_name']}`
- Aggregate job: `{state['workflow_identity']['aggregate_job']}`
- Manifest-declared required workflows: `{', '.join(state['workflow_identity']['manifest_declared_required_workflows']) or 'none'}`

## Stage 3 baseline

- TaskPack: `{state['stage3']['taskpack_id']}`
- Tasks: `{state['stage3']['task_count']}`
- Initial state: `{state['stage3']['initial_state']}`
- Incoming candidate tree: `{state['stage3']['baseline_candidate_tree']}`
- Incoming dirty paths: `{state['stage3']['incoming_dirty_count']}`
- Writer state: `{state['stage3']['writer_state']}`

## CI evidence

- Run: `{state['ci'].get('run_id', 'unknown')}`
- Head SHA: `{state['ci'].get('head_sha', 'unknown')}`
- Conclusion: `{state['ci'].get('conclusion', 'unknown')}`
{job_lines}

## Explicitly unverified

{unverified}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json-out", type=Path, default=Path("00-governance/generated/CURRENT_STATE.json"))
    parser.add_argument("--markdown-out", type=Path, default=Path("00-governance/generated/CURRENT_STATE.md"))
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--portable-readback", type=Path)
    parser.add_argument("--check-stale", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.check_stale:
        findings = check_stale_references(_canonical_doc_paths(root))
        if findings:
            print("CURRENT_STATE_STALE_DOC_FAIL")
            print("\n".join(findings))
            return 1
        projects = _read_json(root, "00-governance/projects.json")
        modules = {str(item.get("id")) for item in projects.get("modules", []) if isinstance(item, dict)}
        if modules != {"workflow-assistance", "work-lab-observer"}:
            print("CURRENT_STATE_STALE_DOC_FAIL fourth-active-module")
            return 1
        print("CURRENT_STATE_STALE_DOC_PASS")
        return 0
    ci_evidence = args.ci_evidence.resolve() if args.ci_evidence else None
    portable_readback = args.portable_readback.resolve() if args.portable_readback else None
    state = build_state(root, ci_evidence=ci_evidence, portable_readback=portable_readback)
    json_out = args.json_out if args.json_out.is_absolute() else root / args.json_out
    markdown_out = args.markdown_out if args.markdown_out.is_absolute() else root / args.markdown_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(state), encoding="utf-8")
    print(
        f"CURRENT_STATE_PASS head={state['git']['head']} modules={len(state['modules'])} "
        f"skills={state['skills']['count']} contracts={state['contracts']['count']} "
        f"source_digest={state['source_digest']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
