from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/workflow/user_profile_export.py"
spec = importlib.util.spec_from_file_location("user_profile_export", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class UserProfileExportTests(unittest.TestCase):
    def test_redact_walk_redacts_secret_keys_and_values(self) -> None:
        data = {
            "display": {"theme": "dark", "skin": "default"},
            "model": {"provider": "deepseek", "model": "deepseek-v4-flash"},
            "api_key": "sk-real-value-1234567890",
            "providers": {"p": {"token": "abcdefghijklmnop"}},
            "description": "contains sk-abcdefghijklmnop literal",
        }
        out = module._redact_walk(data)
        self.assertEqual(out["display"]["theme"], "dark")
        self.assertEqual(out["model"]["provider"], "deepseek")
        self.assertEqual(out["api_key"], module.REDACTED)
        self.assertEqual(out["providers"]["p"]["token"], module.REDACTED)
        self.assertEqual(out["description"], module.REDACTED)

    def test_env_key_names_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            p = Path(raw) / ".env"
            p.write_text("OPENAI_API_KEY=sk-secret-value-abcdefghij\nDEEPSEEK_API_KEY=sk-other-value\n# comment\nEMPTY=\n", encoding="utf-8")
            names = module._env_key_names(p)
            self.assertEqual(names, ["DEEPSEEK_API_KEY", "EMPTY", "OPENAI_API_KEY"])
            self.assertTrue(all("=" not in n for n in names))

    def test_toml_redaction_keeps_provider_model_redacts_credentials(self) -> None:
        data = {
            "model_provider": "cc-switch-official",
            "model": "gpt-5.6-luna",
            "base_url": "https://user:pass@example.invalid/v1",
            "mcp_servers": {"custom": {"command": "safe-placeholder", "api_key": "xyz123"}},
        }
        out = module._redact_toml_keys(data)
        self.assertEqual(out["model_provider"], "cc-switch-official")
        self.assertEqual(out["model"], "gpt-5.6-luna")
        self.assertEqual(out["base_url"], module.REDACTED)
        self.assertEqual(out["mcp_servers"]["custom"]["api_key"], module.REDACTED)
        self.assertEqual(out["mcp_servers"]["custom"]["command"], "safe-placeholder")

    def test_skills_inventory_reads_description(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            d = root / "my-skill"
            d.mkdir()
            (d / "SKILL.md").write_text(
                "---\nname: my-skill\ndescription: 'Use for testing only.'\n---\n\n# body\n", encoding="utf-8"
            )
            inv = module._inventory_skills(root)
            self.assertEqual(len(inv), 1)
            self.assertEqual(inv[0]["name"], "my-skill")
            self.assertEqual(inv[0]["description"], "Use for testing only.")

    def test_profile_output_is_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            home = base / "hermes"
            codex = base / "codex"
            agents = base / "agents"
            (home / "skills").mkdir(parents=True)
            (codex / "rules").mkdir(parents=True)
            (agents / "skills").mkdir(parents=True)
            (home / "config.yaml").write_text(
                "display:\n  theme: dark\nmodel:\n  provider: deepseek\napi_key: sk-literal-abcdefghijklmnop\n",
                encoding="utf-8",
            )
            (home / ".env").write_text("OPENAI_API_KEY=sk-abcdefghijklmnop\n", encoding="utf-8")
            (codex / "config.toml").write_text(
                'model_provider = "cc-switch-official"\nbase_url = "https://u:p@example.invalid"\n', encoding="utf-8"
            )
            (codex / "rules" / "a.rules").write_text("# rule\n", encoding="utf-8")
            (home / "skills" / "s1").mkdir(parents=True)
            (home / "skills" / "s1" / "SKILL.md").write_text("---\nname: s1\ndescription: 'D.'\n---\n", encoding="utf-8")

            profile = module._profile(home, codex, agents)
            payload = json.dumps(profile, ensure_ascii=False)
            self.assertNotIn("sk-literal", payload)
            self.assertNotIn("sk-abcdefghijklmnop", payload)
            self.assertNotIn("user:pass", payload)
            self.assertIn("deepseek", payload)  # provider name kept
            self.assertIn("cc-switch-official", payload)
            self.assertEqual(len(profile["hermes"]["skills"]), 1)


if __name__ == "__main__":
    unittest.main()
