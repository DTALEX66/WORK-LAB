#!/usr/bin/env python3
"""Canonical Config Compiler (WLR-040).

Pipeline: canonical intent → client projection → plan diff → approval → apply → readback

Usage:
  config_compiler.py create  --client <client> --type <type> --target <target> [--value <json>]
  config_compiler.py plan    --intent <intent.json>
  config_compiler.py approve --intent <intent.json>
  config_compiler.py apply   --intent <intent.json>
  config_compiler.py readback --intent <intent.json>
"""
import argparse, json, sys, hashlib, uuid
from pathlib import Path
from datetime import datetime

SCHEMA_VERSION = "work-lab/canonical-config-intent/v1"
APPROVAL_DIR = Path(__file__).parent.parent.parent / "config" / "pending-approvals"

def new_intent_id():
    return f"intent-{uuid.uuid4().hex[:12]}"

def create_intent(args):
    """Create a new canonical config intent."""
    value = json.loads(args.value) if args.value else None
    intent = {
        "schemaVersion": SCHEMA_VERSION,
        "intentId": new_intent_id(),
        "client": args.client,
        "intent": {"type": args.type, "target": args.target, "value": value, "reason": args.reason or ""},
        "plan": {"diff": [], "approval_required": True, "idempotency_key": uuid.uuid4().hex},
        "status": "draft",
    }
    out = Path(args.output) if args.output else APPROVAL_DIR / f"{intent['intentId']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(intent, indent=2), encoding="utf-8")
    print(f"OK: intent {intent['intentId']} -> {out}")

def plan_intent(args):
    """Generate plan diff from intent (stub — real projection needs adapter)."""
    cap = json.loads(Path(args.intent).read_text(encoding="utf-8"))
    client = cap["client"]
    intent = cap["intent"]
    diff_entry = {
        "path": f"{client}:{intent['target']}",
        "operation": "modify",
        "proposed_value": intent.get("value"),
        "file": f"({client} adapter projection)",
    }
    cap["plan"]["diff"] = [diff_entry]
    cap["status"] = "pending_approval"
    Path(args.intent).write_text(json.dumps(cap, indent=2), encoding="utf-8")
    print(f"OK: plan generated ({len(diff_entry)} diff entries), status=pending_approval")

def approve_intent(args):
    """Approve a pending intent."""
    cap = json.loads(Path(args.intent).read_text(encoding="utf-8"))
    if cap["status"] != "pending_approval":
        print(f"FAIL: status is {cap['status']}, expected pending_approval"); sys.exit(1)
    cap["status"] = "approved"
    Path(args.intent).write_text(json.dumps(cap, indent=2), encoding="utf-8")
    print(f"OK: intent {cap['intentId']} approved")

def apply_intent(args):
    """Apply an approved intent (stub — real apply needs adapter)."""
    cap = json.loads(Path(args.intent).read_text(encoding="utf-8"))
    if cap["status"] != "approved":
        print(f"FAIL: status is {cap['status']}, expected approved"); sys.exit(1)
    cap["status"] = "applied"
    cap["applied_at"] = datetime.utcnow().isoformat() + "Z"
    Path(args.intent).write_text(json.dumps(cap, indent=2), encoding="utf-8")
    print(f"OK: intent {cap['intentId']} applied at {cap['applied_at']}")

def readback_intent(args):
    """Readback current state after apply."""
    cap = json.loads(Path(args.intent).read_text(encoding="utf-8"))
    print(json.dumps({
        "intentId": cap["intentId"],
        "client": cap["client"],
        "status": cap["status"],
        "applied_at": cap.get("applied_at"),
        "diff_count": len(cap.get("plan", {}).get("diff", [])),
    }, indent=2))

def main():
    p = argparse.ArgumentParser(description="Canonical Config Compiler (WLR-040)")
    sub = p.add_subparsers(dest="cmd")

    cr = sub.add_parser("create")
    cr.add_argument("--client", required=True)
    cr.add_argument("--type", required=True)
    cr.add_argument("--target", required=True)
    cr.add_argument("--value", default=None)
    cr.add_argument("--reason", default=None)
    cr.add_argument("--output", default=None)

    pl = sub.add_parser("plan")
    pl.add_argument("--intent", required=True)

    ap = sub.add_parser("approve")
    ap.add_argument("--intent", required=True)

    au = sub.add_parser("apply")
    au.add_argument("--intent", required=True)

    rb = sub.add_parser("readback")
    rb.add_argument("--intent", required=True)

    args = p.parse_args()
    if args.cmd == "create": create_intent(args)
    elif args.cmd == "plan": plan_intent(args)
    elif args.cmd == "approve": approve_intent(args)
    elif args.cmd == "apply": apply_intent(args)
    elif args.cmd == "readback": readback_intent(args)
    else: p.print_help()

if __name__ == "__main__":
    main()
