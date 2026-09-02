#!/usr/bin/env python3
"""Validate repository skill metadata, references, and optional live-profile parity.

This checker is intentionally secret-free: it reads only SKILL.md metadata and
content hashes. It never loads Hermes configuration, auth stores, plugins, or
provider credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from typing import Any

import yaml

KNOWN_PROFILE_SKILLS = {
    "agent-workflow-fortress",
    "codex",
    "github-pr-workflow",
    "hermes-agent",
    "plan",
    "project-gap-analysis",
    "project-data-boundary",
    "sleep-mode",
    "systematic-debugging",
    "test-driven-development",
}
def sha256(path: Path) -> str:
    """Hash canonical UTF-8 text so Windows CRLF and Linux LF agree."""

    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"missing YAML frontmatter: {path}")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError(f"unterminated YAML frontmatter: {path}")
    data = yaml.safe_load(text[4:end]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"frontmatter must be a mapping: {path}")
    return data


def discover(root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    result: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(root.rglob("SKILL.md")):
        data = frontmatter(path)
        name = data.get("name")
        version = data.get("version")
        metadata = data.get("metadata")
        hermes = metadata.get("hermes") if isinstance(metadata, dict) else None
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"skill name is missing: {path}")
        if not isinstance(version, (str, int, float)):
            raise ValueError(f"skill version is missing: {path}")
        if not isinstance(hermes, dict):
            raise ValueError(f"metadata.hermes is missing: {path}")
        if name in result:
            raise ValueError(f"duplicate skill name {name!r}: {path}")
        result[name] = (path, data)
    return result


def related_names(data: dict[str, Any]) -> list[str]:
    metadata = data.get("metadata") or {}
    hermes = metadata.get("hermes") if isinstance(metadata, dict) else {}
    values = hermes.get("related_skills", []) if isinstance(hermes, dict) else []
    if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
        raise ValueError("metadata.hermes.related_skills must be a string list")
    return values


def validate(repo_root: Path, manifest_path: Path, live_root: Path | None = None) -> int:
    source_root = repo_root / "skills"
    source = discover(source_root)
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("skill provenance manifest schema_version must be 1")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("skill provenance manifest entries must be a list")

    for name, (_, data) in source.items():
        missing = sorted(set(related_names(data)) - (set(source) | KNOWN_PROFILE_SKILLS))
        if missing:
            raise ValueError(f"{name} references unknown source skills: {', '.join(missing)}")

    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("provenance entry must be a mapping")
        name = entry.get("name")
        source_rel = entry.get("source")
        if not isinstance(name, str) or not isinstance(source_rel, str):
            raise ValueError("provenance entry requires name and source")
        if name in seen:
            raise ValueError(f"duplicate provenance entry: {name}")
        seen.add(name)
        if source_rel.startswith("profile-live-only/"):
            source_path = None
        else:
            source_path = (repo_root / source_rel).resolve()
            if not source_path.is_file():
                raise ValueError(f"provenance source does not exist: {source_rel}")
            data = frontmatter(source_path)
            if data.get("name") != name:
                raise ValueError(f"provenance name mismatch: {source_rel}")
            expected_sha = entry.get("source_sha256")
            if expected_sha != sha256(source_path):
                raise ValueError(f"source SHA drift: {name}")
        if not entry.get("trust") or not entry.get("permission") or "enabled" not in entry:
            raise ValueError(f"provenance trust/permission/enabled missing: {name}")
        if live_root is not None:
            live_rel = entry.get("live")
            if not isinstance(live_rel, str):
                raise ValueError(f"live path missing: {name}")
            live_path = (live_root / live_rel).resolve()
            if not live_path.is_file():
                raise ValueError(f"live skill missing: {name}: {live_path}")
            live_sha = sha256(live_path)
            if entry.get("live_sha256") != live_sha:
                raise ValueError(f"live SHA drift: {name}")
    if not set(source).issubset(seen):
        missing = sorted(set(source) - seen)
        raise ValueError("manifest does not cover all repository skills: " + ", ".join(missing))
    print(f"SKILL_PROVENANCE_PASS skills={len(source)} live_checked={live_root is not None}")
    return 0


def build_manifest(repo_root: Path, live_root: Path | None = None) -> dict[str, Any]:
    source = discover(repo_root / "skills")
    entries: list[dict[str, Any]] = []
    for name, (path, data) in sorted(source.items()):
        rel = path.relative_to(repo_root).as_posix()
        live_rel = f"skills/{path.relative_to(repo_root / 'skills').as_posix()}"
        entry: dict[str, Any] = {
            "name": name,
            "source": rel,
            "live": live_rel,
            "source_sha256": sha256(path),
            "version": str(data["version"]),
            "trust": "repository-controlled",
            "enabled": True,
            "permission": "read-write-via-explicit-wrapper" if name == "project-data-boundary" else "skill-guidance",
            "profile_scope": "default",
        }
        if live_root is not None:
            live_path = live_root / live_rel
            if not live_path.is_file():
                raise ValueError(f"cannot build manifest: live skill missing: {live_path}")
            entry["live_sha256"] = sha256(live_path)
        else:
            entry["live_sha256"] = "pending-live-sync"
        entries.append(entry)
    return {"schema_version": 1, "profile_scope": "default", "entries": entries}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--live-root", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    live = args.live_root.resolve() if args.live_root else None
    if args.write:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(yaml.safe_dump(build_manifest(repo, live), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return validate(repo, args.manifest, live)


if __name__ == "__main__":
    raise SystemExit(main())
