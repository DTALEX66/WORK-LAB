#!/usr/bin/env python3
"""Local Windows token monitor for JSON/JSONL usage logs.

The monitor only counts explicit provider usage fields. It never estimates token
counts from characters and never displays raw log lines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

MODEL_KEYS = ("model", "model_name", "modelName")
REQUEST_KEYS = ("request_id", "requestId", "id")
TIMESTAMP_KEYS = ("timestamp", "created", "created_at", "time")
_JSON_START = re.compile(r"\{")


@dataclass(frozen=True)
class UsageRecord:
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    model: str
    request_id: str
    timestamp: str
    source: str = "provider_usage"

    @property
    def exact(self) -> bool:
        return self.input_tokens is not None or self.output_tokens is not None or self.total_tokens is not None


@dataclass
class UsageTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    records: int = 0
    unrecognized_lines: int = 0
    by_model: dict[str, "UsageTotals"] = field(default_factory=dict)

    def add(self, record: UsageRecord) -> None:
        input_value = record.input_tokens or 0
        output_value = record.output_tokens or 0
        total_value = record.total_tokens
        if total_value is None:
            total_value = input_value + output_value
        self.input_tokens += input_value
        self.output_tokens += output_value
        self.total_tokens += total_value
        self.records += 1
        model = record.model or "(unknown model)"
        if model not in self.by_model:
            self.by_model[model] = UsageTotals()
        child = self.by_model[model]
        child.input_tokens += input_value
        child.output_tokens += output_value
        child.total_tokens += total_value
        child.records += 1


def _as_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    if isinstance(value, float) and value.is_integer() and value >= 0:
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _first_text(data: dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if value is not None and isinstance(value, (str, int, float)):
            return str(value)
    return default


def _token_value(data: dict[str, Any], names: tuple[str, ...]) -> int | None:
    for name in names:
        value = _as_nonnegative_int(data.get(name))
        if value is not None:
            return value
    return None


def _usage_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        token_values = {
            "input": _token_value(value, ("prompt_tokens", "input_tokens")),
            "output": _token_value(value, ("completion_tokens", "output_tokens")),
            "total": _token_value(value, ("total_tokens",)),
        }
        if any(item is not None for item in token_values.values()):
            yield value
        for child in value.values():
            yield from _usage_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _usage_dicts(child)


def parse_usage_payload(payload: Any, *, source: str = "provider_usage") -> list[UsageRecord]:
    """Extract explicit usage records from a decoded JSON payload.

    We intentionally do not infer tokens from text, byte length, or model name.
    """
    if not isinstance(payload, (dict, list)):
        return []
    root = payload if isinstance(payload, dict) else {}
    records: list[UsageRecord] = []
    seen: set[tuple[int | None, int | None, int | None, str, str]] = set()
    for usage in _usage_dicts(payload):
        values = {
            "input": _token_value(usage, ("prompt_tokens", "input_tokens")),
            "output": _token_value(usage, ("completion_tokens", "output_tokens")),
            "total": _token_value(usage, ("total_tokens",)),
        }
        # Prefer the nearest parent/root metadata when usage is nested in a response.
        model = _first_text(usage, MODEL_KEYS) or _first_text(root, MODEL_KEYS, "unknown")
        request_id = _first_text(usage, REQUEST_KEYS) or _first_text(root, REQUEST_KEYS)
        timestamp = _first_text(usage, TIMESTAMP_KEYS) or _first_text(root, TIMESTAMP_KEYS)
        key = (values["input"], values["output"], values["total"], model, request_id)
        if key in seen:
            continue
        seen.add(key)
        total = values["total"]
        if total is None and values["input"] is not None and values["output"] is not None:
            total = values["input"] + values["output"]
        records.append(
            UsageRecord(
                input_tokens=values["input"],
                output_tokens=values["output"],
                total_tokens=total,
                model=model,
                request_id=request_id,
                timestamp=timestamp,
                source=source,
            )
        )
    return records


def decode_log_line(line: str) -> Any | None:
    """Decode JSONL or a timestamp/prefix followed by a JSON object."""
    text = line.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_START.search(text)
        if not match:
            return None
        try:
            return json.loads(text[match.start() :])
        except json.JSONDecodeError:
            return None


def parse_log_line(line: str) -> list[UsageRecord]:
    payload = decode_log_line(line)
    return parse_usage_payload(payload) if payload is not None else []


class LogTail:
    """Read only appended lines and handle truncation/file rotation."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.offset = 0
        self.identity: tuple[int, int] | None = None

    def read_new_lines(self) -> list[str]:
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return []
        identity = (getattr(stat, "st_dev", 0), stat.st_ino)
        if self.identity != identity or stat.st_size < self.offset:
            self.offset = 0
            self.identity = identity
        try:
            with self.path.open("r", encoding="utf-8", errors="replace") as handle:
                handle.seek(self.offset)
                lines = handle.readlines()
                self.offset = handle.tell()
        except (FileNotFoundError, PermissionError, OSError):
            return []
        return lines


