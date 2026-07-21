from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_OUTPUT = Path(".hermes/task-artifacts/context-pack.md")
MAX_SECTION_CHARS = 8000
# Keep a new-session handoff inside the portable token policy default. Callers may
# explicitly raise this up to the documented 30k hard ceiling for audits.
DEFAULT_MAX_CHARS = 12000
HARD_MAX_CHARS = 30000

SELECTED_TEXT_FILES = (
    "README.md",
    "docs/workflow/project-definition.md",
    "docs/workflow/gateway-cron-delivery.md",
    "docs/workflow/agent-evaluation.md",
    "docs/workflow/context-pack.md",
    "docs/workflow/local-quality-gates.md",
    "docs/workflow/ui-skin-system.md",
    "docs/workflow/project-data-boundary.md",
    "docs/mcp/workflow-mcp-stack.md",
    "docs/mcp/mcp-catalog-governance.md",
    "docs/absorption/open-source-workflow-absorption.md",
    "config/config.yaml",
    "config/SOUL.md",
)

INVENTORY_ROOTS = (
    "bin",
    "config",
    "docs",
    "scripts",
    "skills",
    "templates",
    "tests",
)

FORBIDDEN_PATH_PARTS = {
    ".git",
    ".hermes",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "venv",
    ".venv",
    "logs",
    "cache",
}

FORBIDDEN_FILE_NAMES = {
    ".env",
    "auth.json",
    "state.db",
    "cookies.txt",
}

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization|bearer)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"npm_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
)


def run_git(root: Path, *args: str, check: bool = False) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return redact(result.stdout.strip())


