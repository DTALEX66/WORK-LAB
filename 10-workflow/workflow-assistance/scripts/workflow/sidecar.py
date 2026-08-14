"""Local-first Workflow Assistance sidecar with read-only health/projection routes."""
from __future__ import annotations

import argparse
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import queue
import threading
import time
from typing import Any
from urllib.parse import urlsplit
import uuid

from sidecar_lock import SingleInstanceLock
from canonical_store import CanonicalStore
from sse_hub import HEARTBEAT_SECONDS, LIVE, LiveProjection, SNAPSHOT, STALE, render_sse_frames
from composition_root import build_v3_snapshot, load_approved_index
from live_gate import evaluate_live
from sse_revision import SseRevisionHub
from snapshot_validator import validate_snapshot


class WorkflowSidecar:
    def __init__(self, project_root: Path, runtime_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.runtime_root = runtime_root.resolve()
        self.store = CanonicalStore(self.runtime_root / "canonical.sqlite")
        self.live = LiveProjection(self.store)
        # WLGM composition root: approved index + persistent SSE revision hub.
        self.index = load_approved_index(self.store)  # 失败时降级空索引，不 raise
        self.revision_hub = SseRevisionHub()
        self._revision = self.store.seed_revision()
        self._last_heartbeat_at = __import__("time").time()
        self._last_write_at = __import__("time").time()
        self._sse_connected = False
        self._events_url: str | None = None
        self._watch_stop = threading.Event()
        self._watch_thread: threading.Thread | None = None

    def _canonical_fingerprint(self) -> str:
        canonical = self.store.projection()
        stable = {
            "integrity": canonical["integrity"],
            "tables": canonical["tables"],
            "tasks_by_status": canonical["tasks_by_status"],
            "telemetry_events": canonical["telemetry_events"],
            "usage_summary": canonical["usage_summary"],
            "ci_summary": canonical["ci_summary"],
        }
        return json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def start_live_updates(self, interval_seconds: float = 0.25) -> None:
        """Publish canonical deltas written by the separate Workflow worker."""
        if interval_seconds <= 0:
            raise ValueError("live update interval must be positive")
        if self._watch_thread and self._watch_thread.is_alive():
            return
        self._watch_stop.clear()
        last_fingerprint = self._canonical_fingerprint()
        # P0-4: LIVE only comes from the live gate; the watcher must not
        # declare LIVE by itself.
        self.live.set_mode(SNAPSHOT)

        def _watch() -> None:
            nonlocal last_fingerprint
            while not self._watch_stop.wait(interval_seconds):
                try:
                    current = self._canonical_fingerprint()
                except Exception:  # fail closed if canonical readback is unavailable
                    if self.live.mode() != STALE:
                        self.live.set_mode(STALE)
                    continue
                if current != last_fingerprint:
                    last_fingerprint = current
                    self._last_write_at = __import__("time").time()
                    self.publish_observed()

        self._watch_thread = threading.Thread(
            target=_watch,
            daemon=True,
            name="workflow-sidecar-canonical-watch",
        )
        self._watch_thread.start()

    def stop_live_updates(self) -> None:
        self._watch_stop.set()
        if self._watch_thread and self._watch_thread is not threading.current_thread():
            self._watch_thread.join(timeout=2.0)
        self._watch_thread = None

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "readOnlyControl": True, "ledgerOwner": "workflow-assistance", "observerMutation": False}

    def projection(self) -> dict[str, Any]:
        canonical = self.store.projection()
        statuses = canonical["tasks_by_status"]
        return {
            "schema_version": "workflow/sidecar-projection/v1",
            "mode": self.live.mode(),
            "health": self.health(),
            "integrity": canonical["integrity"],
            "telemetry": {"count": canonical["telemetry_events"]},
            "tasks": {"count": sum(statuses.values()), "by_status": statuses},
            "usage": canonical["usage_summary"],
            "ci": canonical["ci_summary"],
            "observed_at": canonical["observed_at"],
        }

    def publish_observed(self) -> str:
        legacy_id = self.live.hub.publish("observed", self.projection())
        # 新链路双写：persistent revision hub（sidecar.v3_snapshot 由 live gate
        # 提供 transport verdict；watch 触发时数据已变化）。
        snapshot = self.v3_snapshot()
        self._revision = self.revision_hub.publish("observed", snapshot)
        return legacy_id

    def _collector_coverage(self) -> tuple[int, int]:
        rows = self.store.list_collector_health()
        fresh = sum(1 for row in rows if str(row.get("state") or "") == "healthy")
        return fresh, len(rows)

    def v3_snapshot(self) -> dict:
        """P0-2: /api/v1/snapshot returns the v3 snapshot; transport verdict
        comes exclusively from the live gate (never fabricated LIVE)."""
        fresh, total = self._collector_coverage()
        verdict = evaluate_live(
            snapshot_valid=bool(validate_snapshot(self.live_projection_skeleton())["valid"]),
            sse_connected=self._sse_connected,
            heartbeat_age_seconds=__import__("time").time() - self._last_heartbeat_at,
            heartbeat_threshold_seconds=HEARTBEAT_SECONDS,
            cursor_valid=self._revision > 0,
            writer_watermark_age_seconds=__import__("time").time() - self._last_write_at,
            writer_watermark_threshold_seconds=60.0,
            coverage=fresh if total else None,
        )
        return build_v3_snapshot(
            self.store,
            self.index,
            revision=self._revision,
            events_url=self._events_url,
            transport_state=verdict.state,
        )

    def live_projection_skeleton(self) -> dict:
        """Minimal valid snapshot skeleton for live-gate schema validation."""
        return build_v3_snapshot(
            self.store,
            self.index,
            revision=self._revision,
            events_url=self._events_url,
            transport_state="UNKNOWN",
        )

    def close(self) -> None:
        self.stop_live_updates()
        self.store.close()


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
        self.sidecar = sidecar
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
                    "startedAt": __import__("time").time(),
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
                try:
                    self.sidecar.close()
                finally:
                    self._sidecar_lock.release()


