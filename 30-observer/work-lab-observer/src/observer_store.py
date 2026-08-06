from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from observer_runtime import (
    ObserverInputError,
    append_events,
    project_tasks,
    quality_summary,
)


class ObserverStore:
    """Persist only Observer-owned events under the project runtime boundary."""

    FILENAME = "observer-events.jsonl"

    def __init__(self, runtime_root: Path, *, project_root: Path, max_events: int = 256) -> None:
        self.project_root = Path(project_root).resolve()
        if not (self.project_root / ".git").exists():
            raise ValueError("Observer store project root must be a Git project")
        self.runtime_root = Path(runtime_root).resolve()
        if not self.runtime_root.is_dir():
            raise ValueError("Observer runtime root must already exist")
        expected = (self.project_root / ".hermes" / "task-runtime" / "observer").resolve()
        if self.runtime_root != expected:
            raise ValueError("Observer store must stay in the project Observer runtime root")
        if max_events < 1:
            raise ValueError("max_events must be positive")
        self.max_events = max_events
        self.path = self.runtime_root / self.FILENAME

    def read_events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        seen: set[str] = set()
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise ObserverInputError(f"observer event store unreadable: {exc}") from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ObserverInputError(f"observer event store malformed at line {line_number}") from exc
            if not isinstance(raw, dict):
                raise ObserverInputError(f"observer event store record must be an object at line {line_number}")
            accepted = append_events(events, [raw], max_events=self.max_events)
            if accepted != 1 or raw["eventId"] in seen:
                raise ObserverInputError(f"duplicate observer event at line {line_number}")
            seen.add(raw["eventId"])
        return events

    def append(self, incoming: Iterable[dict[str, Any]]) -> int:
        events = self.read_events()
        before = len(events)
        append_events(events, incoming, max_events=self.max_events)
        added = len(events) - before
        if added:
            self._write(events)
        return added

    def rebuild_projection(self) -> dict[str, Any]:
        events = self.read_events()
        return {
            "tasks": project_tasks(events),
            "quality": quality_summary(events),
        }

    def _write(self, events: list[dict[str, Any]]) -> None:
        payload = "".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events)
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.runtime_root,
                prefix=".observer-events-",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            temporary = None
        finally:
            if temporary:
                try:
                    Path(temporary).unlink()
                except FileNotFoundError:
                    pass
