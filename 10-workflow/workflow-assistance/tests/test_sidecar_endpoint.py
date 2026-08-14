"""WLGM-210 tests: sidecar endpoint descriptor validation."""
from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from sidecar_endpoint import (
    capability_probe,
    read_descriptor,
    validate_descriptor,
)


def make_descriptor(**overrides):
    descriptor = {
        "schemaVersion": "workflow/sidecar-endpoint/v1",
        "pid": os.getpid(),
        "host": "127.0.0.1",
        "port": 54321,
        "startedAt": time.time(),
        "projectionUrl": "http://127.0.0.1:54321/api/v1/snapshot",
        "eventsUrl": "http://127.0.0.1:54321/api/v1/events",
    }
    descriptor.update(overrides)
    return descriptor


class SidecarEndpointTests(unittest.TestCase):
    def test_valid_descriptor_passes(self) -> None:
        result = validate_descriptor(make_descriptor(), require_ephemeral_port=False)
        self.assertTrue(result.valid, result.errors)

    def test_external_host_rejected(self) -> None:
        result = validate_descriptor(make_descriptor(host="evil.example.com", projectionUrl="http://evil.example.com:54321/api/v1/snapshot"))
        self.assertFalse(result.valid)
        self.assertTrue(any("loopback" in e for e in result.errors))

    def test_wrong_path_rejected(self) -> None:
        result = validate_descriptor(make_descriptor(projectionUrl="http://127.0.0.1:54321/api/dashboard"))
        self.assertFalse(result.valid)
        self.assertTrue(any("path" in e for e in result.errors))

    def test_query_bearing_url_rejected(self) -> None:
        result = validate_descriptor(make_descriptor(projectionUrl="http://127.0.0.1:54321/api/v1/snapshot?write=1"))
        self.assertFalse(result.valid)

    def test_dead_pid_rejected(self) -> None:
        result = validate_descriptor(make_descriptor(pid=99999999))
        self.assertFalse(result.valid)
        self.assertTrue(any("not alive" in e for e in result.errors))

    def test_future_started_at_rejected(self) -> None:
        result = validate_descriptor(make_descriptor(startedAt=time.time() + 3600))
        self.assertFalse(result.valid)
        self.assertTrue(any("future" in e for e in result.errors))

    def test_old_started_at_rejected(self) -> None:
        result = validate_descriptor(make_descriptor(startedAt=time.time() - 100 * 3600))
        self.assertFalse(result.valid)
        self.assertTrue(any("too old" in e for e in result.errors))

    def test_ephemeral_port_requirement(self) -> None:
        ok = validate_descriptor(make_descriptor(port=54321), require_ephemeral_port=True)
        self.assertTrue(ok.valid, ok.errors)
        low = validate_descriptor(make_descriptor(port=8080), require_ephemeral_port=True)
        self.assertFalse(low.valid)

    def test_none_descriptor_fails(self) -> None:
        result = validate_descriptor(None)
        self.assertFalse(result.valid)

    def test_read_descriptor_roundtrip(self) -> None:
        raw = tempfile.TemporaryDirectory()
        self.addCleanup(raw.cleanup)
        path = Path(raw.name) / "sidecar-endpoint.json"
        path.write_text(json.dumps(make_descriptor()), encoding="utf-8")
        descriptor = read_descriptor(path)
        self.assertIsNotNone(descriptor)
        self.assertEqual(descriptor["schemaVersion"], "workflow/sidecar-endpoint/v1")
        self.assertTrue(validate_descriptor(descriptor).valid)

    def test_read_missing_returns_none(self) -> None:
        self.assertIsNone(read_descriptor(Path(tempfile.mkdtemp()) / "missing.json"))

    def test_capability_probe(self) -> None:
        probe = capability_probe(make_descriptor())
        self.assertTrue(probe["installed"])
        self.assertIn("snapshot_v3", probe["capabilities"])
        none = capability_probe(None)
        self.assertFalse(none["installed"])
        self.assertEqual(none["capabilities"], [])


if __name__ == "__main__":
    unittest.main()
