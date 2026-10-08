#!/usr/bin/env python3
"""Gate: may this commit be pushed? Only if a full-gate receipt names it and says GATE_EXIT=0.

Why this exists: the ordering rule (commit -> verify at HEAD -> push) has been broken three times,
twice by me. ERR-181 pushed a head whose own gate run had already reported red, because the wrapper's
exit code was read instead of the receipt. This one was pushed after a governance-only run. A receipt
that does not say which head it describes cannot answer "was THIS head verified", so
`run_quality_gate.py` now stamps `GATE_HEAD=<sha>` into its own output and this tool matches it.

Verdicts, each with a distinct exit code so a caller cannot mistake one for another:
  PUSH_PERMIT_OK            0   a receipt names this head and carries GATE_EXIT=0
  PUSH_PERMIT_REFUSE        1   NO_RECEIPT / RECEIPT_RED / NO_EXIT_LINE / NOT_A_COMMIT
  PUSH_PERMIT_NOT_RUN       3   the tool itself cannot work (no runs dir, git missing)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE_HEAD = re.compile(r"^GATE_HEAD=([0-9a-f]{40})\b", re.MULTILINE)
GATE_EXIT = re.compile(r"^GATE_EXIT=(-?\d+)\s*$", re.MULTILINE)
GATE_FULL = re.compile(r"GATE_FULL=(\w+)")


def resolve(head: str, cwd: Path) -> str | None:
    """Expand a short sha to the 40-hex form receipts carry, or None if git refuses it."""
    out = subprocess.run(["git", "rev-parse", "--verify", f"{head}^{{commit}}"],
                         cwd=cwd, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    value = (out.stdout or "").strip()
    return value if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None


def receipts(runs: Path) -> list[Path]:
    if not runs.is_dir():
        return []
    return sorted(p for p in runs.rglob("*.log") if p.is_file())


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def shown(path: Path) -> str:
    """Repo-relative when it is inside the repo, absolute otherwise (a temp receipt in a test)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def decide(head: str, files: list[Path], allow_partial: bool = False) -> tuple[int, str]:
    """Pure: the verdict for one head against a set of receipt files.

    A receipt that ran one cheap gate is not evidence that the head was verified, so GATE_FULL=yes is
    part of what makes a receipt count. Receipts that name the head but are partial are reported as
    their own verdict rather than folded into NO_RECEIPT, because "verified narrowly" and "never run"
    need different next actions.
    """
    matching = [(p, read(p)) for p in files]
    naming = [(p, body) for p, body in matching if f"GATE_HEAD={head}" in body]
    partial = [(p, b) for p, b in naming if "GATE_FULL=yes" not in b]
    full = [(p, b) for p, b in naming if "GATE_FULL=yes" in b]
    if not naming:
        seen = {m.group(1) for _, b in matching for m in [GATE_HEAD.search(b)] if m}
        return 1, (f"PUSH_PERMIT_REFUSE NO_RECEIPT head={head[:8]} receipts={len(files)} "
                   f"heads_with_receipts={len(seen)} — this head has never been through a full gate")
    if not full and not allow_partial:
        kinds = sorted({m.group(1) for _, b in partial for m in [GATE_FULL.search(b)] if m})
        return 1, (f"PUSH_PERMIT_REFUSE PARTIAL_ONLY head={head[:8]} receipts={len(partial)} "
                   f"gates_run={kinds or ['unstamped']} — a narrow run does not verify a head; "
                   f"pass --allow-partial only when that is genuinely what you mean")
    if not full:
        full = partial
    def is_green(body: str) -> bool:
        exits = GATE_EXIT.findall(body)
        return bool(exits) and exits[-1] == "0"

    greens = [(p, b) for p, b in naming if is_green(b)]
    if greens:
        return 0, f"PUSH_PERMIT_OK head={head[:8]} receipt={shown(greens[0][0])}"
    first_path, first_body = naming[0]
    exits = GATE_EXIT.findall(first_body)
    if not exits:
        return 1, (f"PUSH_PERMIT_REFUSE NO_EXIT_LINE head={head[:8]} "
                   f"receipt={first_path.name} — the file records no completion line, so the run is "
                   f"either still live or was killed; an absent verdict is not a pass")
    return 1, (f"PUSH_PERMIT_REFUSE RECEIPT_RED head={head[:8]} GATE_EXIT={exits[-1]} "
               f"receipt={shown(first_path)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", required=True, help="the commit about to be pushed (any rev-parse form)")
    ap.add_argument("--runs", default=str(ROOT / ".project-local" / "runs"))
    ap.add_argument("--allow-partial", action="store_true",
                    help="accept a receipt that ran fewer than the full gate set")
    args = ap.parse_args(argv)

    full = resolve(args.head, ROOT)
    if full is None:
        print(f"PUSH_PERMIT_REFUSE NOT_A_COMMIT {args.head!r} does not resolve in {ROOT}")
        return 1
    if not Path(args.runs).is_dir():
        print(f"PUSH_PERMIT_NOT_RUN no runs directory at {args.runs}")
        return 3
    code, message = decide(full, receipts(Path(args.runs)), allow_partial=args.allow_partial)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