class UsageMonitor:
    def __init__(self, path: Path) -> None:
        self.tail = LogTail(path)
        self.totals = UsageTotals()
        self._seen_fingerprints: set[str] = set()

    def poll(self) -> int:
        records_added = 0
        for line in self.tail.read_new_lines():
            records = parse_log_line(line)
            if not records:
                if line.strip():
                    self.totals.unrecognized_lines += 1
                continue
            fingerprint_base = line.strip().encode("utf-8", errors="replace")
            for index, record in enumerate(records):
                fingerprint = hashlib.sha256(fingerprint_base + str(index).encode()).hexdigest()
                if fingerprint in self._seen_fingerprints:
                    continue
                self._seen_fingerprints.add(fingerprint)
                self.totals.add(record)
                records_added += 1
        return records_added


def default_log_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "hermes" / "logs" / "agent.log"
    return Path.home() / ".local" / "share" / "hermes" / "logs" / "agent.log"


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "agent.log"
        path.write_text(
            json.dumps({"model": "test-model", "usage": {"prompt_tokens": 11, "completion_tokens": 7}})
            + "\n"
            + json.dumps({"model": "test-model", "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}})
            + "\nnot usage\n",
            encoding="utf-8",
        )
        monitor = UsageMonitor(path)
        if monitor.poll() != 2:
            raise AssertionError("expected two usage records")
        if monitor.totals.input_tokens != 14 or monitor.totals.output_tokens != 9 or monitor.totals.total_tokens != 23:
            raise AssertionError(f"unexpected totals: {monitor.totals}")
        if monitor.totals.unrecognized_lines != 1:
            raise AssertionError("expected one unrecognized line")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"usage": {"total_tokens": 4}}) + "\n")
        if monitor.poll() != 1 or monitor.totals.total_tokens != 27:
            raise AssertionError("append polling failed")
    print("TOKEN_MONITOR_SELF_TEST_PASS")
    return 0


