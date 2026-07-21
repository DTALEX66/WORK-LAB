#!/usr/bin/env python
"""Install minimal, project-local Workflow-assistance governance into a Git repo."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


FILES = {
    ".hermes/README.md": """# Project-local Hermes runtime\n\nThis ignored directory contains only regenerable task runtime data, caches, logs and verification artifacts. Run project-writing commands through `hermes-project-data.py --project . run -- <command>`.\n""",
    ".hermes/BOOTSTRAP_MANIFEST.yaml": """schema_version: 1\nsource: Workflow-assistance\nfeatures:\n  - project_data_boundary\n  - context_pack\n  - local_quality_gate\ncredentials: not_copied\n""",
}


def git_root(target: Path) -> Path:
    result = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"target is not inside a Git repository: {target}")
    return Path(result.stdout.strip()).resolve()


def ignored(root: Path) -> bool:
    result = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--no-index", ".hermes/.probe"], check=False)
    return result.returncode == 0


def plan(root: Path) -> list[Path]:
    if not ignored(root):
        raise RuntimeError("target must ignore .hermes/ before bootstrap; add '.hermes/' to .gitignore")
    return [root / relative for relative in FILES]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap project-local Hermes workflow state without credentials.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    root = git_root(args.project)
    outputs = plan(root)
    if args.dry_run:
        print("BOOTSTRAP_DRY_RUN project=" + str(root))
        for output in outputs:
            print("would_write=" + output.relative_to(root).as_posix())
        return 0
    for relative, content in FILES.items():
        output = root / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print("BOOTSTRAP_WRITTEN=" + output.relative_to(root).as_posix())
    print("BOOTSTRAP_PASS project=" + str(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
