"""Local-first Workflow Assistance sidecar with read-only health/projection routes."""
from __future__ import annotations

import argparse
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
import uuid

from sidecar_lock import SingleInstanceLock
from telemetry_ledger import TelemetryLedger
from task_ledger import TaskLedger


class WorkflowSidecar:
    def __init__(self, project_root: Path, runtime_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.runtime_root = runtime_root.resolve()
        self.ledger = TelemetryLedger(self.runtime_root / "telemetry.jsonl")
        self.tasks = TaskLedger(self.runtime_root / "task-ledger")

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "readOnlyControl": True, "ledgerOwner": "workflow-assistance", "observerMutation": False}

    def projection(self) -> dict[str, Any]:
        # A GET must never initialize or mutate the Task Ledger.
        if self.tasks.path.exists():
            data = json.loads(self.tasks.path.read_text(encoding="utf-8"))
            if data.get("schema_version") != "workflow/task-ledger/v1" or not isinstance(data.get("tasks"), dict):
                raise ValueError("invalid task ledger schema")
        else:
            data = {"schema_version": "workflow/task-ledger/v1", "tasks": {}}
        statuses: dict[str, int] = {}
        for task in data.get("tasks", {}).values():
            status = str(task.get("status", "UNKNOWN"))
            statuses[status] = statuses.get(status, 0) + 1
        ci_path = self.runtime_root / "ci-observation.json"
        try:
            ci = json.loads(ci_path.read_text(encoding="utf-8")) if ci_path.exists() else {"state": "UNKNOWN"}
        except (OSError, UnicodeError, json.JSONDecodeError):
            ci = {"state": "UNKNOWN", "quality": "unreadable"}
        return {"schema_version": "workflow/sidecar-projection/v1", "health": self.health(), "telemetry": self.ledger.projection(), "tasks": {"count": sum(statuses.values()), "by_status": statuses}, "ci": {"state": ci.get("state", "UNKNOWN"), "observed_at": ci.get("observed_at"), "next_observation_at": ci.get("next_observation_at")}}


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    candidate = host.strip().strip("[]").lower()
    if candidate == "localhost":
        return True
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def _allowed_origin(origin: str) -> bool:
    try:
        parsed = urlsplit(origin)
        _ = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and _is_loopback_host(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
    )


def _url_host(host: str) -> str:
    return f"[{host}]" if ":" in host and not host.startswith("[") else host


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


class _WorkflowHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler], sidecar: WorkflowSidecar) -> None:
        self._sidecar_lock = SingleInstanceLock(sidecar.runtime_root / "sidecar.lock")
        self._sidecar_lock.acquire()
        self._endpoint_path = sidecar.runtime_root / "sidecar-endpoint.json"
        self._closed = False
        try:
            super().__init__(address, handler)
            host = str(self.server_address[0])
            url_host = _url_host(host)
            port = int(self.server_address[1])
            _atomic_json(
                self._endpoint_path,
                {
                    "schemaVersion": "workflow/sidecar-endpoint/v1",
                    "pid": os.getpid(),
                    "host": host,
                    "port": port,
                    "projectionUrl": f"http://{url_host}:{port}/api/v1/snapshot",
                    "eventsUrl": f"http://{url_host}:{port}/api/v1/events",
                },
            )
        except Exception:
            self._sidecar_lock.release()
            raise

    def server_close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            try:
                endpoint = json.loads(self._endpoint_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, UnicodeError, json.JSONDecodeError):
                endpoint = {}
            if endpoint.get("pid") == os.getpid() and endpoint.get("port") == self.server_port:
                self._endpoint_path.unlink(missing_ok=True)
        finally:
            try:
                super().server_close()
            finally:
                self._sidecar_lock.release()


def create_server(sidecar: WorkflowSidecar, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    if not _is_loopback_host(host):
        raise ValueError("sidecar host must be loopback-only")

    class Handler(BaseHTTPRequestHandler):
        def _cors_origin(self) -> str | None:
            origin = self.headers.get("Origin")
            return origin if origin and _allowed_origin(origin) else None

        def send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            cors_origin = self._cors_origin()
            if cors_origin:
                self.send_header("Access-Control-Allow-Origin", cors_origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            origin = self.headers.get("Origin")
            if origin and not _allowed_origin(origin):
                self.send_json(403, {"status": "origin_not_allowed"})
                return
            path = urlsplit(self.path).path
            if path == "/healthz":
                self.send_json(200, sidecar.health())
            elif path in {"/api/projection", "/api/v1/snapshot"}:
                self.send_json(200, sidecar.projection())
            elif path == "/api/v1/events":
                events = sidecar.ledger.projection()["events"]
                last_id = self.headers.get("Last-Event-ID")
                if last_id:
                    for index, event in enumerate(events):
                        if event.get("event_id") == last_id:
                            events = events[index + 1 :]
                            break
                frames = ["retry: 2000\n\n"]
                frames.extend(
                    f"id: {event['event_id']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                    for event in events
                )
                body = "".join(frames).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Content-Length", str(len(body)))
                cors_origin = self._cors_origin()
                if cors_origin:
                    self.send_header("Access-Control-Allow-Origin", cors_origin)
                    self.send_header("Vary", "Origin")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_json(404, {"status": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            self.send_json(405, {"status": "method_not_allowed"})

        def do_PUT(self) -> None:  # noqa: N802
            self.send_json(405, {"status": "method_not_allowed"})

        def do_PATCH(self) -> None:  # noqa: N802
            self.send_json(405, {"status": "method_not_allowed"})

        def do_DELETE(self) -> None:  # noqa: N802
            self.send_json(405, {"status": "method_not_allowed"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return _WorkflowHTTPServer((host, port), Handler, sidecar)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the Workflow Assistance loopback-only sidecar")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    runtime_root = (args.runtime_root or project_root / ".hermes" / "task-runtime" / "workflow").resolve()
    server = create_server(WorkflowSidecar(project_root, runtime_root), args.host, args.port)
    print(f"WORKFLOW_SIDECAR_READY url=http://{args.host}:{server.server_port} ledger_owner=workflow-assistance")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