def git_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise SystemExit("build_context_pack: not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def _windows_long_path(path: Path) -> Path:
    """Return a stable long-name path for existing Windows paths.

    GitHub Actions can expose the same temp directory as both
    ``C:\\Users\\runneradmin`` and the DOS 8.3 alias ``C:\\Users\\RUNNER~1``.
    ``Path.relative_to`` is purely lexical, so normalize existing path prefixes
    before containment checks.
    """
    if os.name != "nt":
        return path
    text = str(path)
    buffer_size = ctypes.windll.kernel32.GetLongPathNameW(text, None, 0)
    if buffer_size <= 0:
        return path
    buffer = ctypes.create_unicode_buffer(buffer_size)
    written = ctypes.windll.kernel32.GetLongPathNameW(text, buffer, buffer_size)
    if written <= 0:
        return path
    return Path(buffer.value)


def canonical_path(path: Path) -> Path:
    """Canonicalize a path, including Windows short-name aliases.

    Works for paths that do not exist yet by canonicalizing the nearest existing
    ancestor and appending the unresolved suffix.
    """
    resolved = path.resolve(strict=False)
    existing = resolved
    suffix: list[str] = []
    while not existing.exists() and existing != existing.parent:
        suffix.append(existing.name)
        existing = existing.parent
    existing = _windows_long_path(existing.resolve(strict=False))
    for part in reversed(suffix):
        existing = existing / part
    return existing


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        canonical_path(path).relative_to(canonical_path(parent))
        return True
    except ValueError:
        return False


def require_ignored_output(root: Path, output: Path) -> None:
    output = canonical_path(output)
    root = canonical_path(root)
    if not is_relative_to(output, root):
        raise SystemExit(f"output path escapes project root: {output}")
    relative = output.relative_to(root).as_posix()
    probe = subprocess.run(
        ["git", "check-ignore", "-q", relative],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if probe.returncode != 0:
        raise SystemExit(f"output path is not git-ignored: {relative}")


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def safe_rel(path: Path) -> str:
    return path.as_posix().replace("\\", "/")


def forbidden_path(relative: Path) -> bool:
    parts = set(relative.parts)
    return bool(parts & FORBIDDEN_PATH_PARTS) or relative.name in FORBIDDEN_FILE_NAMES


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_safe_text(root: Path, relative: str, max_chars: int = MAX_SECTION_CHARS) -> str | None:
    path = root / relative
    if not path.is_file() or forbidden_path(Path(relative)):
        return None
    data = path.read_text(encoding="utf-8", errors="replace")
    data = redact(data)
    if len(data) > max_chars:
        return data[:max_chars] + f"\n\n[truncated at {max_chars} characters]\n"
    return data


def tracked_inventory(root: Path, limit: int = 300) -> list[str]:
    raw = run_git(root, "ls-files", *INVENTORY_ROOTS).splitlines()
    safe = []
    for item in raw:
        relative = Path(item)
        if forbidden_path(relative):
            continue
        safe.append(item)
    return safe[:limit]


def skill_inventory(root: Path) -> list[str]:
    skills_root = root / "skills"
    if not skills_root.exists():
        return []
    items = []
    for skill in sorted(skills_root.rglob("SKILL.md")):
        rel = skill.parent.relative_to(skills_root)
        items.append(safe_rel(rel))
    return items


def build_context_pack(root: Path, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    head = run_git(root, "rev-parse", "--short", "HEAD") or "unknown"
    branch = run_git(root, "branch", "--show-current") or "unknown"
    status = run_git(root, "status", "--short", "--branch")
    recent = run_git(root, "log", "-5", "--oneline", "--date=short")
    inventory = tracked_inventory(root)
    skills = skill_inventory(root)

    sections: list[str] = []
    sections.append(
        "# Workflow-assistance Context Pack\n\n"
        "Generated for a new Hermes Agent / CC Switch / Codex handoff. "
        "This is a project-local ignored artifact, not a committed source file.\n\n"
        f"- Generated UTC: `{now}`\n"
        f"- Project root: `{root}`\n"
        f"- Branch: `{branch}`\n"
        f"- HEAD: `{head}`\n"
        f"- Content SHA-256: `filled-after-render`\n"
    )
    sections.append(
        "## Safety Boundary\n\n"
        "- This pack is generated from tracked, allowlisted workflow assets plus git metadata.\n"
        "- It excludes `.env`, `auth.json`, `state.db`, `.hermes/`, logs, caches, installed dependencies and session data.\n"
        "- Secret-like values are redacted before rendering.\n"
        "- It strengthens the global Hermes Agent + CC Switch + Codex workflow; it is not proof that live Hermes has reloaded these assets.\n"
    )
    sections.append(f"## Git Status\n\n```text\n{status}\n```\n")
    sections.append(f"## Recent Commits\n\n```text\n{recent}\n```\n")
    sections.append(
        "## Portable Asset Inventory\n\n"
        + "\n".join(f"- `{item}`" for item in inventory)
        + ("\n- ... truncated ..." if len(inventory) >= 300 else "")
        + "\n"
    )
    sections.append(
        "## Skill Inventory\n\n"
        + ("\n".join(f"- `{item}`" for item in skills) if skills else "_No skills found._")
        + "\n"
    )
    sections.append(
        "## Handoff Reminders\n\n"
        "- Distinguish repo updated, live Hermes Home synced, and current session loaded.\n"
        "- Use `/reload-skills` or `/reset` after live skill/config changes when needed.\n"
        "- Gateway running is not the same as messaging platform delivery configured.\n"
        "- Keep one writer per checkout; context-pack generation is evidence/handoff, not completed product work by itself.\n"
        "- If output is used in another project, regenerate inside that project so paths and git evidence match.\n"
    )

    for relative in SELECTED_TEXT_FILES:
        text = read_safe_text(root, relative)
        if text is None:
            continue
        sections.append(
            f"## Excerpt: `{relative}`\n\n"
            f"```text\n{text.rstrip()}\n```\n"
        )

    content = "\n".join(sections).rstrip() + "\n"
    digest = sha256_text(content.replace("filled-after-render", ""))[:16]
    content = content.replace("filled-after-render", digest)
    if len(content) > max_chars:
        marker = f"\n\n[context pack truncated at {max_chars} characters]\n"
        content = content[: max_chars - len(marker)] + marker
    return content


def write_context_pack(root: Path, output: Path, max_chars: int) -> Path:
    root = canonical_path(root)
    if not output.is_absolute():
        output = root / output
    require_ignored_output(root, output)
    output = canonical_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    content = build_context_pack(root, max_chars=max_chars)
    output.write_text(content, encoding="utf-8")
    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a redacted, project-local context pack for Hermes/Codex handoff."
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Project path inside the target Git repository (default: cwd).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output file, relative to project root by default. Must be git-ignored.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help="Maximum rendered characters before truncation.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the rendered pack instead of writing the output file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not 1 <= args.max_chars <= HARD_MAX_CHARS:
        raise SystemExit(f"--max-chars must be between 1 and {HARD_MAX_CHARS}")
    root = git_root(args.project).resolve()
    if args.stdout:
        print(build_context_pack(root, max_chars=args.max_chars), end="")
        return 0
    output = write_context_pack(root, args.output, args.max_chars)
    relative = output.relative_to(canonical_path(root)).as_posix()
    print(f"context_pack={relative}")
    print(f"chars={len(output.read_text(encoding='utf-8'))}")
    print(f"utf8_bytes={output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
