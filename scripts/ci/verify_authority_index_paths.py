#!/usr/bin/env python3
"""Every path-shaped reference in a navigation surface must resolve in the TRACKED tree, or be declared.

Two deliberate choices, both learned the hard way in this repo.

Resolution is against `git ls-files`, never against the filesystem. An ignored directory such as
`.project-local/` exists on the machine that wrote the sentence and does not exist on a fresh checkout, so
a filesystem test makes the verdict host-dependent -- the same class of defect as an authorization decision
computed with `Path.resolve()`. A directory reference counts as real when at least one tracked file sits
under it.

Why this exists: the authority index is the navigation surface for the whole chain and nothing checked it.
Measured on 2026-10-08 before the fix, section 3 sent readers to `docs/handoffs/` and `docs/audit/`,
directories that have not existed since the 2026-09 convergence, and section 2 named the config standard
without the date suffix that both the file on disk and AGENTS.md carry.

`--index` may be repeated and defaults to both guarded surfaces, so a new one joins by being named and a
planted copy is how the rule is shown firing without editing real files.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from posixpath import normpath

DEFAULT_TARGETS = (
    "docs/current/workflow-assistance/workflow/active-authority-index.md",
    "docs/current/workflow-assistance-README.md",
    "docs/current/workflow-assistance-TROUBLESHOOTING.md",
    "docs/current/workflow-assistance/workflow/project-definition.md",
)
FILE_REF = re.compile(r"`([^`\s]*/[^`\s]*\.(?:md|json|py|ts|tsx|yml|yaml|example|lock|txt|sh|bash|ps1))`")
DIR_REF = re.compile(r"`([^`\s]+/)`")
FENCE = re.compile(r"^```(\w*)")
# a reference containing one of these is not a name the tree can answer to, so it is never even tried
PLACEHOLDER_MARKERS = ("<", ">", "*", "$", "~")
LOWER_SEGMENT = re.compile(r"^[a-z0-9._-]+$")


def looks_like_path(ref: str) -> bool:
    """Reject backticked terms that merely contain a slash.

    Two real cases decided this rule. `GUI/TUI` in the troubleshooting doc is a mode pair and would
    otherwise fire as a missing file. `/WORK-LAB-AUTHORITY.md` is the top-level authority itself, written
    root-absolute: a rule that required a lowercase first *character* dropped it silently, which is worse
    than a false positive because the checker would then claim to guard a surface while excluding its most
    important pointer.
    """
    if ref.startswith(("/", "./", "../")):
        return True
    if not ref or ref[0].isupper():
        return False
    first = ref.split("/", 1)[0]
    return bool(LOWER_SEGMENT.match(first))

# Declared non-repo references, each with the measured reason. A declaration whose path starts resolving
# in the tracked tree is itself a failure, so this list cannot quietly become a hiding place.
DECLARED_NON_PATHS: dict[str, str] = {
    ".project-local/": "the git-ignored in-boundary runtime and evidence root; nothing under it is "
                       "tracked by design, so it must never be judged against git ls-files",
}
# This list is deliberately one entry long. It used to also declare `skills/`, `bin/` and
# `.codex/AGENTS.md`, and that turned out to be a bug in the checker rather than in the docs: the README
# wrote those bare names for the user's Hermes Home and Codex home, while the same spellings appeared in
# 仓库结构 meaning repository directories. One string-keyed declaration cannot tell the two referents
# apart, so it hid the stale map entry. The prose now says `$HERMES_HOME/skills/`, `$HERMES_HOME/bin/` and
# `$CODEX_HOME/AGENTS.md` -- the notation this repo already uses elsewhere -- and a placeholder is skipped
# rather than excused.


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() and (parent / "services").is_dir():
            return parent
    raise SystemExit("AUTHORITY_INDEX_PATHS_FAIL cannot locate WORK-LAB root")


def tracked_paths(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, check=True).stdout
    return [line.decode("utf-8", "replace").strip() for line in out.splitlines() if line.strip()]


def references(text: str) -> list[tuple[int, str, str]]:
    """Backticked references, plus the first-column token of a language-less fenced map.

    A directory map written in a fenced block is normative prose -- the README's 仓库结构 listed `bin/`,
    `skills/` and `scripts/workflow/` as repository directories with no backticks around them, and a
    backtick-only reader would have called that clean. Only the leading token counts, because that is how
    an aligned map writes its path, and only in an unlabelled or `text` fence: a ```bash transcript's first
    token is a command or an output fragment (`usr/bin/bash:`, `d/All\`), not a claim about the tree.
    """
    rows: list[tuple[int, str, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        opener = FENCE.match(line.strip())
        if opener:
            if fence is None:
                fence = (opener.group(1) or "text").lower()
            else:
                fence = None
            continue
        for match in FILE_REF.finditer(line):
            if looks_like_path(match.group(1)):
                rows.append((number, match.group(1), "file"))
        for match in DIR_REF.finditer(line):
            if looks_like_path(match.group(1)):
                rows.append((number, match.group(1), "directory"))
        if fence not in ("text", "markdown", "md") or not line.strip():
            continue
        token = line.strip().split()[0]
        if "/" not in token or not looks_like_path(token):
            continue
        if token.endswith(":") or "\\" in token:
            continue
        if token in {row[1] for row in rows if row[0] == number}:
            continue
        rows.append((number, token, "directory" if token.endswith("/") else "file"))
    return rows


def is_placeholder(ref: str) -> bool:
    return any(marker in ref for marker in PLACEHOLDER_MARKERS)


def anchored(target: str, ref: str) -> str:
    """Repo-relative form of a reference, resolving `../` against the surface that writes it.

    The README links `../../.github/workflows/work-lab-gate.yml` from `docs/current/`, which is a real
    tracked file once the dots are folded; judging the literal string would call it missing.
    """
    rel = ref.lstrip("/")  # a leading slash here means repo-root-relative, not a filesystem root
    if ".." not in rel:
        return rel
    # PurePosixPath keeps `..` segments untouched, so the folding is done by normpath
    return normpath(PurePosixPath(PurePosixPath(target).parent / rel).as_posix())


def declared(ref: str) -> str | None:
    """The declaration covering this reference: exact, or an untracked directory prefix."""
    if ref in DECLARED_NON_PATHS:
        return ref
    for entry in DECLARED_NON_PATHS:
        if entry.endswith("/") and (ref == entry or ref.startswith(entry)):
            return entry
    return None


def resolves(tracked: list[str], ref: str, kind: str) -> bool:
    if kind == "directory":
        return any(path.startswith(ref) for path in tracked)
    return ref in tracked


def check(root: Path, tracked: list[str], target: str) -> tuple[list, list, list]:
    """(considered rows, broken rows, stale declarations) for one surface, or ([], [], []) if absent."""
    index = root / target
    if not index.is_file():
        return [], [], []
    rows = []
    for number, ref, kind in references(index.read_text(encoding="utf-8")):
        if is_placeholder(ref):
            continue
        rows.append((number, anchored(target, ref), kind))
    broken = [row for row in rows
              if declared(row[1]) is None and not resolves(tracked, row[1], row[2])]
    # a declaration goes stale when the tree contradicts what it asserted, so the test is run on the
    # declaration itself: ".project-local/" means "nothing under here is tracked", and one tracked file
    # under it makes the whole entry false regardless of which child row mentioned it
    stale = [(0, entry, "directory" if entry.endswith("/") else "file") for entry in DECLARED_NON_PATHS
             if resolves(tracked, entry.rstrip("/") + "/" if entry.endswith("/") else entry,
                         "directory" if entry.endswith("/") else "file")]
    return rows, broken, stale


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", action="append", default=None,
                    help="repo-relative markdown surface to check; repeatable")
    args = ap.parse_args(argv)

    root = repo_root()
    targets = args.index or list(DEFAULT_TARGETS)
    tracked = tracked_paths(root)
    if not tracked:
        print("AUTHORITY_INDEX_PATHS_FAIL git ls-files returned nothing -- nothing can resolve against "
              "an empty tracked set, which is a broken checker, not a clean tree")
        return 1

    failed_targets = 0
    total_refs = total_broken = 0
    for target in targets:
        rows, broken, stale = check(root, tracked, target)
        if not rows:
            print(f"AUTHORITY_INDEX_PATHS_FAIL {target} yielded refs=0 -- either the file is missing or "
                  "the extractor matched nothing; neither is a pass")
            failed_targets += 1
            continue
        total_refs += len(rows)
        total_broken += len(broken)
        kinds: dict[str, int] = {}
        for _, _, kind in rows:
            kinds[kind] = kinds.get(kind, 0) + 1
        flag = "FAIL" if broken or stale else "PASS"
        print(f"AUTHORITY_INDEX_PATHS_{flag} target={target} refs={len(rows)} "
              f"files={kinds.get('file', 0)} directories={kinds.get('directory', 0)} "
              f"broken={len(broken)} declared={len(DECLARED_NON_PATHS)} "
              f"declared_but_tracked={len(stale)}")
        for number, ref, kind in broken:
            print(f"  line {number}: `{ref}` is not a tracked {kind}")
        for _, ref, _ in stale:
            print(f"  declared as non-repo but tracked now: {ref} -- drop the declaration")
        failed_targets += 1 if (broken or stale) else 0

    print(f"AUTHORITY_INDEX_PATHS_TOTAL targets={len(targets)} refs={total_refs} "
          f"broken={total_broken} failed_targets={failed_targets}")
    return 1 if failed_targets else 0


if __name__ == "__main__":
    raise SystemExit(main())
