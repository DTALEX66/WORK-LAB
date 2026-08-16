# -*- coding: utf-8 -*-
"""GitHub delivery common layer (WL-DSH / GitHub Delivery Accelerator).

Shared credential acquisition (git credential fill, never hardcoded), API
requests, and the managed repository manifest for upload/review acceleration.
"""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
GITHUB_HOST = "github.com"

# Managed repositories in the D:\All projects workspace (local_path, repo).
# local_path is relative to the workspace root; repo is owner/name on GitHub.
WORKSPACE_ROOT = Path(r"D:\All projects")

MANAGED_REPOS = [
    {"local": "WORK-LAB", "repo": "DTALEX66/WORK-LAB"},
    {"local": "DESIGN-LAB", "repo": "DTALEX66/DESIGN-LAB"},
    {"local": "ArcheAxis-Knowledge-OS", "repo": "DTALEX66/ArcheAxis-Knowledge-OS"},
    {"local": "Obsidian-Assistance", "repo": "DTALEX66/Obsidian-Assistance"},
    {"local": "OS External Configuration", "repo": "DTALEX66/OS-configuration"},
]


def credential() -> str:
    """Get a GitHub token from the git credential manager (never hardcoded)."""
    result = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        timeout=20,
        check=True,
    )
    fields = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    token = fields.get("password")
    if not token:
        raise RuntimeError("Git credential manager returned no password")
    return token


def request(method: str, path: str, payload: dict | None = None,
            repo: str = "DTALEX66/WORK-LAB") -> dict:
    """Call the GitHub REST API with bearer auth."""
    token = credential()
    url = path if path.startswith("http") else f"{API}/repos/{repo}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def local_path(entry: dict) -> Path:
    return WORKSPACE_ROOT / entry["local"]


def git(repo_dir: Path, *args: str) -> str:
    """Run git in repo_dir, return stdout trimmed."""
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_ok(repo_dir: Path, *args: str) -> tuple[bool, str]:
    try:
        return True, git(repo_dir, *args)
    except RuntimeError:
        return False, ""


if __name__ == "__main__":
    print(f"managed repos: {len(MANAGED_REPOS)}")
    for e in MANAGED_REPOS:
        d = local_path(e)
        print(f"  {e['local']:30s} git={'YES' if (d/'.git').exists() else 'NO'} remote={git_ok(d, 'remote', 'get-url', 'origin')[1][:60]}")
    tok = credential()
    print(f"credential: {'OK (' + tok[:4] + '...)' if tok else 'FAIL'}")
