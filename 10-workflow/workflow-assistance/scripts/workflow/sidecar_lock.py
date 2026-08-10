from __future__ import annotations

import json
import os
from pathlib import Path
import uuid


class SingleInstanceLock:
    """PID-aware cross-process lock with stale-owner recovery.

    The lock never removes a live or unverifiable owner. Release is fenced by a
    per-acquisition token so one process cannot delete another process's lock.
    """

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self._owned = False
        self._token: str | None = None

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        if pid == os.getpid():
            return True
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            # Windows reports an invalid-parameter OSError for a missing PID.
            return False
        return True

    def _read_owner(self) -> tuple[bytes, dict[str, object]]:
        raw = self.path.read_bytes()
        try:
            owner = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("sidecar_lock_unreadable") from exc
        if not isinstance(owner, dict) or not isinstance(owner.get("pid"), int) or not isinstance(owner.get("token"), str):
            raise RuntimeError("sidecar_lock_invalid")
        return raw, owner

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        token = uuid.uuid4().hex
        payload = (json.dumps({"pid": os.getpid(), "token": token}, sort_keys=True) + "\n").encode("utf-8")
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                raw, owner = self._read_owner()
                if self._pid_alive(int(owner["pid"])):
                    raise RuntimeError("sidecar_already_running") from exc
                try:
                    if self.path.read_bytes() != raw:
                        raise RuntimeError("sidecar_lock_changed")
                    self.path.unlink()
                except FileNotFoundError:
                    pass
                continue
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            self._owned = True
            self._token = token
            return
        raise RuntimeError("sidecar_lock_contention")

    def release(self) -> None:
        if self._owned:
            try:
                _, owner = self._read_owner()
                if owner.get("pid") == os.getpid() and owner.get("token") == self._token:
                    self.path.unlink(missing_ok=True)
            except (FileNotFoundError, RuntimeError):
                pass
            self._owned = False
            self._token = None

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
