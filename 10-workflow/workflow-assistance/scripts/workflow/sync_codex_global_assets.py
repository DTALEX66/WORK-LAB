from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import tomllib
from pathlib import Path
from typing import Any

GUIDANCE_BEGIN = "<!-- BEGIN WORKFLOW-ASSISTANCE MANAGED CODEX OVERLAY -->"
GUIDANCE_END = "<!-- END WORKFLOW-ASSISTANCE MANAGED CODEX OVERLAY -->"
CONFIG_BEGIN = "# BEGIN WORKFLOW-ASSISTANCE MANAGED CODEX OVERLAY"
CONFIG_END = "# END WORKFLOW-ASSISTANCE MANAGED CODEX OVERLAY"
STATE_FILE = ".workflow-assistance-state.json"
RULE_RELATIVE = Path("rules/workflow-assistance.rules")
MANAGED_CONFIG: dict[str, Any] = {
    "approval_policy": "on-request",
    "sandbox_mode": "workspace-write",
    "project_doc_max_bytes": 65536,
}
VERSION = 2


class ManagedConflict(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.is_dir():
        raise FileNotFoundError(root)
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _remove_managed_block(text: str, begin: str, end: str) -> tuple[str, bool]:
    start = text.find(begin)
    finish = text.find(end)
    if start == -1 and finish == -1:
        return text, False
    if start == -1 or finish == -1 or finish < start:
        raise ManagedConflict(f"malformed managed block: {begin}")
    if text.find(begin, start + len(begin)) != -1 or text.find(end, finish + len(end)) != -1:
        raise ManagedConflict(f"duplicate managed block: {begin}")
    finish += len(end)
    while finish < len(text) and text[finish] in "\r\n":
        finish += 1
    base = (text[:start].rstrip() + "\n" + text[finish:].lstrip()).strip()
    return (base + "\n" if base else ""), True


def _render_guidance(existing: str, overlay: str) -> str:
    base, _ = _remove_managed_block(existing, GUIDANCE_BEGIN, GUIDANCE_END)
    block = f"{GUIDANCE_BEGIN}\n{overlay.strip()}\n{GUIDANCE_END}\n"
    return f"{base.rstrip()}\n\n{block}" if base.strip() else block


def _toml_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"unsupported managed TOML value: {type(value).__name__}")


def _render_config(existing: str) -> tuple[str, list[str], dict[str, Any]]:
    base, _ = _remove_managed_block(existing, CONFIG_BEGIN, CONFIG_END)
    parsed = tomllib.loads(base) if base.strip() else {}
    appended: list[str] = []
    preserved: dict[str, Any] = {}
    for key, desired in MANAGED_CONFIG.items():
        if key in parsed:
            preserved[key] = parsed[key]
        else:
            appended.append(key)
    if not appended:
        return base, appended, preserved
    lines = [CONFIG_BEGIN]
    lines.extend(f"{key} = {_toml_value(MANAGED_CONFIG[key])}" for key in appended)
    lines.append(CONFIG_END)
    block = "\n".join(lines) + "\n"
    if not base.strip():
        rendered = block
    else:
        base_lines = base.rstrip().splitlines()
        first_table = next(
            (index for index, line in enumerate(base_lines) if line.lstrip().startswith("[")),
            len(base_lines),
        )
        before = "\n".join(base_lines[:first_table]).rstrip()
        after = "\n".join(base_lines[first_table:]).lstrip()
        sections = [section for section in (before, block.rstrip(), after) if section]
        rendered = "\n\n".join(sections) + "\n"
    tomllib.loads(rendered)
    return rendered, appended, preserved


def _load_state(codex_home: Path) -> dict[str, Any]:
    path = codex_home / STATE_FILE
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManagedConflict(f"invalid managed state: {path}") from exc
    if not isinstance(state, dict) or state.get("version") not in {1, VERSION}:
        raise ManagedConflict(f"unsupported managed state: {path}")
    if not isinstance(state.get("target_hashes"), dict):
        raise ManagedConflict(f"incomplete managed state: {path}")
    if state.get("version") == 1 and "managed_skill_names" not in state:
        state["managed_skill_names"] = sorted(
            key.removeprefix("skills/")
            for key in state["target_hashes"]
            if isinstance(key, str) and key.startswith("skills/")
        )
    if not isinstance(state.get("managed_skill_names"), list) or not state["managed_skill_names"]:
        raise ManagedConflict(f"incomplete managed state: {path}")
    for name in state["managed_skill_names"]:
        if not isinstance(name, str) or not re.fullmatch(r"workflow-assistance-[a-z0-9-]+", name):
            raise ManagedConflict(f"invalid managed skill name in state: {path}")
    return state


