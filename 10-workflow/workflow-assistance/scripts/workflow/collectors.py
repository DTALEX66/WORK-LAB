"""Four bounded collectors for the Workflow Assistance worker (WL3-510).

All collectors are read-only against their sources and write normalized
canonical facts. No prompt/response bodies, credentials, tokens, or sensitive
absolute paths are ever stored. Degraded sources produce STALE/UNKNOWN values
and last-good ages instead of fabricated EXACT/LIVE/0 values.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_store import CanonicalStore
from durable_worker import CollectorResult

TOKEN_FILE_NAME_RE = re.compile(r".*?(usage|token|tokens|usage_rollup).*\.jsonl?$", re.IGNORECASE)
SENSITIVE_PATH_FRAGMENTS = ("appdata", "users", "documents", "desktop", "downloads", "keys", "secrets")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: object) -> str:
    encoded = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(encoded).hexdigest()[:32]}"


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, text=True, capture_output=True, check=False, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _sanitize_path(path: str) -> str:
    """Keep only a stable, non-sensitive project-relative key."""
    normalized = path.replace("\\", "/")
    for fragment in SENSITIVE_PATH_FRAGMENTS:
        if fragment in normalized.lower():
            return "<redacted-home-path>"
    return normalized


def collect_task_ledger(store: CanonicalStore, project_id: str) -> CollectorResult:
    """Collector 1: task ledger counts as canonical facts."""
    tasks = store.list_tasks()
    by_status: dict[str, int] = {}
    for task in tasks:
        status = task.get("status", "UNKNOWN")
        by_status[status] = by_status.get(status, 0) + 1
    records = [
        {
            "event_id": _stable_id("task-ledger", project_id, by_status),
            "project_id": project_id,
            "producer": "task-ledger-collector",
            "occurred_at": _now(),
            "freshness": "EXACT_SOURCE",
            "coverage": "PARTIAL",
            "quality": "EXACT_SOURCE",
            "task_counts": by_status,
            "total": len(tasks),
        }
    ]
    return CollectorResult(kind="telemetry", ok=True, records=records)


def collect_git_ci(store: CanonicalStore, project_id: str, project_root: Path) -> CollectorResult:
    """Collector 2: read-only git/CI status for the owning project."""
    head = _git(project_root, "rev-parse", "HEAD")
    branch = _git(project_root, "branch", "--show-current")
    dirty_raw = _git(project_root, "status", "--porcelain=v1") or ""
    dirty = len([line for line in dirty_raw.splitlines() if line.strip()])
    records: list[dict[str, Any]] = []
    if head:
        records.append(
            {
                "row_id": f"git-{project_id}",
                "project_id": project_id,
                "scope": "git",
                "quality": "EXACT_SOURCE" if head else "UNKNOWN",
                "coverage": "PARTIAL",
                "freshness": "STALE",
                "observed_at": _now(),
                "last_good_at": _now() if head else None,
                "head_sha": head,
                "branch": branch or "detached",
                "dirty_count": dirty,
                "sourceRef": "git-rev-parse",
            }
        )
    return CollectorResult(kind="quality", ok=True, records=records)


def collect_usage_files(store: CanonicalStore, project_id: str, search_root: Path) -> CollectorResult:
    """Collector 3: explicit usage counters from local JSON/JSONL, never estimates.

    Only numeric usage fields are accepted; auth tokens and prompt/response
    bodies are rejected by the store. Files are found only inside the project
    runtime root, never by scanning user profile paths.
    """
    records: list[dict[str, Any]] = []
    if search_root.is_dir():
        for candidate in sorted(search_root.rglob("*")):
            if not candidate.is_file():
                continue
            if not TOKEN_FILE_NAME_RE.match(candidate.name):
                continue
            try:
                text = candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            try:
                source_ref = candidate.relative_to(search_root).as_posix()
            except ValueError:
                source_ref = candidate.name
            content_occurrences: dict[str, int] = {}
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(item, dict):
                    continue
                tokens = {
                    key: item[key]
                    for key in (
                        "input_tokens", "output_tokens", "cache_read_tokens",
                        "cache_write_tokens", "reasoning_tokens", "tool_tokens",
                        "subagent_tokens", "total_tokens",
                    )
                    if isinstance(item.get(key), int) and item[key] >= 0
                }
                if not tokens:
                    continue
                provider = str(item.get("provider", "unknown"))
                model = str(item.get("model", "unknown"))
                content_identity = json.dumps(
                    {"provider": provider, "model": model, **tokens},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                content_occurrences[content_identity] = content_occurrences.get(content_identity, 0) + 1
                if candidate.suffix.lower() == ".jsonl":
                    # JSONL is an event log. Keep identities stable across
                    # prepend/reorder while preserving identical real events.
                    sample_identity: object = (
                        content_identity,
                        content_occurrences[content_identity],
                    )
                else:
                    # A .json rollup is a mutable snapshot; its row updates in
                    # place instead of accumulating every observed value.
                    sample_identity = line_number
                records.append(
                    {
                        "project_id": project_id,
                        "provider": provider,
                        "model": model,
                        "observed_at": _now(),
                        "quality": "EXACT_SOURCE",
                        "source_ref": _sanitize_path(source_ref),
                        "sample_id": _stable_id("usage", project_id, source_ref, sample_identity),
                        **tokens,
                    }
                )
    return CollectorResult(kind="usage", ok=True, records=records)


def collect_source_quality(store: CanonicalStore, project_id: str, project_root: Path) -> CollectorResult:
    """Collector 4: source-quality facts (freshness/coverage/quality)."""
    head = _git(project_root, "rev-parse", "HEAD")
    quality = "EXACT_SOURCE" if head else "UNKNOWN"
    record = {
        "row_id": f"quality-{project_id}-source",
        "project_id": project_id,
        "scope": "source",
        "quality": quality,
        "coverage": "PARTIAL",
        "freshness": "STALE",
        "observed_at": _now(),
        "last_good_at": _now() if head else None,
        "sourceRef": "git-head" if head else "unavailable",
    }
    return CollectorResult(kind="quality", ok=True, records=[record])


def collect_growth_watcher(store: CanonicalStore, project_id: str, search_root: Path) -> CollectorResult:
    """Collector 5 (WL3-300): discovery watcher over allowed project-adjacent dirs.

    Looks for candidate growth assets (skills/plugins/context packs) in the
    project's own runtime boundaries and classifies them with the existing
    growth pipeline state machine. Pure metadata (names, digests, statuses);
    never copies content bodies and never promotes anything automatically.
    """
    from growth_candidates import intake, source_digest

    candidates: list[dict[str, Any]] = []
    probe_dirs = [
        search_root / ".hermes" / "growth-candidates",
        search_root / ".agents" / "skills",
        search_root / ".hermes" / "desktop-attachments",
    ]
    for probe_dir in probe_dirs:
        if not probe_dir.is_dir():
            continue
        try:
            entries = sorted(probe_dir.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_file():
                continue
            name = entry.name.lower()
            if not (name.endswith((".md", ".json", ".yaml", ".yml")) or name.endswith(".zip")):
                continue
            candidates.append(
                {
                    "candidate_id": f"{project_id}-{entry.name}",
                    "origin": "local-discovery",
                    "classification": "learn",
                    "risk": "low",
                    "source": {"name": entry.name, "size": entry.stat().st_size},
                }
            )
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            item = intake(
                candidate["candidate_id"],
                candidate["origin"],
                candidate["classification"],
                candidate["risk"],
                candidate["source"],
            )
        except ValueError:
            continue  # un-discoverable candidate; quarantine implicitly by omission
        records.append(
            {
                "event_id": _stable_id("growth", item["candidateId"], source_digest(candidate["source"])),
                "project_id": project_id,
                "producer": "growth-watcher-collector",
                "occurred_at": _now(),
                "freshness": "EXACT_SOURCE",
                "coverage": "PARTIAL",
                "quality": "EXACT_SOURCE",
                "candidate_id": item["candidateId"],
                "candidate_status": item["status"],
                "candidate_risk": item["risk"],
                "source_digest": source_digest(candidate["source"]),
            }
        )
    return CollectorResult(kind="telemetry", ok=True, records=records)


def build_standard_collectors(project_root: Path) -> list[Any]:
    """Standard collector set bound to a project root."""
    from durable_worker import CollectorFn

    def task_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
        return collect_task_ledger(store, project_id)

    def git_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
        # Multi-project: collect git truth for every approved project root.
        # Unapproved roots are never scanned; missing roots are skipped.
        rows = store.list_projects()
        records: list[dict[str, Any]] = []
        ok_any = False
        err: str | None = None
        for row in rows:
            pid = str(row.get("project_id") or row.get("projectId") or "")
            if not pid:
                continue
            definition = store.get_project_definition(pid)
            if definition and not definition.get("approved", False):
                continue
            root = (definition or {}).get("root_path") or row.get("root_path")
            if not root:
                continue
            rp = Path(root)
            if not (rp / ".git").exists():
                continue
            result = collect_git_ci(store, pid, rp)
            records.extend(result.records)
            ok_any = ok_any or result.ok
            if result.error:
                err = result.error
        return CollectorResult(kind="quality", ok=ok_any or bool(records), records=records,
                               error=err)

    def usage_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
        return collect_usage_files(
            store,
            project_id,
            project_root / ".hermes" / "task-artifacts",
        )

    def quality_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
        return collect_source_quality(store, project_id, project_root)

    def growth_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
        return collect_growth_watcher(store, project_id, project_root)

    def platform_collector(store: CanonicalStore, project_id: str) -> CollectorResult:
        from platform_collector import collect_platform_observations
        return collect_platform_observations(store, project_id)

    return [task_collector, git_collector, usage_collector, quality_collector,
            growth_collector, platform_collector]


if __name__ == "__main__":
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Run the four standard collectors once")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--project-id", default="work-lab")
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    runtime_root = (args.runtime_root or Path(tempfile.gettempdir()) / "workflow-assistance-collectors").resolve()
    store = CanonicalStore(runtime_root / "canonical.sqlite")
    try:
        results = []
        for collector in build_standard_collectors(args.project_root):
            outcome = collector(store, args.project_id)
            results.append({"kind": outcome.kind, "ok": outcome.ok, "records": len(outcome.records)})
        print(json.dumps({"collectors": results, "integrity": store.integrity_check()}, ensure_ascii=False, indent=2))
    finally:
        store.close()
