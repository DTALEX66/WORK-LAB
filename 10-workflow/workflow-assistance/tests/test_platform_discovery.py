"""Contract tests for real platform discovery (WL3-100)."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

import platform_discovery as discovery


class PlatformDiscoveryTests(unittest.TestCase):
    def test_discover_all_returns_observations_without_exceptions(self) -> None:
        observations = discovery.discover_all()
        self.assertIsInstance(observations, list)
        self.assertTrue(observations)
        for observation in observations:
            self.assertIn("package_identity", observation)
            self.assertIn("effective_config_root", observation)
            self.assertNotIn("token", json_serialized(observation).lower())
            self.assertNotIn("secret", json_serialized(observation).lower())

    def test_resolve_current_platform_never_crashes_on_any_machine(self) -> None:
        resolved = discovery.resolve_current_platform()
        self.assertEqual(resolved["schema_version"], "workflow/platform-identity/v1")
        self.assertIn("discovery_source", resolved)
        self.assertIn("probed", resolved)
        for identity in resolved["identities"]:
            self.assertIn(identity["state"], discovery.identity.STATES)

    def test_missing_executable_yields_unavailable_without_crash(self) -> None:
        with patch("platform_discovery._which", return_value=None):
            resolved = discovery.resolve_current_platform()
            by_package = {i["package_identity"]: i for i in resolved["identities"]}
            for package in ("codex-cli", "hermes-agent"):
                self.assertIn(package, by_package)
                self.assertEqual(by_package[package]["source"], "missing")

    def test_sha256_digest_is_stable(self) -> None:
        path = Path(__file__)
        first = discovery._sha256_file(path)
        second = discovery._sha256_file(path)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


def json_serialized(observation: dict) -> str:
    import json

    return json.dumps(observation, ensure_ascii=False, default=str)


if __name__ == "__main__":
    unittest.main()
