#!/usr/bin/env python3
"""Secret-free user environment profile export (neutral, client-agnostic).

Inventories the user's Hermes and Codex user-level configuration and skills
into a tracked manifest for cross-machine restoration. It is read-only
against user homes and NEVER records secret values: any key or value matching
a secret pattern is replaced with [REDACTED].

Output: config/user-environment-profile.json (tracked, secret-free).
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

try:
    import yaml  # pyyaml
except ImportError:  # pragma: no cover
    yaml = None

SECRET_KEY = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|passwd|credential|auth|cookie|cookie|keyring|private|session|connection|endpoint|base_url|webhook|signing)"
)
SECRET_VALUE = re.compile(
    r"(?i)(sk-[A-Za-z0-9]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN|Bearer\s+[A-Za-z0-9._~+/=-]{16,}|"
    r"https?://[^\s/:@]{3,}:[^\s/@]{8,}@)"
)
REDACTED = "[REDACTED]"


def _redact_key(key: str) -> str:
    return REDACTED if SECRET_KEY.search(key) else key


def _redact_value(key: str, value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value  # handled by the walker
    text = str(value)
    if SECRET_KEY.search(key) or SECRET_VALUE.search(text):
        return REDACTED
    return value


def _redact_walk(data: Any, key: str = "") -> Any:
    if isinstance(data, dict):
        return {
            str(k): (REDACTED if SECRET_KEY.search(str(k)) else _redact_walk(v, str(k)))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact_walk(v, key) for v in data]
    return _redact_value(key, data)


def _frontmatter_description(skill_md: Path) -> str:
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    fm = text[3:end]
    for line in fm.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip("\"'").strip()
    return ""


def _inventory_skills(root: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not root.is_dir():
        return out
    for skill_md in sorted(root.rglob("SKILL.md")):
        if any(part in {"node_modules", ".git", ".archive", "__pycache__"} for part in skill_md.parts):
            continue
        out.append(
            {
                "name": skill_md.parent.name,
                "description": _frontmatter_description(skill_md),
                "path": str(skill_md.parent.relative_to(root)).replace("\\", "/"),
            }
        )
    return out


def _config_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file() or yaml is None:
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001 - best-effort
        return {}


def _config_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {}
    except tomllib.TOMLDecodeError:
        return {}


def _env_key_names(path: Path) -> list[str]:
    if not path.is_file():
        return []
    names: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            names.append(line.split("=", 1)[0].strip())
    return sorted(set(names))


def _redact_toml_keys(data: dict[str, Any]) -> dict[str, Any]:
    """Redact secret keys in a nested TOML config, keep provider/model names."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        if SECRET_KEY.search(key):
            out[key] = REDACTED
        elif isinstance(value, dict):
            out[key] = _redact_toml_keys(value)
        elif isinstance(value, list):
            out[key] = [_redact_toml_keys(v) if isinstance(v, dict) else _redact_value(key, v) for v in value]
        else:
            out[key] = _redact_value(key, value)
    return out


def _profile(home: Path, codex_home: Path, agent_home: Path) -> dict[str, Any]:
    hermes_config = _config_yaml(home / "config.yaml")
    codex_config = _config_toml(codex_home / "config.toml")
    return {
        "schema_version": "worklab/user-environment-profile/v1",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds"),
        "paths": {
            "hermes_home": str(home),
            "codex_home": str(codex_home),
            "agents_skills_root": str(agent_home / "skills"),
        },
        "hermes": {
            "config_yaml": _redact_walk(hermes_config),
            "env_key_names": _env_key_names(home / ".env"),
            "skills": _inventory_skills(home / "skills"),
        },
        "codex": {
            "config_toml": _redact_toml_keys(codex_config),
            "rules": sorted(p.relative_to(codex_home).as_posix() for p in (codex_home / "rules").glob("*.rules")) if (codex_home / "rules").is_dir() else [],
            "agents_skills": _inventory_skills(agent_home / "skills"),
        },
    }


def main(argv: list[str]) -> int:
    home = Path(argv[1]) if len(argv) > 1 else Path.home() / "AppData/Local/hermes"
    codex_home = Path(argv[2]) if len(argv) > 2 else Path.home() / ".codex"
    agent_home = Path(argv[3]) if len(argv) > 3 else Path.home() / ".agents"
    out = Path(argv[4]) if len(argv) > 4 else Path(__file__).resolve().parents[2] / "config/user-environment-profile.json"

    profile = _profile(home, codex_home, agent_home)
    payload = json.dumps(profile, ensure_ascii=False, indent=2)
    if REDACTED not in payload and any(
        SECRET_VALUE.search(line) for line in payload.splitlines() if "generated_at" not in line
    ):
        print("FAIL: unredacted secret value found in profile", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload + "\n", encoding="utf-8")
    print(
        f"USER_ENVIRONMENT_PROFILE_WRITTEN path={out} "
        f"hermes_skills={len(profile['hermes']['skills'])} "
        f"codex_skills={len(profile['codex']['agents_skills'])} "
        f"env_keys={len(profile['hermes']['env_key_names'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
