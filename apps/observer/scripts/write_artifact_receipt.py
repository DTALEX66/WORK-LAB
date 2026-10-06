#!/usr/bin/env python
"""Write a build-time input receipt next to the release binary.

ERR-105's remaining boundary was that a rollback to an older commit leaves
every input matching HEAD, so nothing in the tree evidences a change and a
superseded binary looks current. mtimes and `git diff` cannot see that; a
record of the bytes the build actually consumed can.

This is the build side's job, not the gate's: the writer runs immediately
after the compiler so the receipt attests to a build that was observed, and
`u19_webview_e2e.py` only ever reads it. A missing receipt is not an error —
the gate falls back to its content-evidence rule and says which basis decided.

v2 records two stages: the bytes the compiler consumed (rust, capabilities,
tauri.conf.json, the embedded dist) and the frontend build chain that produced
that bundle (source tree, entry html, vite/ts/postcss/tailwind configs, both
lockfiles, npm's installed-tree manifest). The second stage is what removes
the need for mtime between `frontend/src` and `frontend/dist`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

RECEIPT_SUFFIX = ".inputs.json"
RECEIPT_SCHEMA = "work-lab/artifact-input-receipt/v2"
# v1 recorded only the bytes the compiler consumed. The frontend chain that
# produced the embedded bundle was outside it, so an uncommitted edit with a
# back-dated mtime still rested on mtime (ERR-105 blind spot 2). v2 adds that
# stage. v1 receipts stay readable — discarding them would unattest a binary
# that is still the current one — but the gate must say which stage each covers.
RECEIPT_SCHEMA_V1 = "work-lab/artifact-input-receipt/v1"


def repo_root(script: Path) -> Path:
    current = script
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() and (parent / "services").is_dir():
            return parent
    raise SystemExit("WRITE_RECEIPT_FAIL cannot locate the WORK-LAB root")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_files(root: Path, obs: Path) -> list[Path]:
    """Every byte the compiler and tauri-build consume, in one sorted list."""
    groups = [
        sorted((obs / "src-tauri" / "src").rglob("*")),
        sorted((obs / "src-tauri" / "capabilities").rglob("*")),
        [obs / "src-tauri" / "Cargo.toml", obs / "src-tauri" / "Cargo.lock",
         obs / "src-tauri" / "build.rs", obs / "src-tauri" / "tauri.conf.json"],
        sorted((obs / "frontend" / "dist").rglob("*")),
    ]
    files: list[Path] = []
    for group in groups:
        for p in group:
            if p.is_file():
                files.append(p)
    return files


# The stage that produces the bundle the compiler embeds. vite reads the entry
# index.html, the source tree, both transform configs and whatever npm resolved
# into node_modules; a receipt that skips these cannot tell a current bundle
# from one built before the edit that should have rebuilt it.
FRONTEND_CHAIN_FILES = (
    "src",
    "index.html",
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "tsconfig.json",
    "postcss.config.js",
    "tailwind.config.js",
    "node_modules/.package-lock.json",
)


def frontend_chain_files(root: Path, obs: Path) -> list[Path]:
    """The frontend build chain's own inputs, in one sorted list."""
    frontend = obs / "frontend"
    files: list[Path] = []
    for name in FRONTEND_CHAIN_FILES:
        target = frontend / name
        if target.is_dir():
            files.extend(p for p in sorted(target.rglob("*")) if p.is_file())
        elif target.is_file():
            files.append(target)
    return files


def git_head(root: Path) -> str:
    done = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, errors="replace",
                          check=False)
    return done.stdout.strip() or "UNKNOWN"


def write_receipt(root: Path, obs: Path, exe: Path) -> dict:
    if not exe.is_file():
        raise SystemExit(f"WRITE_RECEIPT_FAIL no binary at {exe}")
    files = input_files(root, obs)
    if not files:
        raise SystemExit("WRITE_RECEIPT_FAIL no build inputs found")
    chain = frontend_chain_files(root, obs)
    receipt = {
        "schemaVersion": RECEIPT_SCHEMA,
        "writtenAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "gitHead": git_head(root),
        "binary": {"path": str(exe), "bytes": exe.stat().st_size,
                   "sha256": digest(exe)},
        "inputCount": len(files),
        "inputs": [{"path": p.relative_to(root).as_posix(),
                    "bytes": p.stat().st_size, "sha256": digest(p)}
                   for p in files],
        "frontendInputCount": len(chain),
        "frontendInputs": [{"path": p.relative_to(root).as_posix(),
                            "bytes": p.stat().st_size, "sha256": digest(p)}
                           for p in chain],
    }
    out = exe.with_name(exe.name + RECEIPT_SUFFIX)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    receipt["receiptPath"] = str(out)
    return receipt


def main() -> int:
    here = Path(__file__).resolve()
    root = repo_root(here)
    obs = root / "apps" / "observer"
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exe", default=None,
                    help="the binary just built; defaults to "
                         "$CARGO_TARGET_DIR or src-tauri/target release/app.exe")
    args = ap.parse_args()
    if args.exe:
        exe = Path(args.exe)
    else:
        import os
        target = os.environ.get("CARGO_TARGET_DIR")
        base = Path(target) if target else obs / "src-tauri" / "target"
        if not base.is_absolute():
            base = Path.cwd() / base
        exe = base / "release" / "app.exe"
    receipt = write_receipt(root, obs, exe)
    print(f"WRITE_RECEIPT_OK exe={receipt['binary']['sha256'][:16]} "
          f"inputs={receipt['inputCount']} "
          f"frontendInputs={receipt['frontendInputCount']} "
          f"gitHead={receipt['gitHead'][:9]} "
          f"receipt={receipt['receiptPath']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
