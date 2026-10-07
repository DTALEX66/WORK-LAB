"""Read-only triage of the ledger's unbound PASS records.

95 records claim PASS but carry no fixedCommit, so nothing pins which change made them true. This partitions
them by what is checkable today: whether the record's own regression command points at a file that exists,
and when that file entered the tree relative to the record's date.

It binds nothing. A fix commit is only honest when the record points at it; where the guard file predates
the record by many commits the candidate is ambiguous and must be decided per record, not in a batch — that
is the ERR-16 failure mode (a binder generating plausible provenance faster than a gate can reject it).
"""
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "taskpacks/current/error-ledger.json"
TARGETS = ROOT / "docs/audits/LEDGER_REGRESSION_COMMAND_TARGETS_2026-10-07.json"
OUT = ROOT / "docs/audits/LEDGER_UNBOUND_TRIAGE_2026-10-07.json"
# A guard file added within this many days of the record is treated as a same-round fix, so the binding
# candidate is the commit that introduced it rather than one of the later commits that merely touched it.
CLEAR_WINDOW_DAYS = 3

ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
targets = json.loads(TARGETS.read_text(encoding="utf-8"))
state_of = {r["errorId"]: r for r in targets["rows"]}
records = {e["error_id"]: e for e in ledger["errors"]}

unbound = [eid for eid, e in records.items()
           if e.get("status_after") == "PASS"
           and not (e.get("lifecycle") or {}).get("fixedCommit")]

first_commit_cache: dict[str, tuple[str, str]] = {}


def first_commit(path: str) -> tuple[str, str]:
    if path not in first_commit_cache:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h|%aI", "--", path],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                             errors="replace").stdout.strip().splitlines()
        first_commit_cache[path] = (out[-1].split("|") + [""])[:2] if out else ("", "")
    return first_commit_cache[path]


kinds: Counter[str] = Counter()
rows = []
for eid in sorted(unbound):
    record = records[eid]
    target = state_of.get(eid, {})
    state = target.get("state", "NOT_IN_TARGETS_AUDIT")
    operand = (target.get("operands") or [{}])[0].get("operand", "")
    kinds[state] += 1
    entry = {"errorId": eid, "date": record.get("date"), "state": state, "operand": operand,
             "command": (target.get("command") or "")[:120]}
    if state == "RESOLVES" and operand:
        added, when = first_commit(operand)
        entry["guardFirstCommit"] = added
        entry["guardAddedAt"] = when[:10]
        days = None
        if when and record.get("date"):
            try:
                days = (datetime.fromisoformat(when[:10]) -
                        datetime.fromisoformat(record["date"])).days
            except ValueError:
                days = None
        entry["guardVsRecordDays"] = days
    rows.append(entry)

clear = [r for r in rows if r.get("state") == "RESOLVES"
         and r.get("guardVsRecordDays") is not None
         and abs(r["guardVsRecordDays"]) <= CLEAR_WINDOW_DAYS]
undated = [r for r in rows if r.get("state") == "RESOLVES" and r.get("guardVsRecordDays") is None]
distant = [r for r in rows if r.get("state") == "RESOLVES"
           and r.get("guardVsRecordDays") is not None
           and r not in clear]
# The 2026-08 batch records carry no date field at all, so the window rule cannot be applied to them;
# naming that reason keeps "ambiguous" from reading like "decided against".

doc = {"schemaVersion": "work-lab/ledger-unbound-triage/v1",
       "tool": "scripts/audit/triage_unbound_ledger_records.py",
       "generatedByCommand": "python scripts/audit/triage_unbound_ledger_records.py",
       "readOnly": True,
       "bindsNothing": True,
       "whyItMatters": "a PASS record without fixedCommit claims an outcome with no pinned cause; this "
                       "splits that debt into what a commit can actually answer for and what it cannot",
       "clearWindowDays": CLEAR_WINDOW_DAYS,
       "counts": {"unboundPassRecords": len(unbound), "byState": dict(kinds),
                  "clearCandidates": len(clear),
                  "resolvesGuardUndatedRecord": len(undated),
                  "resolvesGuardDistant": len(distant),
                  "noResolvableOperand": len(unbound) - sum(
                      1 for r in rows if r.get("state") == "RESOLVES")},
       "clearCandidates": [r["errorId"] for r in clear],
       "resolvesGuardUndatedRecord": [r["errorId"] for r in undated],
       "resolvesGuardDistant": [r["errorId"] for r in distant],
       "rows": rows}
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("unboundPass", len(unbound), "byState", dict(kinds))
print("clear", len(clear), "undated", len(undated), "distant", len(distant))
for r in clear[:12]:
    print(f"  {r['errorId']} record={r['date']} guard={r['guardFirstCommit']} "
          f"added={r['guardAddedAt']} delta={r['guardVsRecordDays']}d {r['operand']}")
print("triage ->", OUT)
