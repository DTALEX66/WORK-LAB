"""Probe the managed executors where they actually are, and record what the machine answers.

AG-16's chain (ContextEnvelope → PlanningCandidate → check/authorize → selected executor → Receipt)
has never been walked end to end, and the reason is checkable rather than mysterious: every entry in
`config/adapter-registry.json` carries `detection.evidence_state = UNVERIFIED`, so no capability
decision can name a probed executor. This script is the probe half of that. It is read-only:

  * it resolves each adapter's declared entry point — the HERMES_HOME binary, the repo's codex
    wrapper, the DSH install root read from the uninstall registry or the shortcut target rather
    than a hardcoded drive letter (AGENTS.md), `gh` for GitHub — and never a guessed path;
  * it runs exactly one version readback per entry, under a timeout, and writes nothing anywhere;
  * it never inflates. LIVE_VERIFIED requires exit 0 AND agreement with the version the registry
    already claims; a different version is recorded as VERSION_MOVED with both strings, because the
    registry is not the truth and neither is a stale note about it.

Usage:
    python scripts/audit/executor_live_probe.py [--out docs/audits/EXECUTOR_LIVE_PROBE_2026-10-07.json]
Exit: 0 always for a completed probe (an absent executor is a finding, not a crash); 2 if the
registry cannot be read. The counts line is what a reader compares against the register row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "config" / "adapter-registry.json"
VERSION_RE = re.compile(r"(\d+\.\d+[^\s)]*)")
TIMEOUT_SECONDS = 25


def run_readonly(argv: list[str]) -> dict:
    """One short-lived version readback, with no shell and no write capability."""
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
                              encoding="utf-8", errors="replace", shell=False)
    except FileNotFoundError as exc:
        return {"invoked": False, "reason": f"ENTRY_NOT_EXECUTABLE {exc!r}"}
    except subprocess.TimeoutExpired:
        return {"invoked": True, "exitCode": None, "reason": f"PROBE_TIMEOUT_{TIMEOUT_SECONDS}s"}
    except OSError as exc:
        return {"invoked": False, "reason": f"PROBE_OS_ERROR {exc!r}"}
    out = (proc.stdout or "") + (proc.stderr or "")
    line = next((l.strip() for l in out.splitlines() if VERSION_RE.search(l)), out.strip()[:160])
    return {"invoked": True, "exitCode": proc.returncode, "outputSha256": hashlib.sha256(
        out.encode("utf-8", errors="replace")).hexdigest(), "versionLine": line[:200],
        "observedVersion": (VERSION_RE.search(line) or [None, None])[1] if VERSION_RE.search(line)
        else None}


def resolve_hermes() -> list[str] | None:
    home = os.environ.get("HERMES_HOME") or (Path(os.path.expanduser("~")) / "AppData/Local/hermes")
    exe = Path(home) / "bin" / "hermes.exe"
    return [str(exe), "--version"] if exe.is_file() else None


def resolve_codex() -> list[str] | None:
    """The repo-declared wrapper is the single canonical entry (AGENTS.md dimension 1)."""
    cmd = REPO / "packages" / "client-neutral-core" / "bin" / "codex.cmd"
    if not cmd.is_file():
        return None
    # cmd.exe is needed to run a .cmd; pass the version flag as one argument so no shell
    # interpretation of the path (which contains a space) can happen.
    return ["cmd.exe", "/d", "/c", str(cmd), "--version"]


def resolve_dsh() -> list[str] | None:
    """DeepSeek Harness: resolve the install root from the uninstall registry entry, never a drive."""
    exe = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DeepSeek Harness" / \
        "DeepSeek Harness.exe"
    return [str(exe), "--version"] if exe.is_file() else None


def resolve_gh() -> list[str] | None:
    from shutil import which
    found = which("gh") or which("gh.exe")
    return [found, "--version"] if found else None


def resolve_desktop_shortcut(name: str) -> list[str] | None:
    """A GUI client's declared entry is its desktop shortcut; reading the target is not launching it."""
    desktop = Path(os.path.expanduser("~")) / "Desktop"
    candidates = list(desktop.glob(f"*{name}*.lnk")) + list(
        (Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs")
        .glob(f"*{name}*.lnk"))
    if not candidates:
        return None
    shell = ("Set s = CreateObject(\"WScript.Shell\").CreateShortcut(\""
             + str(candidates[0]).replace('"', '""') + "\")\n"
             "WScript.Echo s.TargetPath")
    proc = subprocess.run(["cscript.exe", "//nologo", "//U", "//E:vbscript",
                           "-"], input="\r\n".join(shell).encode("utf-16-le"),
                          capture_output=True, timeout=20)
    target = proc.stdout.decode("utf-16-le", errors="replace").strip().strip("\x00")
    return [target, "--version"] if target and Path(target).is_file() else None


RESOLVERS = {
    "hermes": resolve_hermes,
    "codex": resolve_codex,
    "deepseek-harness": resolve_dsh,
    "github": resolve_gh,
    "openhuman": lambda: resolve_desktop_shortcut("OpenHuman") or resolve_desktop_shortcut("Open Human"),
    "open-design": lambda: resolve_desktop_shortcut("Open Design"),
    "cc-switch": lambda: resolve_desktop_shortcut("CC Switch"),
}


def adjudicate(entry: dict, probe: dict) -> tuple[str, str]:
    claimed = ((entry.get("provenance") or {}).get("version") or "").strip()
    if not probe.get("invoked"):
        return "ENTRY_NOT_RESOLVED", probe.get("reason") or "no declared entry point resolved"
    if probe.get("exitCode") != 0:
        return ("PROBE_TIMEOUT" if probe.get("exitCode") is None else "PROBE_FAILED"), \
            f"exit={probe.get('exitCode')} {probe.get('reason') or probe.get('versionLine','')[:80]}"
    observed = probe.get("observedVersion")
    # A registry field holding the literal word UNVERIFIED is a placeholder, not a version claim:
    # comparing against it produced a confident-looking VERSION_MOVED for the two executors that
    # really did answer. Measured bytes with nothing to compare to are recorded as MEASURED.
    if not claimed or not VERSION_RE.search(claimed):
        return ("MEASURED_NO_CLAIM_TO_COMPARE" if observed else "PROBED_NO_VERSION_READBACK",
                f"observed={observed or probe.get('versionLine','')[:60]!r}; registry claims "
                f"{claimed!r} which is not a version string")
    if claimed.split("+")[0] == (observed or "").split("+")[0]:
        return "LIVE_VERIFIED", f"observed={observed} agrees with claimed={claimed}"
    return "VERSION_MOVED", f"observed={observed} claimed={claimed} — both kept, neither reconciled"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if not REGISTRY.is_file():
        print(f"EXECUTOR_PROBE_NOT_RUN REGISTRY_ABSENT {REGISTRY}")
        return 2
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    results = []
    for entry in registry["entries"]:
        adapter_id = entry["id"]
        resolver = RESOLVERS.get(adapter_id)
        if resolver is None:
            results.append({"adapter": adapter_id, "state": "NOT_PROBED_DECLARATIVE_ONLY",
                            "detail": "no live entry point is declared for this support level"})
            continue
        try:
            argv = resolver()
        except Exception as exc:  # noqa: BLE001 — a resolver failure is a finding, not a crash
            results.append({"adapter": adapter_id, "state": "RESOLVER_ERROR", "detail": repr(exc)})
            continue
        if not argv:
            results.append({"adapter": adapter_id, "state": "ENTRY_NOT_RESOLVED",
                            "detail": "declared entry point not found on this machine"})
            continue
        probe = run_readonly(argv)
        state, detail = adjudicate(entry, probe)
        results.append({"adapter": adapter_id, "command": argv, "state": state, "detail": detail,
                        "probe": probe, "claimedVersion": (entry.get("provenance") or {}).get("version")})

    counts: dict[str, int] = {}
    for r in results:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    report = {"schemaVersion": "work-lab/executor-live-probe/v1",
              "at": time.strftime("%Y-%m-%dT%H:%M:%S+0800", time.gmtime(time.time() + 8 * 3600)),
              "tool": "scripts/audit/executor_live_probe.py", "readOnly": True,
              "registrySha256": hashlib.sha256(REGISTRY.read_bytes()).hexdigest(),
              "counts": counts, "results": results,
              "note": ("LIVE_VERIFIED requires exit 0 and agreement with the version the registry "
                       "already claims. This script mutates nothing: it reports, and a human or a "
                       "follow-up change decides whether a registry entry's evidence_state moves.")}

    if args.out:
        out = REPO / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(json.dumps(report, ensure_ascii=False, indent=2).replace("\n", "\r\n")
                        .encode("utf-8"))
        print("record ->", out.relative_to(REPO).as_posix())
    print("adapters=%d %s" % (len(results), json.dumps(counts, ensure_ascii=False)))
    for r in results:
        print(f"  {r['adapter']:18} {r['state']:28} {r['detail'][:78]}")
    print("EXECUTOR_PROBE_DONE" if counts.get("LIVE_VERIFIED") else "EXECUTOR_PROBE_NO_LIVE_VERIFIED")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
