#!/usr/bin/env python3
"""Generate Open Design assistance index files."""

from __future__ import annotations

import json
from pathlib import Path

ASSISTANCE_DIR = "opendesign-assistance"

CATEGORY_LABELS = {
    "brand": "Brand / 品牌",
    "decks": "Decks / 演示",
    "design-systems": "Design Systems / 风格参考",
    "graphic": "Graphic / 平面",
    "layouts": "Layouts / UIUX",
    "motion": "Motion / 动效",
    "qa": "QA / 审查",
    "spatial": "Spatial / 文化墙展厅",
    "typography": "Typography / 排版",
    "visual": "Visual / 2D/3D",
    "config": "Config / 配置",
}


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ASSISTANCE_DIR).is_dir() and (parent / ".git").exists():
            return parent
    raise SystemExit("Could not locate repository root")


def first_heading(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def first_paragraph(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    heading_seen = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            heading_seen = True
            continue
        if not heading_seen:
            continue
        if not stripped:
            if collected:
                break
            continue
        if stripped.startswith("## "):
            break
        collected.append(stripped)
    return " ".join(collected)[:220]


def plugin_row(plugin_dir: Path, root: Path) -> str:
    manifest = json.loads((plugin_dir / "open-design.json").read_text(encoding="utf-8"))
    od = manifest.get("od") or {}
    name = manifest.get("name", plugin_dir.name)
    title = manifest.get("title", name)
    categories = ", ".join(od.get("categories") or [])
    capabilities = ", ".join(od.get("capabilities") or [])
    inputs = ", ".join(od.get("suggestedInputs") or [])
    rel = (plugin_dir / "README.md").relative_to(root).as_posix()
    return f"| [`{name}`]({rel}) | {title} | {categories} | {capabilities} | {inputs} |"


def generate_plugins_index(root: Path) -> None:
    plugins_dir = root / ASSISTANCE_DIR / "plugins"
    rows = [plugin_row(path, root) for path in sorted(plugins_dir.iterdir()) if (path / "open-design.json").is_file()]
    content = "\n".join([
        "# Open Design plugin index",
        "",
        "Generated from `opendesign-assistance/plugins/*/open-design.json`.",
        "",
        "Run:",
        "",
        "```bash",
        "python opendesign-assistance/scripts/generate_open_design_indexes.py",
        "```",
        "",
        "| Plugin | Title | Categories | Capabilities | Suggested inputs |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ])
    (plugins_dir / "INDEX.md").write_text(content, encoding="utf-8")


def generate_templates_index(root: Path) -> None:
    templates_dir = root / ASSISTANCE_DIR / "templates"
    sections: dict[str, list[str]] = {}
    for path in sorted(templates_dir.rglob("*.md")):
        if path.name == "INDEX.md":
            continue
        parts = path.relative_to(templates_dir).parts
        category = parts[0] if len(parts) > 1 else "config"
        label = CATEGORY_LABELS.get(category, category.title())
        rel = path.relative_to(root).as_posix()
        title = first_heading(path)
        desc = first_paragraph(path)
        sections.setdefault(label, []).append(f"- [`{title}`]({rel}) — {desc}")

    lines = [
        "# Open Design template index",
        "",
        "Generated from `opendesign-assistance/templates/**/*.md`.",
        "",
        "Use this as the quick map for choosing local Open Design capability templates.",
        "",
    ]
    for label in sorted(sections):
        lines.extend([f"## {label}", "", *sections[label], ""])
    (templates_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = repo_root()
    generate_plugins_index(root)
    generate_templates_index(root)
    print("generated opendesign-assistance/plugins/INDEX.md")
    print("generated opendesign-assistance/templates/INDEX.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
