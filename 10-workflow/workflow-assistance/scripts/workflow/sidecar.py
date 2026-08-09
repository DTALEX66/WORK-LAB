"""Local-first Workflow Assistance sidecar with read-only health/projection routes."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

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
        data = self.tasks._read()
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


def create_server(sidecar: WorkflowSidecar, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            origin = self.headers.get("Origin")
            if origin and not (origin.startswith("http://127.0.0.1") or origin.startswith("http://localhost")):
                self.send_json(403, {"status": "origin_not_allowed"})
                return
            if self.path == "/healthz":
                self.send_json(200, sidecar.health())
            elif self.path in {"/api/projection", "/api/v1/snapshot"}:
                self.send_json(200, sidecar.projection())
            elif self.path == "/api/v1/events":
                events = sidecar.ledger.projection()["events"]
                last_id = self.headers.get("Last-Event-ID")
                if last_id:
                    for index, event in enumerate(events):
                        if event.get("event_id") == last_id:
                            events = events[index + 1:]
                            break
                body = "".join(f"id: {event['event_id']}\\ndata: {json.dumps(event, ensure_ascii=False)}\\n\\n" for event in events).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_json(404, {"status": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            self.send_json(405, {"status": "method_not_allowed"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)