def _skill_sources(source_root: Path) -> list[Path]:
    skill_root = source_root / "skills"
    skills = sorted(path.parent for path in skill_root.glob("workflow-assistance-*/SKILL.md"))
    if len(skills) < 6:
        raise ManagedConflict(f"Codex skill pack incomplete: found {len(skills)}")
    return skills


def _preflight(codex_home: Path, agent_home: Path, source_root: Path) -> dict[str, Any]:
    guidance_source = source_root / "global-guidance.md"
    rules_source = source_root / RULE_RELATIVE
    if not guidance_source.is_file() or not rules_source.is_file():
        raise ManagedConflict("Codex asset source is incomplete")
    state = _load_state(codex_home)
    previous = state.get("target_hashes", {}) if isinstance(state.get("target_hashes", {}), dict) else {}

    config_path = codex_home / "config.toml"
    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    guidance_path = codex_home / "AGENTS.md"
    guidance_text = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""
    if not state and (
        CONFIG_BEGIN in config_text
        or CONFIG_END in config_text
        or GUIDANCE_BEGIN in guidance_text
        or GUIDANCE_END in guidance_text
    ):
        raise ManagedConflict("managed markers exist without an ownership state file")

    rules_target = codex_home / RULE_RELATIVE
    if rules_target.exists():
        if not state:
            raise ManagedConflict(f"unowned rule target already exists: {rules_target}")
        current = _sha256_bytes(rules_target.read_bytes())
        source = _sha256_bytes(rules_source.read_bytes())
        old = previous.get(RULE_RELATIVE.as_posix())
        if current != source and current != old:
            raise ManagedConflict(f"user-owned rule conflict: {rules_target}")

    skills: list[dict[str, Any]] = []
    for source in _skill_sources(source_root):
        target = agent_home / "skills" / source.name
        source_hash = _tree_hash(source)
        relative = f"skills/{source.name}"
        if target.exists():
            if not state:
                raise ManagedConflict(f"unowned skill target already exists: {target}")
            current_hash = _tree_hash(target)
            old_hash = previous.get(relative)
            if current_hash != source_hash and current_hash != old_hash:
                raise ManagedConflict(f"user-owned skill conflict: {target}")
        skills.append({"name": source.name, "source": source, "target": target, "hash": source_hash})

    rendered_config, appended_fields, preserved_fields = _render_config(config_text)
    rendered_guidance = _render_guidance(guidance_text, guidance_source.read_text(encoding="utf-8"))
    return {
        "state": state,
        "rules_source": rules_source,
        "rules_target": rules_target,
        "skills": skills,
        "config_path": config_path,
        "config_original": config_text,
        "config_rendered": rendered_config,
        "appended_fields": appended_fields,
        "preserved_fields": preserved_fields,
        "guidance_path": guidance_path,
        "guidance_original": guidance_text,
        "guidance_rendered": rendered_guidance,
    }


def build_plan(codex_home: Path, agent_home: Path, source_root: Path) -> dict[str, Any]:
    data = _preflight(codex_home, agent_home, source_root)
    actions: list[dict[str, str]] = []
    if data["state"] and data["state"].get("version") != VERSION:
        actions.append({"action": "MIGRATE_OWNERSHIP_STATE", "target": f"CODEX_HOME/{STATE_FILE}"})
    if data["config_original"] != data["config_rendered"]:
        actions.append({"action": "PATCH_MANAGED_FIELDS", "target": "CODEX_HOME/config.toml"})
    if data["guidance_original"] != data["guidance_rendered"]:
        actions.append({"action": "MERGE_MANAGED_BLOCK", "target": "CODEX_HOME/AGENTS.md"})
    rules_source: Path = data["rules_source"]
    rules_target: Path = data["rules_target"]
    if not rules_target.exists() or rules_target.read_bytes() != rules_source.read_bytes():
        actions.append({"action": "REPLACE_OWNED_FILE", "target": RULE_RELATIVE.as_posix()})
    for skill in data["skills"]:
        target: Path = skill["target"]
        if not target.exists() or _tree_hash(target) != skill["hash"]:
            actions.append({"action": "REPLACE_OWNED_SKILL", "target": f"skills/{skill['name']}"})
    return {
        "status": "DRY_RUN",
        "managed_config_fields": sorted(MANAGED_CONFIG),
        "preserved_user_config_fields": sorted(data["preserved_fields"]),
        "actions": actions,
        "write_set_count": len(actions),
    }


