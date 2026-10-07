"""Precise byte-range reads on large evidence artifacts (REQ-RANGE-20261007 / blueprint SoL row).

The evidence chain already carries a sha256 per artifact and a cost budget, but the only way to look at a
large log was to read it whole or show a prefix (`_truncate(limit=4000)`-style). A prefix is not a slice:
a reader cannot tell where it stopped, whether more exists, or whether the bytes they were shown still
belong to the digest that was recorded.

This module reads an exact interval and reports enough identity to trust it:

* the handle must resolve inside a declared evidence surface — an absolute path outside the repository, a
  path that is inside the repository but not evidence, a credential-shaped name, a missing file, a
  directory, and an unreadable file are each their own typed failure, never an empty success;
* the caller may pin the expected whole-file digest; a mismatch is DIGEST_MISMATCH and returns NO content,
  because showing bytes from a file that is not the recorded one is worse than showing nothing;
* `sliceDigest` is a digest of exactly the bytes returned, so an interval can be cited without shipping
  the whole artifact;
* cost is measured and reported (bytes read against file size), because the point of the feature is that a
  slice of a large log is cheap, and that claim has to be checkable.

Read-only by construction: there is no write path here, it never follows a handle out of the project, and
it never serves a file that the project's own boundary calls configuration, credentials, or a session store.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "worklab/evidence-range-result/v1"
MAX_LIMIT = 4 * 1024 * 1024          # 4 MiB per read; larger requests are refused, not silently capped
DEFAULT_LIMIT = 64 * 1024
DIGEST_HEX_LENGTH = 64

STATUS_OK = "OK"
STATUS_OUT_OF_RANGE = "OUT_OF_RANGE"
REFUSALS = {
    "HANDLE_REQUIRED": "handle 为空：没有句柄就没有对象。",
    "ABSOLUTE_PATH_REQUIRED": "handle 必须是绝对路径；相对路径会随调用者的工作目录改变所指文件。",
    "OUT_OF_BOUNDARY": "handle 解析到本仓库之外，只读投影不跨越项目边界。",
    "OUT_OF_EVIDENCE_SURFACE": "handle 不在声明的证据目录内：项目内部本身就是敏感的，边界不等于许可。",
    "SENSITIVE_NAME": "handle 指向凭证、配置、会话库或密钥类文件，读取投影在任何边界内都不提供这类内容。",
    "UNRESOLVABLE": "handle 无法解析，按失败关闭处理。",
    "NOT_A_FILE": "handle 不指向普通文件（不存在、目录或特殊文件）。",
    "UNREADABLE": "handle 存在但读不了；这是实测到的失败，不是没有内容。",
    "LIMIT_TOO_LARGE": f"单次读取上限 {MAX_LIMIT} 字节，超限拒绝而不是静默截断。",
    "DIGEST_MISMATCH": "期望摘要与实际文件不符：返回的字节不属于被记录的那份产物，因此不返回内容。",
    "DIGEST_SHAPE": "expected_digest 必须是 64 位十六进制 sha256。",
    "DIGEST_UNAVAILABLE": "调用方给了 expected_digest 却没有可比的摘要来源，无法判定一致性；不返回内容。",
}

# `.project-local/artifacts` and `.project-local/runs` are what the boundary declaration names as evidence
# and runtime surfaces. Everything else inside the repository is source, configuration, or a local database:
# staying inside the Git root is a spill rule, not a reading licence.
DEFAULT_EVIDENCE_ROOTS = (".project-local/artifacts", ".project-local/runs")

# The owner's no-read law is about kinds of content, so it is enforced by name as well as by directory: a
# restored pre-install backup sits under an evidence root and still contains another tool's config.
SENSITIVE_NAME_TOKENS = (
    ".env", "credential", "secret", "token", "cookie", "password", "private_key", ".key", ".pem",
    ".pfx", ".pkcs12", "id_rsa", "config.yaml", "config.yml", "canonical.sqlite", ".sqlite", ".db",
    "session", "auth_store", "login data", "history",
)


def _name_is_sensitive(resolved: Path) -> bool:
    names = [part.lower() for part in resolved.parts]
    return any(token in name for name in names for token in SENSITIVE_NAME_TOKENS)


BOUNDARY_DECLARATION = ".project/governance/project-data-boundary.json"
_BOUNDARY_ROOT_KEYS = ("canonicalEvidenceRoot", "taskArtifactsRoot", "runtimeRoot")


def declared_evidence_roots(root: Path) -> tuple[str, ...]:
    """Read the evidence surfaces from the boundary declaration instead of hardcoding a second opinion.

    A missing or unreadable declaration falls back to the narrow default, never to "everything in the
    repository": an absent authority is a reason to refuse, not to allow.
    """
    try:
        document = json.loads((Path(root) / BOUNDARY_DECLARATION).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return DEFAULT_EVIDENCE_ROOTS
    declared = tuple(str(document[key]) for key in _BOUNDARY_ROOT_KEYS if document.get(key))
    return declared or DEFAULT_EVIDENCE_ROOTS


def _sha256_slice(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _refusal(code: str, *, handle: str, detail: str = "") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "REFUSED",
        "reason_code": code,
        "reason": REFUSALS[code] + (f" 细节：{detail}" if detail else ""),
        "handle": handle,
        "content": None,
        "cost": {"bytesRead": 0, "fileSize": None, "wholeFileWasRead": False},
    }


def read_range(*, handle: str, root: Path, offset: int = 0, limit: int = DEFAULT_LIMIT,
               expected_digest: str | None = None, whole_digest: str | None = None,
               evidence_roots: tuple[str, ...] = DEFAULT_EVIDENCE_ROOTS) -> dict[str, Any]:
    """Read `limit` bytes at `offset` from a declared evidence artifact inside this project.

    `evidence_roots` are relative to `root` and default to the surfaces the boundary declaration names as
    evidence and runtime storage. Passing an explicit tuple narrows the surface; passing () refuses
    everything, because an unset surface is not the same as an unrestricted one.
    """
    root = Path(root).resolve()
    if not handle or not str(handle).strip():
        return _refusal("HANDLE_REQUIRED", handle=str(handle))
    path = Path(str(handle))
    if not path.is_absolute():
        return _refusal("ABSOLUTE_PATH_REQUIRED", handle=str(handle))
    try:
        resolved = path.resolve()
    except OSError as error:
        return _refusal("UNRESOLVABLE", handle=str(handle), detail=type(error).__name__)
    if not resolved.is_relative_to(root):
        return _refusal("OUT_OF_BOUNDARY", handle=str(handle), detail=str(resolved))
    if _name_is_sensitive(resolved):
        # Named before the surface test: a credential-looking path is refused even when it sits in an
        # evidence root, so a restored backup cannot be read just because it was filed under artifacts/.
        return _refusal("SENSITIVE_NAME", handle=str(handle), detail=resolved.name)
    surfaces = tuple((root / relative).resolve() for relative in evidence_roots)
    if not surfaces or not any(resolved.is_relative_to(surface) for surface in surfaces):
        return _refusal("OUT_OF_EVIDENCE_SURFACE", handle=str(handle), detail=str(resolved))
    if not resolved.is_file():
        return _refusal("NOT_A_FILE", handle=str(handle))
    if limit <= 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_OUT_OF_RANGE,
            "reason_code": "LIMIT_NON_POSITIVE",
            "reason": "limit 必须为正数；0 或负数不是一次读取。",
            "handle": str(handle),
            "content": None,
            "cost": {"bytesRead": 0, "fileSize": None, "wholeFileWasRead": False},
        }
    if limit > MAX_LIMIT:
        return _refusal("LIMIT_TOO_LARGE", handle=str(handle), detail=f"requested={limit}")

    size = resolved.stat().st_size
    if offset < 0:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_OUT_OF_RANGE,
            "reason_code": "OFFSET_NEGATIVE",
            "reason": "offset 不能为负。",
            "handle": str(handle),
            "content": None,
            "cost": {"bytesRead": 0, "fileSize": size, "wholeFileWasRead": False},
        }
    if offset >= size:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_OUT_OF_RANGE,
            "reason_code": "OFFSET_PAST_END",
            "reason": f"offset {offset} 已超过文件长度 {size}；这是空区间，不是读失败。",
            "handle": str(handle),
            "content": None,
            "cost": {"bytesRead": 0, "fileSize": size, "wholeFileWasRead": False},
        }

    if expected_digest is not None:
        if len(expected_digest) != DIGEST_HEX_LENGTH or any(
                character not in "0123456789abcdefABCDEF" for character in expected_digest):
            return _refusal("DIGEST_SHAPE", handle=str(handle), detail=expected_digest[:16])
        if not whole_digest:
            # Verifying identity against the recorded artifact is the caller's input, never this reader's
            # job: hashing the whole file here would silently turn a cheap range read into a full read.
            return _refusal("DIGEST_UNAVAILABLE", handle=str(handle),
                            detail="expected_digest 已给出但没有 whole_digest 可比")
        if whole_digest != expected_digest:
            result = _refusal("DIGEST_MISMATCH", handle=str(handle),
                              detail=f"expected={expected_digest[:12]}… actual={whole_digest[:12]}…")
            result["cost"]["fileSize"] = size
            result["identity"] = {"wholeDigest": whole_digest, "sizeBytes": size}
            return result

    try:
        with resolved.open("rb") as stream:
            stream.seek(offset)
            data = stream.read(limit)
    except OSError as error:
        return _refusal("UNREADABLE", handle=str(handle), detail=type(error).__name__)

    end = offset + len(data)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_OK,
        "reason_code": "READ_OK",
        "reason": "按精确区间读取。",
        "handle": str(resolved),
        "offset": offset,
        "limit": limit,
        "bytesRequested": min(limit, size - offset),
        "endOffset": end,
        "eofReached": end >= size,
        "content": data.decode("utf-8", errors="replace"),
        "sliceDigest": _sha256_slice(data),
        "identity": {"wholeDigest": whole_digest, "sizeBytes": size,
                     "digestSource": "caller-supplied" if whole_digest else "not-supplied"},
        "cost": {"bytesRead": len(data), "fileSize": size,
                 "wholeFileWasRead": end >= size and offset == 0 and len(data) == size},
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", required=True, help="absolute path inside this repository")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--expected-digest", default=None)
    parser.add_argument("--evidence-root", action="append", default=None,
                        help="relative evidence surface; defaults to the boundary declaration")
    parser.add_argument("--json", action="store_true", help="print the full typed result")
    args = parser.parse_args(argv)
    roots = tuple(args.evidence_root) if args.evidence_root else declared_evidence_roots(args.root)
    result = read_range(handle=args.handle, root=args.root, offset=args.offset, limit=args.limit,
                        expected_digest=args.expected_digest, evidence_roots=roots)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"status={result['status']} reason={result['reason_code']} "
              f"bytes={result['cost']['bytesRead']}/{result['cost']['fileSize']}")
        if result["content"] is not None:
            print(result["content"], end="")
    return 0 if result["status"] == STATUS_OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