def create_server(
    sidecar: WorkflowSidecar,
    host: str = "127.0.0.1",
    port: int = 0,
    *,
    live_updates: bool = False,
) -> ThreadingHTTPServer:
    if not _is_loopback_host(host):
        raise ValueError("sidecar host must be loopback-only")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
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
            elif path == "/api/projection":
                self.send_json(200, sidecar.projection())  # 旧 v1 兼容，保留
            elif path == "/api/v1/snapshot":
                self.send_json(200, sidecar.v3_snapshot())  # P0-2: 真 v3
            elif path == "/api/v1/events":
                last_id = self.headers.get("Last-Event-ID")
                client = sidecar.revision_hub.connect(uuid.uuid4().hex, last_event_id=last_id)
                if client is None:
                    self.send_json(503, {"status": "too_many_connections"})
                    return
                sidecar._sse_connected = True
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Connection", "keep-alive")
                cors_origin = self._cors_origin()
                if cors_origin:
                    self.send_header("Access-Control-Allow-Origin", cors_origin)
                    self.send_header("Vary", "Origin")
                self.end_headers()
                try:
                    frames = sidecar.revision_hub.frames_for(client)
                    if not frames:  # 新连接：先推一帧 snapshot 事件
                        frames = [SseRevisionHub._frame("snapshot", sidecar.v3_snapshot(), sidecar._revision)]
                    self.wfile.write("".join(frames).encode("utf-8"))
                    self.wfile.flush()
                    while True:
                        time.sleep(HEARTBEAT_SECONDS / 2)
                        sidecar._last_heartbeat_at = time.time()
                        frames = sidecar.revision_hub.frames_for(client)
                        if not frames:
                            frames = [sidecar.revision_hub.heartbeat_frame()]
                        self.wfile.write("".join(frames).encode("utf-8"))
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return
                finally:
                    sidecar.revision_hub.disconnect(client.client_id)
                    sidecar._sse_connected = False
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

    server: _WorkflowHTTPServer | None = None
    try:
        server = _WorkflowHTTPServer((host, port), Handler, sidecar)
        # P0-4: backfill eventsUrl once the real port is known (frontend reads
        # transport.eventsUrl to subscribe).
        url_host = _url_host(str(server.server_address[0]))
        sidecar._events_url = f"http://{url_host}:{int(server.server_address[1])}/api/v1/events"
        if live_updates:
            sidecar.start_live_updates()
        return server
    except Exception:
        if server is not None:
            server.server_close()
        else:
            sidecar.close()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the Workflow Assistance loopback-only sidecar")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    runtime_root = (args.runtime_root or project_root / ".hermes" / "task-runtime" / "workflow").resolve()
    server = create_server(
        WorkflowSidecar(project_root, runtime_root),
        args.host,
        args.port,
        live_updates=True,
    )
    print(
        f"WORKFLOW_SIDECAR_READY url=http://{args.host}:{server.server_port} ledger_owner=workflow-assistance",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