def apply_overlay(codex_home: Path, agent_home: Path, source_root: Path) -> dict[str, Any]:
    data = _preflight(codex_home, agent_home, source_root)
    changed = False
    target_hashes: dict[str, str] = {}

    config_path: Path = data["config_path"]
    if data["config_original"] != data["config_rendered"]:
        _atomic_write(config_path, data["config_rendered"].encode("utf-8"))
        changed = True

    guidance_path: Path = data["guidance_path"]
    if data["guidance_original"] != data["guidance_rendered"]:
        _atomic_write(guidance_path, data["guidance_rendered"].encode("utf-8"))
        changed = True

    rules_source: Path = data["rules_source"]
    rules_target: Path = data["rules_target"]
    rules_bytes = rules_source.read_bytes()
    if not rules_target.exists() or rules_target.read_bytes() != rules_bytes:
        _atomic_write(rules_target, rules_bytes)
        changed = True
    target_hashes[RULE_RELATIVE.as_posix()] = _sha256_bytes(rules_bytes)

    for skill in data["skills"]:
        source: Path = skill["source"]
        target: Path = skill["target"]
        if not target.exists() or _tree_hash(target) != skill["hash"]:
            temporary = target.parent / f".{target.name}.staging"
            if temporary.exists():
                shutil.rmtree(temporary)
            shutil.copytree(source, temporary)
            if target.exists():
                shutil.rmtree(target)
            os.replace(temporary, target)
            changed = True
        target_hashes[f"skills/{skill['name']}"] = skill["hash"]

    state = {
        "version": VERSION,
        "managed_config_fields": list(data["appended_fields"]),
        "preserved_user_config_fields": sorted(data["preserved_fields"]),
        "managed_skill_names": [skill["name"] for skill in data["skills"]],
        "target_hashes": target_hashes,
    }
    state_bytes = (json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    state_path = codex_home / STATE_FILE
    if not state_path.exists() or state_path.read_bytes() != state_bytes:
        _atomic_write(state_path, state_bytes)
        changed = True

    verification = verify_overlay(codex_home, agent_home, source_root)
    if verification["status"] != "PASS":
        raise ManagedConflict(f"post-apply verification failed: {verification['issues']}")
    return {
        "status": "APPLIED" if changed else "NO_CHANGE",
        "managed_config_fields": sorted(MANAGED_CONFIG),
        "installed_skills": len(data["skills"]),
        "preserved_user_config_fields": sorted(data["preserved_fields"]),
    }


def verify_overlay(codex_home: Path, agent_home: Path, source_root: Path) -> dict[str, Any]:
    issues: list[str] = []
    config_path = codex_home / "config.toml"
    config_text = ""
    try:
        config_text = config_path.read_text(encoding="utf-8")
        config = tomllib.loads(config_text)
    except (OSError, tomllib.TOMLDecodeError):
        config = {}
        issues.append("config_invalid")
    state = _load_state(codex_home)
    if not state:
        issues.append("state_missing")
    managed_fields = state.get("managed_config_fields", []) if isinstance(state, dict) else []
    for key in managed_fields:
        if config.get(key) != MANAGED_CONFIG.get(key):
            issues.append(f"config_drift:{key}")
    if managed_fields and (config_text.count(CONFIG_BEGIN) != 1 or config_text.count(CONFIG_END) != 1):
        issues.append("config_managed_block_missing_or_duplicate")

    guidance_path = codex_home / "AGENTS.md"
    guidance = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""
    if guidance.count(GUIDANCE_BEGIN) != 1 or guidance.count(GUIDANCE_END) != 1:
        issues.append("guidance_missing_or_duplicate")
    else:
        guidance_source = (source_root / "global-guidance.md").read_text(encoding="utf-8")
        if guidance != _render_guidance(guidance, guidance_source):
            issues.append("guidance_drift")

    rules_source = source_root / RULE_RELATIVE
    rules_target = codex_home / RULE_RELATIVE
    if not rules_target.exists() or rules_target.read_bytes() != rules_source.read_bytes():
        issues.append("rules_drift")

    skills = _skill_sources(source_root)
    for source in skills:
        target = agent_home / "skills" / source.name
        if not target.exists() or _tree_hash(target) != _tree_hash(source):
            issues.append(f"skill_drift:{source.name}")
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "managed_config_fields": sorted(MANAGED_CONFIG),
        "installed_skills": len(skills),
    }


