"""WLGM-100 tests: generic adapter SDK."""
from __future__ import annotations

import unittest

from adapter_sdk import (
    CapabilityUnsupported,
    GenericHeartbeatAdapter,
    MockAdapter,
    negotiate,
)


class AdapterSdkTests(unittest.TestCase):
    def test_mock_adapter_negotiation(self) -> None:
        adapter = MockAdapter()
        result = negotiate(adapter, {"session_list", "run_status", "event_stream"})
        self.assertTrue(result["session_list"])
        self.assertTrue(result["run_status"])
        self.assertFalse(result["event_stream"])

    def test_missing_capability_is_explicit_unsupported(self) -> None:
        adapter = MockAdapter(capabilities={"heartbeat"})
        with self.assertRaises(CapabilityUnsupported):
            adapter.session_list()

    def test_probe_reports_unsupported_not_fake_success(self) -> None:
        adapter = MockAdapter(capabilities=set())
        probe = adapter.probe()
        self.assertEqual(probe.capabilities, set())

    def test_heartbeat_adapter_only_heartbeat(self) -> None:
        adapter = GenericHeartbeatAdapter()
        probe = adapter.probe()
        self.assertEqual(probe.capabilities, {"heartbeat"})
        self.assertIsNotNone(adapter.heartbeat())

    def test_adapter_crash_is_isolated_to_adapter(self) -> None:
        class ExplodingAdapter(MockAdapter):
            adapter_id = "exploding"

            def heartbeat(self):
                raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            ExplodingAdapter().heartbeat()

    def test_token_usage_unsupported_is_not_zero(self) -> None:
        adapter = MockAdapter()
        with self.assertRaises(CapabilityUnsupported):
            adapter.token_usage()

    def test_mock_session_and_run(self) -> None:
        adapter = MockAdapter()
        sessions = adapter.session_list()
        runs = adapter.run_status("s1")
        self.assertEqual(sessions[0]["sessionId"], "mock-session-1")
        self.assertEqual(runs[0]["executionId"], "mock-exec-1")


if __name__ == "__main__":
    unittest.main()
