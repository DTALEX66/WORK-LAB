#!/usr/bin/env python3
"""Verify OPEN-DESIGN-Assistance integration assets.

This is a focused repository validator for the Open Design assistance layer:
plugins, template references, design-system manifests, visual-pack paths, and
key documentation links. It intentionally uses only the Python standard library.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PLUGIN_SCHEMA = "https://open-design.ai/schemas/plugin.v1.json"
ASSISTANCE_DIR = "opendesign-assistance"


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> object:
    return json.loads(read_text(path))


def check(results: list[Result], label: str, ok: bool, detail: str = "") -> None:
    results.append(Result(label, ok, detail))


def require_file(results: list[Result], root: Path, rel: str, min_bytes: int = 1) -> Path:
    path = root / rel
    check(results, f"exists: {rel}", path.is_file())
    size = path.stat().st_size if path.exists() else 0
    check(results, f"non-empty: {rel}", size >= min_bytes, str(size))
    return path


def iter_plugin_dirs(root: Path) -> Iterable[Path]:
    plugins_dir = root / ASSISTANCE_DIR / "plugins"
    return sorted(path for path in plugins_dir.iterdir() if path.is_dir())


def verify_plugin_manifests(root: Path, results: list[Result]) -> None:
    plugins = list(iter_plugin_dirs(root))
    check(results, "at least one Open Design plugin exists", bool(plugins), str(len(plugins)))

    for plugin_dir in plugins:
        name = plugin_dir.name
        manifest_path = plugin_dir / "open-design.json"
        skill_path = plugin_dir / "SKILL.md"
        readme_path = plugin_dir / "README.md"

        check(results, f"plugin {name}: open-design.json exists", manifest_path.is_file())
        check(results, f"plugin {name}: SKILL.md exists", skill_path.is_file())
        check(results, f"plugin {name}: README.md exists", readme_path.is_file())
        if not manifest_path.is_file():
            continue

        try:
            manifest = load_json(manifest_path)
            check(results, f"plugin {name}: manifest JSON parses", isinstance(manifest, dict))
        except Exception as exc:  # noqa: BLE001 - verifier reports any parse issue.
            check(results, f"plugin {name}: manifest JSON parses", False, str(exc))
            continue

        od = manifest.get("od") if isinstance(manifest, dict) else None
        od = od if isinstance(od, dict) else {}
        capabilities = od.get("capabilities") or []
        categories = od.get("categories") or []
        suggested_inputs = od.get("suggestedInputs") or []

        check(results, f"plugin {name}: schema", manifest.get("$schema") == PLUGIN_SCHEMA, str(manifest.get("$schema")))
        check(results, f"plugin {name}: specVersion", manifest.get("specVersion") == "1.0.0", str(manifest.get("specVersion")))
        check(results, f"plugin {name}: name matches directory", manifest.get("name") == name, str(manifest.get("name")))
        check(results, f"plugin {name}: version present", bool(manifest.get("version")), str(manifest.get("version")))
        check(results, f"plugin {name}: entry is SKILL.md", manifest.get("entry") == "SKILL.md", str(manifest.get("entry")))
        check(results, f"plugin {name}: od.kind is skill", od.get("kind") == "skill", str(od.get("kind")))
        check(results, f"plugin {name}: prompt injection capability", "prompt:inject" in capabilities, str(capabilities))
        check(results, f"plugin {name}: categories present", bool(categories), str(categories))
        check(results, f"plugin {name}: suggested inputs present", bool(suggested_inputs), str(suggested_inputs))


def referenced_local_paths(text: str) -> set[str]:
    pattern = re.compile(r"opendesign-assistance/[A-Za-z0-9_./-]+\.(?:md|json|html|py)")
    return set(pattern.findall(text))


def verify_skill_references(root: Path, results: list[Result]) -> None:
    for plugin_dir in iter_plugin_dirs(root):
        skill_path = plugin_dir / "SKILL.md"
        if not skill_path.is_file():
            continue
        rel_skill = skill_path.relative_to(root).as_posix()
        for rel_ref in sorted(referenced_local_paths(read_text(skill_path))):
            check(results, f"{rel_skill} reference exists: {rel_ref}", (root / rel_ref).exists())


def verify_templates(root: Path, results: list[Result]) -> None:
    templates_dir = root / ASSISTANCE_DIR / "templates"
    template_files = sorted(templates_dir.rglob("*.md"))
    check(results, "template library has markdown files", bool(template_files), str(len(template_files)))

    required_terms = {
        "templates/qa/anti-ai-slop-checklist.md": ["Hard fails", "Scorecard", "Reject below"],
        "templates/layouts/landing-page.md": ["Required structure", "hero", "CTA"],
        "templates/layouts/dashboard.md": ["Information architecture", "card soup"],
        "templates/layouts/mobile-menu.md": ["bottom tabs", "danger"],
        "templates/layouts/settings-panel.md": ["danger zone", "unsaved changes"],
        "templates/layouts/pricing-page.md": ["recommended plan", "feature comparison"],
        "templates/layouts/product-page.md": ["product surface", "feature proof"],
        "templates/graphic/poster-cover.md": ["composition", "xiaohongshu"],
        "templates/graphic/social-card.md": ["thumbnail-readable", "safe margins"],
        "templates/decks/pitch-deck.md": ["Six-slide bootstrap", "claim-based"],
        "templates/motion/motion-system.md": ["Motion tokens", "reduced-motion"],
        "templates/typography/cjk-ui-typography.md": ["PingFang SC", "Microsoft YaHei"],
        "templates/design-systems/style-reference-index.md": ["Stripe", "Linear", "Nothing"],
        "templates/brand/brand-identity-system.md": ["品牌", "Visual territory"],
        "templates/spatial/culture-wall.md": ["文化墙", "viewing distance"],
        "templates/spatial/exhibition-hall.md": ["展厅", "Visitor journey"],
        "templates/visual/art-direction.md": ["Visual design", "Three art directions"],
        "templates/visual/2d-design.md": ["2D design", "Export specs"],
        "templates/visual/3d-design.md": ["3D design", "scale references"],
    }

    for rel_suffix, terms in required_terms.items():
        rel = f"{ASSISTANCE_DIR}/{rel_suffix}"
        path = require_file(results, root, rel, min_bytes=500)
        text = read_text(path) if path.is_file() else ""
        text_lower = text.lower()
        for term in terms:
            check(results, f"{rel} includes {term}", term.lower() in text_lower)

    large = [str(path.relative_to(root)) for path in template_files if path.stat().st_size > 100_000]
    check(results, "template library has no large vendored files", not large, str(large))


def verify_design_systems(root: Path, results: list[Result]) -> None:
    base = root / ASSISTANCE_DIR / "design-systems" / "anomaly-monitor-dark"
    if not base.exists():
        check(results, "anomaly-monitor-dark design system exists", False)
        return

    manifest_path = base / "manifest.json"
    require_file(results, root, str(manifest_path.relative_to(root)))
    try:
        manifest = load_json(manifest_path)
        check(results, "anomaly-monitor-dark manifest parses", isinstance(manifest, dict))
    except Exception as exc:  # noqa: BLE001
        check(results, "anomaly-monitor-dark manifest parses", False, str(exc))
        return

    files = manifest.get("files", [])
    if isinstance(files, dict):
        file_refs = files.values()
    else:
        file_refs = files
    for rel in file_refs:
        check(results, f"design system file exists: {rel}", (base / str(rel)).exists())

    for rel in ["design-tokens.json", "components.manifest.json"]:
        try:
            load_json(base / rel)
            check(results, f"design system JSON parses: {rel}", True)
        except Exception as exc:  # noqa: BLE001
            check(results, f"design system JSON parses: {rel}", False, str(exc))


def verify_visual_packs(root: Path, results: list[Result]) -> None:
    manifest_path = root / ASSISTANCE_DIR / "assets" / "visual-packs" / "anomaly-monitor-cctv" / "manifest.json"
    require_file(results, root, str(manifest_path.relative_to(root)))
    try:
        manifest = load_json(manifest_path)
        check(results, "visual pack manifest parses", isinstance(manifest, dict))
    except Exception as exc:  # noqa: BLE001
        check(results, "visual pack manifest parses", False, str(exc))
        return

    assets = manifest.get("assets") or []
    ids = [asset.get("id") for asset in assets if isinstance(asset, dict)]
    check(results, "visual pack has eight retained assets", len(assets) == 8, str(len(assets)))
    check(results, "visual pack asset ids are unique", len(ids) == len(set(ids)), str(ids))
    for asset in assets:
        if not isinstance(asset, dict):
            check(results, "visual pack asset shape", False, str(asset))
            continue
        rel_path = asset.get("path")
        resolved = (manifest_path.parent / rel_path).resolve() if rel_path else manifest_path.parent
        check(results, f"visual pack path exists: {asset.get('id')}", resolved.exists(), str(resolved))


def png_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def verify_exports(root: Path, results: list[Result]) -> None:
    export = root / ASSISTANCE_DIR / "exports" / "minigame-mobile-controls"
    require_file(results, root, str((export / "README.md").relative_to(root)), min_bytes=500)
    html = require_file(results, root, str((export / "index.html").relative_to(root)), min_bytes=20_000)
    require_file(results, root, str((export / "implementation-handoff.md").relative_to(root)), min_bytes=300)
    require_file(results, root, str((export / "critique.json").relative_to(root)), min_bytes=300)
    require_file(results, root, str((export / "index.html.artifact.json").relative_to(root)), min_bytes=100)
    require_file(results, root, str((export / ".open-design" / "project.json").relative_to(root)), min_bytes=100)

    html_text = read_text(html) if html.is_file() else ""
    check(results, "minigame export uses local asset paths", "../../MINIGAME" not in html_text)
    expected_assets = [
        "cctv-elevator-corridor-clear.png",
        "cctv-elevator-corridor-warp.png",
        "cctv-elevator-corridor-figure.png",
    ]
    for name in expected_assets:
        rel = f"opendesign-assistance/exports/minigame-mobile-controls/assets/{name}"
        asset = require_file(results, root, rel, min_bytes=500_000)
        check(results, f"minigame export html references {name}", f"assets/{name}" in html_text)
        size = png_size(asset) if asset.is_file() else None
        check(results, f"minigame export PNG dimensions readable: {name}", bool(size), str(size))


def verify_json_files(root: Path, results: list[Result]) -> None:
    errors: list[str] = []
    for path in (root / ASSISTANCE_DIR).rglob("*.json"):
        try:
            load_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.relative_to(root)}: {exc}")
    check(results, "all opendesign-assistance JSON files parse", not errors, "\n".join(errors))


def verify_indexes(root: Path, results: list[Result]) -> None:
    plugins_index = root / ASSISTANCE_DIR / "plugins" / "INDEX.md"
    templates_index = root / ASSISTANCE_DIR / "templates" / "INDEX.md"
    require_file(results, root, str(plugins_index.relative_to(root)), min_bytes=500)
    require_file(results, root, str(templates_index.relative_to(root)), min_bytes=500)

    plugins_text = read_text(plugins_index) if plugins_index.is_file() else ""
    for plugin_dir in iter_plugin_dirs(root):
        if (plugin_dir / "open-design.json").is_file():
            check(results, f"plugins index mentions {plugin_dir.name}", plugin_dir.name in plugins_text)

    templates_text = read_text(templates_index) if templates_index.is_file() else ""
    required_sections = [
        "Brand / 品牌",
        "Graphic / 平面",
        "Layouts / UIUX",
        "Spatial / 文化墙展厅",
        "Visual / 2D/3D",
        "QA / 审查",
    ]
    for section in required_sections:
        check(results, f"templates index has section {section}", section in templates_text)


def verify_scripts(root: Path, results: list[Result]) -> None:
    scripts = [
        "opendesign-assistance/scripts/verify_open_design_assistance.py",
        "opendesign-assistance/scripts/generate_open_design_indexes.py",
        "opendesign-assistance/scripts/scaffold_open_design_plugin.py",
    ]
    import py_compile

    for rel in scripts:
        path = require_file(results, root, rel, min_bytes=500)
        try:
            py_compile.compile(str(path), doraise=True)
            check(results, f"script compiles: {rel}", True)
        except Exception as exc:  # noqa: BLE001
            check(results, f"script compiles: {rel}", False, str(exc))


def verify_docs(root: Path, results: list[Result]) -> None:
    required_refs = [
        "opendesign-assistance/plugins/brand-visual-director/README.md",
        "opendesign-assistance/plugins/spatial-exhibition-director/README.md",
        "opendesign-assistance/templates/spatial/culture-wall.md",
        "opendesign-assistance/templates/visual/3d-design.md",
        "opendesign-assistance/scripts/verify_open_design_assistance.py",
        "opendesign-assistance/scripts/generate_open_design_indexes.py",
        "opendesign-assistance/scripts/scaffold_open_design_plugin.py",
        "opendesign-assistance/plugins/INDEX.md",
        "opendesign-assistance/templates/INDEX.md",
        "opendesign-assistance/usage-notes/OPEN_DESIGN_PLUGIN_INSTALL.md",
        "opendesign-assistance/exports/minigame-mobile-controls/README.md",
    ]
    root_readme = root / "README.md"
    assistance_readme = root / ASSISTANCE_DIR / "README.md"
    texts = {
        "README.md": read_text(root_readme) if root_readme.exists() else "",
        f"{ASSISTANCE_DIR}/README.md": read_text(assistance_readme) if assistance_readme.exists() else "",
    }
    for rel in required_refs:
        present = any(rel in text for text in texts.values())
        check(results, f"docs mention {rel}", present)


def print_results(results: list[Result]) -> int:
    failed = [result for result in results if not result.ok]
    for result in results:
        prefix = "PASS" if result.ok else "FAIL"
        print(f"{prefix} {result.label}")
        if result.detail:
            print(f"  {result.detail}")
    print(f"\nVERIFY_RESULT={'OK' if not failed else 'FAIL'} total={len(results)} failed={len(failed)}")
    return 0 if not failed else 1


def main() -> int:
    root = repo_root()
    results: list[Result] = []
    verify_plugin_manifests(root, results)
    verify_skill_references(root, results)
    verify_templates(root, results)
    verify_design_systems(root, results)
    verify_visual_packs(root, results)
    verify_exports(root, results)
    verify_json_files(root, results)
    verify_indexes(root, results)
    verify_scripts(root, results)
    verify_docs(root, results)
    return print_results(results)


if __name__ == "__main__":
    raise SystemExit(main())