def rollback_overlay(codex_home: Path, agent_home: Path, source_root: Path) -> dict[str, Any]:
    state = _load_state(codex_home)
    config_path = codex_home / "config.toml"
    guidance_path = codex_home / "AGENTS.md"
    rules_target = codex_home / RULE_RELATIVE
    if not state:
        config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
        guidance_text = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""
        managed_looking_skills = [
            agent_home / "skills" / source.name
            for source in _skill_sources(source_root)
            if (agent_home / "skills" / source.name).exists()
        ]
        if (
            CONFIG_BEGIN in config_text
            or CONFIG_END in config_text
            or GUIDANCE_BEGIN in guidance_text
            or GUIDANCE_END in guidance_text
            or rules_target.exists()
            or managed_looking_skills
        ):
            raise ManagedConflict("managed-looking assets exist without an ownership state file")
        return {"status": "NO_CHANGE"}

    target_hashes = state.get("target_hashes", {}) if isinstance(state.get("target_hashes", {}), dict) else {}
    managed_skill_names = state["managed_skill_names"]

    expected_rule = target_hashes.get(RULE_RELATIVE.as_posix())
    if not expected_rule or not rules_target.exists() or _sha256_bytes(rules_target.read_bytes()) != expected_rule:
        raise ManagedConflict(f"managed rule changed after apply: {rules_target}")

    for name in managed_skill_names:
        target = agent_home / "skills" / name
        expected = target_hashes.get(f"skills/{name}")
        if not expected or not target.exists() or _tree_hash(target) != expected:
            raise ManagedConflict(f"managed skill changed after apply: {target}")

    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    managed_fields = state.get("managed_config_fields", [])
    if managed_fields:
        if config_text.count(CONFIG_BEGIN) != 1 or config_text.count(CONFIG_END) != 1:
            raise ManagedConflict(f"managed config block changed after apply: {config_path}")
        parsed_config = tomllib.loads(config_text)
        if any(parsed_config.get(key) != MANAGED_CONFIG.get(key) for key in managed_fields):
            raise ManagedConflict(f"managed config field changed after apply: {config_path}")

    guidance_text = guidance_path.read_text(encoding="utf-8") if guidance_path.exists() else ""
    if guidance_text.count(GUIDANCE_BEGIN) != 1 or guidance_text.count(GUIDANCE_END) != 1:
        raise ManagedConflict(f"managed guidance block changed after apply: {guidance_path}")
    guidance_source = (source_root / "global-guidance.md").read_text(encoding="utf-8")
    if guidance_text != _render_guidance(guidance_text, guidance_source):
        raise ManagedConflict(f"managed guidance content changed after apply: {guidance_path}")

    changed = False
    if config_path.exists():
        original = config_path.read_text(encoding="utf-8")
        rendered, removed = _remove_managed_block(original, CONFIG_BEGIN, CONFIG_END)
        if removed:
            tomllib.loads(rendered) if rendered.strip() else None
            _atomic_write(config_path, rendered.encode("utf-8"))
            changed = True

    if guidance_path.exists():
        original = guidance_path.read_text(encoding="utf-8")
        rendered, removed = _remove_managed_block(original, GUIDANCE_BEGIN, GUIDANCE_END)
        if removed:
            _atomic_write(guidance_path, rendered.encode("utf-8"))
            changed = True

    if rules_target.exists():
        rules_target.unlink()
        changed = True
    for name in managed_skill_names:
        target = agent_home / "skills" / name
        if target.exists():
            shutil.rmtree(target)
            changed = True

    state_path = codex_home / STATE_FILE
    if state_path.exists():
        state_path.unlink()
        changed = True
    return {"status": "ROLLED_BACK" if changed else "NO_CHANGE"}


def _default_source_root() -> Path:
    return Path(__file__).resolve().parents[2] / "codex-assets"


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize the Workflow Assistance Codex user overlay")
    parser.add_argument("operation", choices=("plan", "apply", "verify", "rollback"))
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--agent-home", type=Path, default=Path.home() / ".agents")
    parser.add_argument("--source-root", type=Path, default=_default_source_root())
    args = parser.parse_args()
    try:
        if args.operation == "plan":
            result = build_plan(args.codex_home, args.agent_home, args.source_root)
        elif args.operation == "apply":
            result = apply_overlay(args.codex_home, args.agent_home, args.source_root)
        elif args.operation == "verify":
            result = verify_overlay(args.codex_home, args.agent_home, args.source_root)
        else:
            result = rollback_overlay(args.codex_home, args.agent_home, args.source_root)
    except (ManagedConflict, FileNotFoundError, OSError, tomllib.TOMLDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") not in {"FAIL", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
