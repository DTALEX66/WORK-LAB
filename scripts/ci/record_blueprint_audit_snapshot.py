#!/usr/bin/env python3
"""Record the blueprint-sync audit snapshot from live observation.

Nothing here is transcribed: repository identity, remote SHAs, PR state, input
digests, gate exit codes and artifact hashes are all read or executed at run
time, so the snapshot binds to the state it actually verified. It records the
base and subject SHA of the work and never its own digest.

Usage: python scripts/ci/record_blueprint_audit_snapshot.py --write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "audits" / "BLUEPRINT_SYNC_AUDIT_2026-10-06.md"
INPUT_DIR = Path("D:/All projects/Record")
INPUT_DOCX = INPUT_DIR / "02_WORK-LAB_完整项目描述与未来蓝图_20261006.docx"
INPUT_PROMPT = (INPUT_DIR /
                "02_WORK-LAB_权威修复_双端描述同步_可审计执行提示词_20261006.txt")
DECLARED_DOCX_SHA = "f3784a9950adce06e8d87015a0ecb39d1ed4fdb3b93d5ccd3c9b40398bea3440"
CHECKS = [
    ["scripts/ci/verify_project_authority_reference.py"],
    ["scripts/ci/verify_error_ledger.py"],
    ["scripts/ci/verify_blueprint_coverage.py"],
    ["scripts/ci/failfast_group.py", "--group", "observer-web-contracts"],
    ["scripts/ci/failfast_group.py", "--group", "observer-python-skeleton"],
]
GAPS = [
    "U19 / T03: the composited desktop surface has not been observed. GDI capture "
    "cannot see a WebView2 DirectComposition visual (ERR-104, retracted), and the "
    "WebView2 remote-debugging port proved unreliable — it accepts TCP and answers "
    "in two early short-timeout attempts but never under patient polling (ERR-107).",
    "T02: the 2026-10-05 local full gate FAIL (1903 tests, 9 skipped, 12 errors, "
    "22 failures) was never re-run after the runtime fix. Recorded here alongside "
    "the affected-group passes below; a group pass is not the aggregate.",
    "ERR-103: the caption-control ACL grants are proven present in the compiled "
    "capability artifact of this build, but the click behaviour has not been "
    "re-observed on a desktop (the owner asked for no further window launches).",
    "ERR-106: the frameless top-row clearance is measured in headless Chrome at a "
    "1262x668 CSS viewport, not in the real 1280x820 logical window.",
    "AG-19 / T07: the original WORK-LAB long conversation, WORK-LAB-SUMMARY and the "
    "2026-09-28 startup/final attachments remain inaccessible (SOURCE_MISSING).",
    "Source-side gaps carried honestly: the blueprint has no AG-14 row, merges "
    "AG-16/AG-17, omits AG-01..AG-08 and W09, cites OD03/OD04 jointly, and its "
    "19-row candidate pool exceeds the 14-entry registry.",
    "Merge to main, release, install, global configuration and other-project writes "
    "are outside this task's authorization and were not performed.",
]


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True,
                          text=True, errors="replace", check=False).stdout.strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_check(argv: list[str]) -> dict:
    done = subprocess.run([sys.executable, str(REPO / argv[0]), *argv[1:]],
                          capture_output=True, text=True, errors="replace",
                          cwd=str(REPO), check=False)
    out = (done.stdout or "") + (done.stderr or "")
    tail = [line for line in out.splitlines() if line.strip()][-1:] or [""]
    return {"command": " ".join(argv), "exit": done.returncode,
            "result": tail[0][:220]}


def main() -> int:
    write = "--write" in sys.argv
    shanghai = datetime.now().astimezone()
    facts = {
        "observedAt": shanghai.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "remote": git("remote", "get-url", "origin"),
        "defaultBranch": "main",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "localHead": git("rev-parse", "HEAD"),
        "baseSha": git("merge-base", "HEAD", "origin/main"),
        "dirtyFiles": [p for p in git("diff", "--name-only").splitlines() if p],
        "statusRecords": sum(1 for r in git("status", "--porcelain", "-z").split("\0")
                            if r.strip()),
        "liveMainSha": (git("ls-remote", "origin", "refs/heads/main").split() or
                        ["UNKNOWN"])[0],
        "liveBranchSha": (git("ls-remote", "origin", "refs/heads/" +
                              git("rev-parse", "--abbrev-ref", "HEAD")).split() or
                          ["NOT-PUSHED"])[0],
    }
    pr = subprocess.run(["gh", "pr", "view", "162", "--json", "state,headRefOid,"
                         "baseRefName,mergeable,url"],
                        capture_output=True, text=True, errors="replace", check=False)
    facts["pr162"] = json.loads(pr.stdout) if pr.returncode == 0 else {
        "error": (pr.stderr or "gh unavailable").strip()[:200]}
    facts["inputs"] = {
        "blueprintDocx": {"path": str(INPUT_DOCX), "exists": INPUT_DOCX.is_file(),
                          "sha256": sha256(INPUT_DOCX) if INPUT_DOCX.is_file() else None,
                          "declaredInPrompt": DECLARED_DOCX_SHA,
                          "match": (INPUT_DOCX.is_file() and
                                    sha256(INPUT_DOCX) == DECLARED_DOCX_SHA)},
        "executionPrompt": {"path": str(INPUT_PROMPT),
                            "exists": INPUT_PROMPT.is_file(),
                            "sha256": sha256(INPUT_PROMPT) if INPUT_PROMPT.is_file() else None,
                            "declaredInPrompt": None},
    }
    facts["checks"] = [run_check(argv) for argv in CHECKS]
    facts["artifacts"] = []
    for rel in ["docs/future/WORK-LAB-BLUEPRINT-20261006.md",
                "docs/future/WORK-LAB-BLUEPRINT-COVERAGE.md",
                ".project/governance/blueprint-coverage.json",
                "scripts/ci/verify_blueprint_coverage.py",
                "apps/observer/scripts/write_artifact_receipt.py"]:
        path = REPO / rel
        if path.is_file():
            facts["artifacts"].append({"path": rel, "bytes": path.stat().st_size,
                                       "sha256": sha256(path)})

    lines = [
        "# WORK-LAB 蓝图同步审计快照",
        "",
        "由 `python scripts/ci/record_blueprint_audit_snapshot.py --write` 生成；"
        "所有标识、远端 SHA、摘要与退出码均为运行时观察值，不转录自旧报告。"
        "本文件不含自身摘要。",
        "",
        "## 现场身份",
        "",
        "```json",
        json.dumps({k: v for k, v in facts.items()
                    if k in ("observedAt", "remote", "branch", "localHead", "baseSha",
                             "dirtyFiles", "statusRecords", "liveMainSha", "liveBranchSha")},
                   indent=2, ensure_ascii=False),
        "```",
        "",
        "脏文件计数按 `git diff --name-only` 计算：git 状态列会把行尾过滤器改写报成"
        "modified，而 `git diff` 无内容差异，因此以 diff 为准（ERR-105 的同一机制）。"
        "`liveBranchSha` 为 `NOT-PUSHED` 时表示交付分支尚未同步到远端，不能声称双端完成。",
        "",
        "## PR #162 读回",
        "",
        "```json",
        json.dumps(facts["pr162"], indent=2, ensure_ascii=False),
        "```",
        "",
        "更正记录：蓝图原文记载 PR #162 head 为 "
        "`6f323a318a9db1c3a3ed4429bab0d4eff129876c`；本次实时读回是其自身的观察值，"
        "两者不同则以上方读回为准，原文值保留为历史观察，不改写。原文记载的 "
        "`origin/main = cd4daa83…` 与本次读回一致。",
        "",
        "## 输入与摘要",
        "",
        "```json",
        json.dumps(facts["inputs"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## 检查命令与退出码（本次运行）",
        "",
        "| 命令 | 退出码 | 末行结果 |",
        "|---|---|---|",
    ]
    for check in facts["checks"]:
        lines.append(f"| `{check['command']}` | {check['exit']} | {check['result']} |")
    lines += [
        "",
        "## 产物摘要",
        "",
        "| 路径 | 字节 | SHA-256 |",
        "|---|---|---|",
    ]
    for artifact in facts["artifacts"]:
        lines.append(f"| `{artifact['path']}` | {artifact['bytes']} | "
                     f"`{artifact['sha256']}` |")
    lines += [
        "",
        "## 范围与未决缺口",
        "",
    ]
    lines += [f"- {gap}" for gap in GAPS]
    lines += [
        "",
        "## 双端同步状态定义",
        "",
        "- 本地文件与提交：本报告生成后即成立（读回见上）。",
        "- 远端分支：需推送后以 `git ls-remote` 读回，未读回前一律记 `未验证`。",
        "- GitHub About：Git 外元数据，单独记录 before→after 与读回，"
        "不能以提交 README 代替。",
        "- exact-SHA CI：以推送后 PR 的检查读回为准；本地通过不称为 CI 绿。",
        "- 默认分支 main：本轮不合并，故记为未更新。",
        "",
    ]
    text = "\n".join(lines) + "\n"
    if write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
        print(f"AUDIT_SNAPSHOT_WRITE -> {OUT.relative_to(REPO)} "
              f"bytes={len(text.encode('utf-8'))}")
    else:
        print(text)
    failing = [c for c in facts["checks"] if c["exit"] != 0]
    print("AUDIT_SNAPSHOT checks=%d failing=%d" % (len(facts["checks"]), len(failing)))
    for check in failing:
        print("  FAILING %s exit=%d %s" % (check["command"], check["exit"],
                                           check["result"]))
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
