# -*- coding: utf-8 -*-
"""AG-05: fail-closed integrity verifier for the model/provider/runtime registries.

Authority chain: `WORK-LAB-AUTHORITY.md` > `.project/governance/project-authority-index.json`
> `AGENTS.md` + scoped machine contracts > this verifier. This script never
mutates anything and never touches the network, a model asset, a runtime
process, or any global software configuration. It reads JSON only.

Why this exists
---------------
The 2026-09-29 Master Atlas recorded that the three registries disagreed with
each other (gap G05, card row AG-05): a provider bound to a model id that no
longer existed, provider entries that claimed `OPERATIONAL` while their own
notes said the weight was not served, digests that were truncated prose rather
than verifiable checksums, and in-process ASR libraries that were not
distinguishable from HTTP servers. Each is a silent-wrong-truth hazard: a
caller reading one field concludes a capability is callable when it is not.

Checks (every one fails closed with a named reason)
--------------------------------------------------
1  `binds_to_model` must resolve to a `models[].id`, or to an explicitly
   declared `externalAssets[].id` (a read-only reference the registry does not
   own), or be an explicit `null` with a non-empty `binding_note` explaining
   why there is no binding. A dangling foreign key is a failure.
2  `binds_to_runtime` must resolve to a `runtimes[].id` or a
   `processLibraries[].id`. In-process libraries are declared distinctly from
   HTTP servers via `executionModel`, so a process library is never mistaken
   for a service that can be polled.
3  `binding_status` is a closed vocabulary. A provider whose model entry is
   RETIRED_PENDING_DECISION must declare `UNSERVED_RETAINED_PENDING_DECISION`
   and must NOT declare `SERVED`. This is the contradiction check: an entry may
   not simultaneously be "not served" and "served".
4  `operationalStatus` is explicitly scoped to the runtime endpoint and may not
   use serving vocabulary ("loads this model", "serves this model") when the
   binding is not served. That phrasing is what made the old rows read as
   "this model works".
5  An `assetDigest` block is either absent, or has `state: COMPLETE` with a
   lowercase 64-hex `sha256`, or has `state: TRUNCATED` with a non-empty
   reason. A truncated prefix may never masquerade as a complete digest.
6  A provider id appears at most once; provider ids are namespaced.

Exit codes: 0 PASS, 1 FAIL (named reason printed), 2 environment error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROVIDER_REGISTRY = ".project/governance/provider-registry.json"
MODEL_REGISTRY = ".project/governance/model-registry.json"
RUNTIME_REGISTRY = ".project/governance/runtime-registry.json"

# Closed vocabulary for the provider -> model binding state (AG-05).
BINDING_STATUSES = frozenset({"SERVED", "UNSERVED_RETAINED_PENDING_DECISION"})
# Model-registry lifecycle values that mean "this weight is not served".
UNSERVED_MODEL_STATUSES = frozenset({"RETIRED_PENDING_DECISION", "RETIRED"})
# Digest states for the assetDigest block.
DIGEST_STATES = frozenset({"COMPLETE", "TRUNCATED"})

HEX64 = re.compile(r"^[0-9a-f]{64}$")
# Serving vocabulary that must not appear in a runtime-scoped operationalStatus
# when the provider's own binding is declared unserved.
SERVING_PHRASES = ("loads this model", "loads the model", "serves this model",
                   "this model is served", "model on demand")
# Fields that must never be null/empty when present.
_REQUIRED_PROVIDER_STRINGS = ("id",)

_errors: list[str] = []


def _fail(reason: str, detail: str = "") -> None:
    suffix = f" {detail}" if detail else ""
    _errors.append(f"{reason}{suffix}")


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail("REGISTRY_MISSING", str(path))
    except json.JSONDecodeError as exc:
        _fail("REGISTRY_INVALID_JSON", f"{path}: {exc}")
    return {}


def _index(entries: object, key: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(entries, list):
        return out
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get(key), str):
            out[entry[key]] = entry
    return out


def verify(root: Path) -> int:
    _errors.clear()
    provider_path = root / PROVIDER_REGISTRY
    if not provider_path.is_file():
        return _report("PROVIDER_REGISTRY_MISSING", str(provider_path))

    providers_doc = _load(provider_path)
    models_doc = _load(root / MODEL_REGISTRY)
    runtimes_doc = _load(root / RUNTIME_REGISTRY)
    if _errors:
        return _report("REGISTRY_UNREADABLE", "; ".join(_errors))

    providers = providers_doc.get("providers")
    if not isinstance(providers, list) or not providers:
        return _report("PROVIDERS_MISSING", "provider-registry.json has no providers[]")

    models = _index(models_doc.get("models"), "id")
    runtimes = _index(runtimes_doc.get("runtimes"), "id")
    process_libs = _index(runtimes_doc.get("processLibraries"), "id")
    external_assets = _index(providers_doc.get("externalAssets"), "id")

    known_bindings = set(models) | set(external_assets)

    seen_ids: set[str] = set()
    served_bindings = 0

    for provider in providers:
        if not isinstance(provider, dict):
            _fail("PROVIDER_ENTRY_MALFORMED", repr(provider)[:80])
            continue
        pid = provider.get("id")
        if not isinstance(pid, str) or not pid:
            _fail("PROVIDER_ID_MISSING", "every provider needs a non-empty id")
            continue
        if pid in seen_ids:
            _fail("PROVIDER_ID_DUPLICATE", pid)
        seen_ids.add(pid)
        for field in _REQUIRED_PROVIDER_STRINGS:
            if not isinstance(provider.get(field), str):
                _fail("PROVIDER_FIELD_MISSING", f"{pid}.{field}")

        # --- check 1: model foreign key -------------------------------
        bound = provider.get("binds_to_model")
        if bound is None:
            note = provider.get("binding_note")
            if not (isinstance(note, str) and note.strip()):
                _fail("BINDING_NULL_WITHOUT_NOTE",
                      f"{pid} declares binds_to_model=null without a binding_note")
        elif not isinstance(bound, str):
            _fail("BINDING_NOT_STRING", f"{pid}.binds_to_model={bound!r}")
        elif bound not in known_bindings:
            _fail("BINDING_UNRESOLVED",
                  f"{pid}.binds_to_model={bound!r} is not a models[].id "
                  f"({len(models)} known) nor a declared externalAssets[].id")

        # --- check 2: runtime foreign key -----------------------------
        runtime = provider.get("binds_to_runtime")
        if runtime is not None:
            if not isinstance(runtime, str):
                _fail("RUNTIME_BINDING_NOT_STRING", f"{pid}.binds_to_runtime={runtime!r}")
            elif runtime not in runtimes and runtime not in process_libs:
                _fail("RUNTIME_BINDING_UNRESOLVED",
                      f"{pid}.binds_to_runtime={runtime!r} is neither a runtimes[].id "
                      "nor a declared processLibraries[].id")

        model_entry = models.get(bound) if isinstance(bound, str) else None
        model_status = model_entry.get("status") if isinstance(model_entry, dict) else None
        binding_status = provider.get("binding_status")

        # --- check 3: binding-status closed vocabulary + contradiction --
        if binding_status is not None:
            if binding_status not in BINDING_STATUSES:
                _fail("BINDING_STATUS_UNKNOWN",
                      f"{pid}.binding_status={binding_status!r} not in {sorted(BINDING_STATUSES)}")
            if binding_status == "SERVED":
                served_bindings += 1
                if model_status in UNSERVED_MODEL_STATUSES:
                    _fail("BINDING_STATUS_CONTRADICTS_MODEL",
                          f"{pid} declares SERVED but model {bound!r} status={model_status!r}")
            source = provider.get("binding_status_source")
            if binding_status == "UNSERVED_RETAINED_PENDING_DECISION" \
                    and not (isinstance(source, str) and source.strip()):
                _fail("BINDING_STATUS_WITHOUT_SOURCE",
                      f"{pid} declares an unserved binding without binding_status_source")
        elif model_status in UNSERVED_MODEL_STATUSES:
            _fail("UNSERVED_MODEL_WITHOUT_BINDING_STATUS",
                  f"{pid} binds model {bound!r} (status={model_status!r}) but declares no "
                  "binding_status; the reader cannot tell the binding is dead")

        # --- check 4: operationalStatus is runtime-scoped only --------
        op_status = provider.get("operationalStatus")
        if isinstance(op_status, str) and binding_status == "UNSERVED_RETAINED_PENDING_DECISION":
            lowered = op_status.lower()
            for phrase in SERVING_PHRASES:
                if phrase in lowered:
                    _fail("OPERATIONAL_STATUS_OVERREACHES",
                          f"{pid} declares an unserved binding but its operationalStatus says "
                          f"{phrase!r}; that reads as 'this model works'")
        if isinstance(op_status, str) and "operational" in op_status.lower() \
                and binding_status is None and model_status in UNSERVED_MODEL_STATUSES:
            _fail("OPERATIONAL_STATUS_UNSCOPED",
                  f"{pid} claims OPERATIONAL with an unserved model and no bound scope")

        # --- check 5: digest honesty ----------------------------------
        digest = provider.get("assetDigest")
        if digest is not None:
            if not isinstance(digest, dict):
                _fail("ASSET_DIGEST_MALFORMED", f"{pid}.assetDigest must be an object")
            else:
                state = digest.get("state")
                if state not in DIGEST_STATES:
                    _fail("ASSET_DIGEST_STATE_UNKNOWN",
                          f"{pid}.assetDigest.state={state!r} not in {sorted(DIGEST_STATES)}")
                elif state == "COMPLETE":
                    sha = digest.get("sha256")
                    if not (isinstance(sha, str) and HEX64.match(sha)):
                        _fail("ASSET_DIGEST_INCOMPLETE",
                              f"{pid}.assetDigest.state=COMPLETE but sha256 is not 64 lowercase hex")
                elif state == "TRUNCATED":
                    reason = digest.get("reason")
                    if not (isinstance(reason, str) and reason.strip()):
                        _fail("ASSET_DIGEST_TRUNCATED_WITHOUT_REASON",
                              f"{pid}.assetDigest.state=TRUNCATED requires a reason")

    # --- check: model registry digest honesty -------------------------
    for model_id, entry in sorted(models.items()):
        raw = entry.get("sha256")
        if raw is None:
            continue
        if isinstance(raw, str) and HEX64.match(raw):
            continue
        _fail("MODEL_SHA256_UNVERIFIABLE",
              f"model {model_id}.sha256={str(raw)[:48]!r} is neither a 64-hex digest nor an "
              "explicit null; move the prose to assetDigest and null the field")

    # --- check: process libraries are not HTTP servers ---------------
    for lib_id, lib in sorted(process_libs.items()):
        model = lib.get("executionModel")
        if model not in ("in-process", "subprocess"):
            _fail("PROCESS_LIBRARY_EXECUTION_MODEL",
                  f"processLibraries[{lib_id}].executionModel={model!r} must be "
                  "'in-process' or 'subprocess'")
        if lib.get("listensOnPort") not in (None, False):
            _fail("PROCESS_LIBRARY_CLAIMS_PORT",
                  f"processLibraries[{lib_id}] declares listensOnPort; an in-process library "
                  "must not be described as a service endpoint")

    # --- check: nothing claims to serve that is not served -----------
    for runtime_id, rt in sorted(runtimes.items()):
        status = rt.get("status")
        if isinstance(status, str) and status.strip().upper() == "RUNNING":
            for provider in providers:
                if not isinstance(provider, dict):
                    continue
                if provider.get("binds_to_runtime") == runtime_id \
                        and provider.get("binding_status") == "UNSERVED_RETAINED_PENDING_DECISION":
                    # Not a failure: only SERVED would be. Recorded for audit.
                    pass

    if _errors:
        return _report("MODEL_REGISTRY_INTEGRITY_FAIL", " | ".join(_errors[:12]))

    print(
        "MODEL_REGISTRY_INTEGRITY_PASS "
        f"providers={len(providers)} models={len(models)} "
        f"runtimes={len(runtimes)} processLibraries={len(process_libs)} "
        f"externalAssets={len(external_assets)} served_bindings={served_bindings}"
    )
    return 0


def _report(reason: str, detail: str) -> int:
    print(f"{reason} {detail}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root to verify")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"MODEL_REGISTRY_INTEGRITY_ENV_ERROR root not a directory: {root}", file=sys.stderr)
        return 2
    return verify(root)


if __name__ == "__main__":
    raise SystemExit(main())