def run_gui(path: Path, poll_ms: int) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError as exc:
        print(f"Tkinter is unavailable: {exc}", file=sys.stderr)
        return 2

    class App:
        def __init__(self, root: Any) -> None:
            self.root = root
            self.monitor = UsageMonitor(path)
            self.running = False
            root.title("Hermes Token Monitor")
            root.geometry("720x460")
            root.minsize(640, 380)
            root.columnconfigure(0, weight=1)
            root.rowconfigure(2, weight=1)

            top = ttk.Frame(root, padding=10)
            top.grid(row=0, column=0, sticky="ew")
            top.columnconfigure(1, weight=1)
            ttk.Label(top, text="日志文件").grid(row=0, column=0, padx=(0, 6))
            self.path_var = tk.StringVar(value=str(path))
            ttk.Entry(top, textvariable=self.path_var).grid(row=0, column=1, sticky="ew")
            ttk.Button(top, text="选择", command=self.choose_file).grid(row=0, column=2, padx=6)
            self.toggle = ttk.Button(top, text="开始监控", command=self.toggle_monitor)
            self.toggle.grid(row=0, column=3)

            stats = ttk.Frame(root, padding=(10, 0, 10, 8))
            stats.grid(row=1, column=0, sticky="ew")
            self.labels: dict[str, tk.StringVar] = {}
            for column, (key, title) in enumerate(
                (("input", "输入"), ("output", "输出"), ("total", "总计"), ("records", "请求数"), ("unknown", "未识别行"))
            ):
                box = ttk.LabelFrame(stats, text=title, padding=8)
                box.grid(row=0, column=column, padx=(0, 6), sticky="ew")
                stats.columnconfigure(column, weight=1)
                var = tk.StringVar(value="0")
                self.labels[key] = var
                ttk.Label(box, textvariable=var, font=("Segoe UI", 15, "bold")).pack()

            body = ttk.Frame(root, padding=(10, 0, 10, 10))
            body.grid(row=2, column=0, sticky="nsew")
            body.columnconfigure(0, weight=1)
            body.rowconfigure(0, weight=1)
            self.table = ttk.Treeview(body, columns=("model", "input", "output", "total", "records"), show="headings")
            for key, heading, width in (("model", "模型", 250), ("input", "输入", 90), ("output", "输出", 90), ("total", "总计", 90), ("records", "请求数", 80)):
                self.table.heading(key, text=heading)
                self.table.column(key, width=width, anchor="e" if key != "model" else "w")
            self.table.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.table.configure(yscrollcommand=scrollbar.set)
            self.status = tk.StringVar(value="未启动；不会读取文件，直到点击“开始监控”。")
            ttk.Label(root, textvariable=self.status, padding=(10, 0, 10, 8)).grid(row=3, column=0, sticky="w")

        def choose_file(self) -> None:
            selected = filedialog.askopenfilename(title="选择 Hermes 日志", filetypes=(("日志文件", "*.log *.jsonl *.json"), ("所有文件", "*.*")))
            if selected:
                self.path_var.set(selected)

        def toggle_monitor(self) -> None:
            if self.running:
                self.running = False
                self.toggle.configure(text="开始监控")
                self.status.set("已暂停")
                return
            selected = Path(self.path_var.get()).expanduser()
            self.monitor = UsageMonitor(selected)
            self.running = True
            self.toggle.configure(text="暂停监控")
            self.status.set(f"监控中：{selected}")
            self.tick()

        def tick(self) -> None:
            if not self.running:
                return
            self.monitor.poll()
            totals = self.monitor.totals
            self.labels["input"].set(f"{totals.input_tokens:,}")
            self.labels["output"].set(f"{totals.output_tokens:,}")
            self.labels["total"].set(f"{totals.total_tokens:,}")
            self.labels["records"].set(str(totals.records))
            self.labels["unknown"].set(str(totals.unrecognized_lines))
            for item in self.table.get_children():
                self.table.delete(item)
            for model, values in sorted(totals.by_model.items()):
                self.table.insert("", "end", values=(model, values.input_tokens, values.output_tokens, values.total_tokens, values.records))
            self.root.after(poll_ms, self.tick)

    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="本地 Hermes 实时 Token Monitor；只统计日志中的真实 usage 字段")
    parser.add_argument("--file", type=Path, default=default_log_path(), help="JSON/JSONL 日志路径；默认指向 Hermes agent.log")
    parser.add_argument("--poll-ms", type=int, default=500, help="轮询间隔，默认 500ms")
    parser.add_argument("--self-test", action="store_true", help="运行无 GUI 自检")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if args.poll_ms < 100:
        parser.error("--poll-ms must be >= 100")
    return run_gui(args.file, args.poll_ms)


if __name__ == "__main__":
    raise SystemExit(main())
