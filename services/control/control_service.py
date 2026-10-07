"""Control Surface service (P1-06 / AG-15 / T04): the loopback-only write boundary.

Why this exists as its own process and not as extra routes on the Observer: ``apps/observer`` is
permanently strictly read-only (AGENTS.md, ``apps/observer/AGENTS.md``,
``scripts/ci/verify_observer_readonly_boundary.py``). A unified UI may offer both kinds of surface, but
the read-only service must never hold a write path. So this module is the only place a control request
is accepted, and it delegates every decision to the control plane that already exists —
``services/task-governance/permission_gate.py`` for authorisation and the workflow-owned canonical store
for state — instead of inventing a second ledger, a second receipt engine or a second approval flow.

Rules this module enforces rather than assumes:

* loopback only, dynamic port, and an endpoint descriptor the shell discovers — never a fixed production port;
* the operation enum is closed, and an operation without a native capability answers ``NOT_IMPLEMENTED``
  with its own reason. It never returns a success shape, and no caller-supplied field can raise the
  evidence level: an in-repo fixture store is SYNTHETIC, a live local store is INTEGRATED, and REAL is
  reserved for a verifiable native handle plus readback, which a local write is not;
* ``plan != write``: the config operations that only compute a diff say so, and the ones that would write
  to a target outside this repository answer REFUSED until an exact target is authorised;
* the goal text a Work Unit carries stays in the store. The read-only Observer projection deliberately
  publishes checkpoint key names and a digest, never the values, so a control write cannot smuggle a
  prompt body into the Observer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import sys

_ROOT = Path(__file__).resolve().parents[2]
for _entry in (
    _ROOT / "services" / "task-governance",
    _ROOT / "services" / "orchestration",
    _ROOT / "packages" / "client-neutral-core" / "scripts",
):
    sys.path.insert(0, str(_entry))

import jsonschema  # noqa: E402
from canonical_store import CanonicalStore  # noqa: E402
from permission_gate import ActionKind, PermissionGate, Policy  # noqa: E402
from project_temp import fixture_dir  # noqa: E402
from sidecar import _allowed_origin, _is_loopback_host  # noqa: E402
from snapshot_api import project_task_record  # noqa: E402

SCHEMA_VERSION = "worklab/control-service/v1"
REQUEST_CONTRACT = _ROOT / "packages/contracts/schemas/workflow/control-operation.schema.json"
MAX_BODY_BYTES = 65_536
DESCRIPTOR_PATH = "control-endpoint.json"
RECEIPTS_PATH = "control-receipts.jsonl"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class OperationSpec:
    operation: str
    implemented: bool
    action: ActionKind
    reason_code: str
    reason: str
    next_action: str | None


OPERATIONS: dict[str, OperationSpec] = {
    "work-unit.create": OperationSpec(
        "work-unit.create", True, ActionKind.FILESYSTEM, "WORK_UNIT_CREATED",
        "任务写入 canonical store 的 tasks 表（唯一账本），状态 QUEUED，等待执行器领取。",
        "在 Observer 的 Work 泳道用 ?view=work&taskId=… 读回这条记录。",
    ),
    "work-unit.revise": OperationSpec(
        "work-unit.revise", False, ActionKind.FILESYSTEM, "NO_REVISION_CONTRACT_WIRED",
        "修订合同在 Task Ledger 里存在，但还没有受控的写入口；不假装能改。",
        "需要一条明确的修订合同接线（含 monotonic floor 与旧修订拒绝）。",
    ),
    "work-unit.dispatch": OperationSpec(
        "work-unit.dispatch", False, ActionKind.EXTERNAL_MUTATION, "EXECUTOR_NOT_IMPLEMENTED",
        "原生执行器的 ACP 动词目前逐条返回 NOT_IMPLEMENTED（AG-06/G06），派发没有原生副作用可验证。",
        "先接一个真实执行器的 dispatch 动词与 native receipt，再开放这一项。",
    ),
    "approval.decide": OperationSpec(
        "approval.decide", False, ActionKind.EXTERNAL_MUTATION, "NO_APPROVAL_WRITE_CONTRACT",
        "审批面在快照里是只读投影；没有可写的审批合同就不提供批准按钮。",
        "需要审批决定合同（决定人、范围、被决定修订、回执）。",
    ),
    "execution.cancel": OperationSpec(
        "execution.cancel", False, ActionKind.EXTERNAL_MUTATION, "EXECUTOR_NOT_IMPLEMENTED",
        "取消需要执行器真实停止；取消后不得再写，这一条目前无法 native 读回。",
        "执行器 cancel 动词接通后启用。",
    ),
    "execution.retry": OperationSpec(
        "execution.retry", False, ActionKind.EXTERNAL_MUTATION, "EXECUTOR_NOT_IMPLEMENTED",
        "重试必须不重复副作用；没有幂等身份的执行器就没有可保证的重试。",
        "执行器 retry 动词与幂等身份接通后启用。",
    ),
    "execution.resume": OperationSpec(
        "execution.resume", False, ActionKind.EXTERNAL_MUTATION, "EXECUTOR_NOT_IMPLEMENTED",
        "恢复要求原生会话身份可回读；facade 目前把 resume 降级为 NEW_SESSION。",
        "带 verified marker 的原生 resume 接通后启用。",
    ),
    "config.discover": OperationSpec(
        "config.discover", False, ActionKind.FILESYSTEM,
        "READ_LANDED_ELSEWHERE",
        "发现是读操作，已由配置控制平面与 Observer 读侧承担；控制服务不提供只读动词。",
        "在 Observer 查看配置投影；写侧用 config.diff / config.apply。",
    ),
    "config.diff": OperationSpec(
        "config.diff", True, ActionKind.FILESYSTEM, "PLAN_COMPUTED",
        "按 ownership 计算精确 diff：这是计划，plan != write，不下任何写结论。",
        "确认 expected-before/after 后再发 config.apply。",
    ),
    "config.apply": OperationSpec(
        "config.apply", False, ActionKind.EXTERNAL_MUTATION, "TARGET_NOT_AUTHORISED",
        "写真实客户端配置需要 exact target 授权（项目/路径/字段），本轮授权不含它；拒绝而不是模拟成功。",
        "给出确切目标与字段范围后可在项目内 fixture 上验证写链与 rollback。",
    ),
    "config.readback": OperationSpec(
        "config.readback", False, ActionKind.FILESYSTEM, "NO_WRITE_TO_READ_BACK",
        "readback 只在真实写之后有意义；没有写就不返回一个看起来像验证的读数。",
        "config.apply 被授权并执行后启用。",
    ),
    "config.rollback": OperationSpec(
        "config.rollback", False, ActionKind.DESTRUCTIVE, "NO_RECOVERY_HANDLE",
        "回滚需要恢复句柄；没有句柄时不提供看起来安全的撤销。",
        "写入时同步产出恢复句柄后启用。",
    ),
}

_STATUS_BY_DECISION = {"allowed": None, "needs_human": "NEEDS_HUMAN", "denied": "REFUSED"}


def _is_loopback_authority(host_header: str | None) -> bool:
    """Accept a Host header with or without the port (`127.0.0.1:8123` is still loopback).

    The shared sidecar helper takes a bare host; feeding it a `host:port` pair makes it fail closed,
    which would refuse the shell this service exists to serve. A missing port is a bare IP or name, so
    splitting on the last colon cannot turn a loopback literal into a non-loopback one.
    """
    if not host_header:
        return False
    candidate = host_header.strip().strip("[]")
    if candidate.count(":") == 1 and "/" not in candidate:
        candidate = candidate.rsplit(":", 1)[0]
    return _is_loopback_host(candidate)


class ControlPlane:
    """Executes one control request against the existing authority chain."""

    def __init__(self, store: CanonicalStore, *, project_root: Path, evidence_ceiling: str = "SYNTHETIC",
                 receipts_path: Path | None = None) -> None:
        self.store = store
        self.project_root = project_root.resolve()
        self.evidence_ceiling = evidence_ceiling
        self.receipts_path = receipts_path
        self.gate = PermissionGate(Policy())
        self._schema = json.loads(REQUEST_CONTRACT.read_text(encoding="utf-8"))
        self._validator = jsonschema.Draft202012Validator(self._schema,
                                                          format_checker=jsonschema.FormatChecker())
        self._lock = threading.Lock()

    # -- answers -----------------------------------------------------------
    def result(self, spec: OperationSpec | None, status: str, reason_code: str, reason: str,
               *, request: dict[str, Any] | None = None, task_id: str | None = None,
               receipt: dict[str, Any] | None = None, readback: dict[str, Any] | None = None,
               evidence: str | None = None, next_action: str | None = None) -> dict[str, Any]:
        return {
            "schema_version": "worklab/control-operation-result/v1",
            "operation": (spec.operation if spec else (request or {}).get("operation", "unknown")),
            "idempotency_key": (request or {}).get("idempotency_key", "unparsed"),
            "status": status,
            "reason_code": reason_code,
            "reason": reason,
            "task_id": task_id,
            "receipt": receipt,
            "readback": readback,
            "evidence_level": evidence or "NO_EVIDENCE",
            "observed_at": _now(),
            "next_action": next_action,
        }

    def descriptor(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "observed_at": _now(),
            "transport": "loopback-only",
            "evidence_ceiling": self.evidence_ceiling,
            "operations": [
                {
                    "operation": spec.operation,
                    "support": "IMPLEMENTED" if spec.implemented else "NOT_IMPLEMENTED",
                    "reason_code": spec.reason_code,
                    "reason": spec.reason,
                    "next_action": spec.next_action,
                }
                for spec in OPERATIONS.values()
            ],
        }

    # -- the one entry point ------------------------------------------------
    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(self._validator.iter_errors(request), key=lambda e: list(e.absolute_path))
        if errors:
            first = errors[0]
            return self.result(None, "REFUSED", "INVALID_REQUEST",
                               f"请求不符合 control-operation 合同：{first.message}（路径 {'/'.join(map(str, first.absolute_path)) or '<root>'}）",
                               request=request,
                               next_action="按合同补齐该字段；缺字段不会被当作空值执行。")

        spec = OPERATIONS.get(request["operation"])
        if spec is None:
            return self.result(None, "REFUSED", "UNKNOWN_OPERATION",
                               f"没有声明过的操作不执行：{request['operation']}", request=request)

        if not spec.implemented:
            return self.result(spec, "NOT_IMPLEMENTED", spec.reason_code, spec.reason,
                               request=request, next_action=spec.next_action)

        scope_failure = self._scope_failure(request)
        if scope_failure is not None:
            code, reason = scope_failure
            return self.result(spec, "REFUSED", code, reason, request=request,
                               next_action="把边界收窄到本仓库内的项目路径。")

        decision = self.gate.evaluate(spec.action, target=request["operation"],
                                      scope=";".join(request["scope"]["boundaries"]),
                                      executor=request["actor"])
        if decision.status.value != "allowed":
            status = _STATUS_BY_DECISION.get(decision.status.value, "REFUSED")
            return self.result(spec, status, f"GATE_{decision.status.value.upper()}", decision.reason,
                               request=request,
                               next_action="该决定由策略给出，执行器与调用方都不是最终授权源。")

        if request["operation"] == "work-unit.create":
            return self._create_work_unit(request, spec)
        if request["operation"] == "config.diff":
            return self._config_diff(request, spec)
        return self.result(spec, "NOT_IMPLEMENTED", "DISPATCH_MISSING",
                           "该操作通过了检查但没有实现分支。", request=request)

    # -- checks -------------------------------------------------------------
    def _scope_failure(self, request: dict[str, Any]) -> tuple[str, str] | None:
        """Every declared boundary must resolve inside this repository.

        A request may name the project it acts on; it may not widen that project's filesystem. E:/F: are
        forbidden roots (project-data-boundary.json) and are refused by name so the reason is legible.
        """
        for raw in request["scope"]["boundaries"]:
            text = str(raw or "").strip()
            if not text:
                return ("EMPTY_BOUNDARY", "边界为空，不能代表一个范围。")
            lowered = text.replace("\\", "/").lower()
            if lowered.startswith(("e:/", "f:/")):
                return ("FORBIDDEN_ROOT", f"边界 {text} 位于受保护的外部盘根，本项目的边界合同禁止读写。")
            candidate = Path(text)
            if candidate.is_absolute() and candidate.drive:
                try:
                    resolved = candidate.resolve()
                except OSError:
                    return ("UNRESOLVABLE_BOUNDARY", f"边界 {text} 无法解析，按失败关闭处理。")
                if not resolved.is_relative_to(self.project_root):
                    return ("OUT_OF_PROJECT_SCOPE", f"边界 {text} 在本仓库之外，控制服务不接受越界写。")
        return None

    def _ceiling(self, requested: str) -> str:
        order = ["NO_EVIDENCE", "SIMULATED", "SYNTHETIC", "INTEGRATED", "REAL"]
        return requested if order.index(requested) <= order.index(self.evidence_ceiling) else self.evidence_ceiling

    # -- implemented operations --------------------------------------------
    def _create_work_unit(self, request: dict[str, Any], spec: OperationSpec) -> dict[str, Any]:
        task_id = str(request["task_id"] or "").strip()
        if not task_id:
            return self.result(spec, "REFUSED", "TASK_ID_REQUIRED",
                               "创建 Work Unit 必须给出确定性的 task_id：幂等重放靠它，不靠时间去猜。",
                               request=request)
        goal = str((request.get("payload") or {}).get("goal") or "").strip()
        if not goal:
            return self.result(spec, "REFUSED", "GOAL_REQUIRED",
                               "没有目标的工作单元不是一个可执行对象；不接受空目标。", request=request)

        record = {
            "task_id": task_id,
            "project_id": request["project_id"],
            "status": "QUEUED",
            "checkpoint": {
                "goal": goal,
                "boundaries": list(request["scope"]["boundaries"]),
                "granted_by": request["scope"]["granted_by"],
                "idempotency_key": request["idempotency_key"],
                "requested_at": request["requested_at"],
            },
        }
        with self._lock:
            existing = {row["task_id"]: row for row in self.store.list_tasks()}.get(task_id)
            replayed = False
            if existing is not None:
                prior_key = str((existing.get("checkpoint") or {}).get("idempotency_key") or "")
                if prior_key and prior_key != request["idempotency_key"]:
                    return self.result(spec, "REFUSED", "IDEMPOTENCY_CONFLICT",
                                       f"task_id {task_id} 已存在且属于另一个幂等身份；不覆盖别人的工作单元。",
                                       request=request, task_id=task_id)
                replayed = True
            else:
                self.store.upsert_task(record)

        readback_row = {row["task_id"]: row for row in self.store.list_tasks()}.get(task_id)
        if readback_row is None:
            return self.result(spec, "READBACK_MISMATCH", "READBACK_MISSING",
                               f"写入后读不到 {task_id}：写没有被证实，不返回成功。",
                               request=request, task_id=task_id)
        projected = project_task_record(readback_row)
        digest = hashlib.sha256(json.dumps(projected, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":")).encode("utf-8")).hexdigest()
        receipt = {
            "receipt_id": f"work-unit.create:{task_id}",
            "kind": "REPLAY" if replayed else "WORK_UNIT_QUEUED",
            "observed_at": _now(),
            "digest": digest,
        }
        self._append_receipt(receipt, projected)
        return self.result(spec, "ACCEPTED", spec.reason_code, spec.reason,
                           request=request, task_id=task_id, receipt=receipt,
                           readback={**projected, "replayed": replayed},
                           evidence=self._ceiling("SYNTHETIC"), next_action=spec.next_action)

    def _config_diff(self, request: dict[str, Any], spec: OperationSpec) -> dict[str, Any]:
        """Compute a plan through the existing config control plane. Plan is never reported as a write."""
        payload = request.get("payload") or {}
        target = str(payload.get("target_file") or "").strip()
        field = str(payload.get("field") or "").strip()
        wanted = payload.get("value")
        if not target or not field:
            return self.result(spec, "REFUSED", "DIFF_INPUT_INCOMPLETE",
                               "diff 需要 target_file 与 field；缺输入不产出看起来像计划的空答案。",
                               request=request)
        # Relative targets are relative to the project, never to whatever directory the caller ran
        # the service from — a diff computed against the wrong file is a plan built on nothing.
        path = Path(target)
        candidate = path if path.is_absolute() else (self.project_root / path)
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = None
        if resolved is None or not resolved.is_relative_to(self.project_root):
            return self.result(spec, "REFUSED", "TARGET_OUT_OF_PROJECT",
                               f"配置目标 {target} 不在本仓库内；本轮没有对它之外的写权或读权。", request=request)
        before = resolved.read_text(encoding="utf-8", errors="replace") if resolved.is_file() else None
        after_field_present = before is not None and field in before
        changes = [{
            "field": field,
            "before": "<read-only: value not projected>" if before is not None else None,
            "after_declared": True if wanted is not None else False,
            "present_before": after_field_present,
        }]
        # PLANNED, not ACCEPTED: a diff that wrote nothing must not arrive in the same status shape
        # as a write that was verified by readback.
        return self.result(spec, "PLANNED", spec.reason_code, spec.reason, request=request,
                           receipt=None,
                           readback={"plan_only": True, "target": resolved.relative_to(self.project_root).as_posix(),
                                     "changes": changes,
                                     "written": False,
                                     "next": "config.apply 需要对该 exact target 的单独授权"},
                           evidence=self._ceiling("SYNTHETIC"), next_action=spec.next_action)

    def _append_receipt(self, receipt: dict[str, Any], projected: dict[str, Any]) -> None:
        if self.receipts_path is None:
            return
        line = json.dumps({"receipt": receipt, "record": projected}, ensure_ascii=False, sort_keys=True)
        self.receipts_path.parent.mkdir(parents=True, exist_ok=True)
        with self.receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


# ---------------------------------------------------------------------------
# loopback HTTP boundary
# ---------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    server_version = "WORK-LAB-Control/1"

    @property
    def plane(self) -> ControlPlane:
        return self.server.plane  # type: ignore[attr-defined]

    def log_message(self, *args: Any) -> None:  # no request bodies in logs
        return

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _refused(self, status: int, code: str, reason: str) -> None:
        self._send(status, {"schema_version": "worklab/control-error/v1", "reason_code": code,
                            "reason": reason, "observed_at": _now()})

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True  # same-origin tools (curl, the shell opened from disk) send no Origin
        return _allowed_origin(origin)

    SHELL_ASSETS = {
        "/": ("index.html", "text/html; charset=utf-8"),
        "/control-shell.css": ("control-shell.css", "text/css; charset=utf-8"),
        "/control-shell.js": ("control-shell.js", "text/javascript; charset=utf-8"),
    }

    def _serve_shell(self, path: str) -> None:
        """Serve the thin shell from the same loopback origin as the write API.

        One origin means one place to reason about: the page that can post an operation is delivered by
        the process that executes it, so there is no cross-origin grant to widen and no second server to
        keep honest. CSP is emitted on the response as well as in the document, and no inline script or
        style is allowed by either.
        """
        asset = self.SHELL_ASSETS[path]
        source = self.plane.project_root / "apps" / "control-surface" / asset[0]
        if not source.is_file():
            self._refused(404, "SHELL_ASSET_MISSING", f"薄壳文件缺失：{asset[0]}")
            return
        body = source.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", asset[1])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server contract
        if not _is_loopback_authority(self.headers.get("Host")) or not self._origin_ok():
            self._refused(403, "NOT_LOOPBACK", "控制服务只监听回环地址，只接受回环来源。")
            return
        if self.path in self.SHELL_ASSETS:
            self._serve_shell(self.path)
        elif self.path == "/api/control/descriptor":
            self._send(200, self.plane.descriptor())
        elif self.path == "/health":
            self._send(200, {"schema_version": SCHEMA_VERSION, "status": "SERVING", "observed_at": _now()})
        else:
            self._refused(404, "UNKNOWN_READ", "控制服务只暴露 descriptor 与 health 两个读端点。")

    def do_POST(self) -> None:  # noqa: N802 - http.server contract
        if not _is_loopback_authority(self.headers.get("Host")) or not self._origin_ok():
            self._refused(403, "NOT_LOOPBACK", "控制服务只监听回环地址，只接受回环来源。")
            return
        if self.path != "/api/control/operations":
            self._refused(404, "UNKNOWN_WRITE", "写入口只有一个：POST /api/control/operations。")
            return
        try:
            length = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            self._refused(400, "EMPTY_BODY", "没有请求体，无法构成一个操作。")
            return
        if length > MAX_BODY_BYTES:
            self._refused(413, "BODY_TOO_LARGE", f"操作请求超过 {MAX_BODY_BYTES} 字节上限。")
            return
        raw = self.rfile.read(length)
        try:
            request = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            self._refused(400, "UNPARSEABLE_REQUEST", f"请求不是合法 JSON：{type(error).__name__}")
            return
        if not isinstance(request, dict):
            self._refused(400, "REQUEST_NOT_OBJECT", "操作请求必须是一个对象。")
            return
        # A refused decision is still a 200 answer: the contract carries the verdict, HTTP 200 does not
        # mean the work happened, and the shell reads status/reason_code/reason from the typed result.
        self._send(200, self.plane.execute(request))

    def do_PUT(self) -> None: self._method_not_allowed()      # noqa: N802
    def do_PATCH(self) -> None: self._method_not_allowed()    # noqa: N802
    def do_DELETE(self) -> None: self._method_not_allowed()   # noqa: N802

    def _method_not_allowed(self) -> None:
        self._refused(405, "METHOD_NOT_ALLOWED", "控制服务只接受 POST 一个写方法与 GET 两个读方法。")


class ControlServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, plane: ControlPlane, host: str = "127.0.0.1", port: int = 0) -> None:
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError(f"the control service binds loopback only, refused: {host}")
        super().__init__((host, port), _Handler)
        self.plane = plane
        self.host, self.bound_port = host, self.server_address[1]

    def endpoint_descriptor(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "host": self.host,
            "port": self.bound_port,
            "pid": os.getpid(),
            "started_at": _now(),
            "transport": "loopback-only",
            "endpoints": ["/api/control/descriptor", "/api/control/operations", "/health"],
            "evidence_ceiling": self.plane.evidence_ceiling,
        }

    def write_descriptor(self, path: Path) -> dict[str, Any]:
        """Publish where this process actually listens, so a shell discovers it instead of guessing a port."""
        descriptor = self.endpoint_descriptor()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(descriptor, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return descriptor

    def serve_loop(self, descriptor_path: Path | None = None) -> None:
        if descriptor_path is not None:
            self.write_descriptor(descriptor_path)
        try:
            self.serve_forever()
        finally:
            if descriptor_path is not None and descriptor_path.is_file():
                descriptor_path.unlink()


def build_plane(runtime_root: Path, project_root: Path, *, evidence_ceiling: str = "SYNTHETIC") -> ControlPlane:
    """Open the ONE canonical store the Observer also reads, then hand the control plane to it."""
    store = CanonicalStore(Path(runtime_root).resolve() / "canonical.sqlite")
    return ControlPlane(store, project_root=project_root, evidence_ceiling=evidence_ceiling,
                        receipts_path=Path(runtime_root) / RECEIPTS_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=_ROOT)
    parser.add_argument("--runtime-root", type=Path,
                        help="the same runtime root the sidecar uses; omit for a fresh in-boundary fixture")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    runtime_root = args.runtime_root or fixture_dir(prefix="control-service-")
    plane = build_plane(runtime_root, args.project_root,
                        evidence_ceiling="INTEGRATED" if args.runtime_root else "SYNTHETIC")
    server = ControlServer(plane, host=args.host, port=args.port)
    # flush=True is not decoration: a launcher that reads this pipe waits on the port line, and a
    # buffered stdout would make a correctly-starting service look hung (the sidecar flushes for the
    # same reason).
    print(f"CONTROL_SERVING url=http://{server.host}:{server.bound_port} runtime_root={runtime_root}",
          flush=True)
    try:
        server.serve_loop(Path(runtime_root) / DESCRIPTOR_PATH)
    except KeyboardInterrupt:
        pass
    finally:
        plane.store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
