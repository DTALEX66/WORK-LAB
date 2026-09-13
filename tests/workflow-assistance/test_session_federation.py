"""Tests for the session federation core (WL-P0-020/021/022/030/090).

Repo convention: modules under services/ are loaded by spec (no package
__init__), so these tests load each file via importlib and pre-register
the required module names in sys.modules.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services" / "session-federation"


def _load(name: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SERVICES / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class CanonicalSessionTests(unittest.TestCase):
    def test_roundtrip_and_digest_stability(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        session = canonical.CanonicalSession(
            universal_session_id="us-1",
            workspace_id="w",
            project_id="work-lab",
            source_agent="hermes",
            source_session_id="s-1",
            source_format="hermes-jsonl",
            native_path="C:/state/db",
            native_hash="abc",
            messages=({"role": "user", "text": "goal"}, {"role": "assistant", "text": "done"}),
            decisions=({"decision": "use v2", "why": "better"},),
            todos=({"text": "t", "state": "open"},),
            changed_files=("a.py",),
            portability_level=canonical.PortabilityLevel.L1_HANDOFF,
            metadata={"progress": "step 2/5"},
        )
        text = session.to_json()
        back = canonical.CanonicalSession.from_json(text)
        self.assertEqual(back, session)
        self.assertEqual(back.content_digest(), session.content_digest())
        self.assertEqual(back.to_dict()["schema_version"], canonical.SCHEMA_VERSION)

    def test_l3_requires_verified_native_resume(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        with self.assertRaisesRegex(ValueError, "L3"):
            canonical.CanonicalSession(
                universal_session_id="x",
                workspace_id="w",
                project_id="p",
                source_agent="a",
                source_session_id="s",
                source_format="f",
                portability_level=canonical.PortabilityLevel.L3_NATIVE_RESUME,
            )
        ok = canonical.CanonicalSession(
            universal_session_id="x",
            workspace_id="w",
            project_id="p",
            source_agent="a",
            source_session_id="s",
            source_format="f",
            portability_level=canonical.PortabilityLevel.L3_NATIVE_RESUME,
            metadata={"native_resume": {"verified": True}},
        )
        self.assertIs(ok.portability_level, canonical.PortabilityLevel.L3_NATIVE_RESUME)

    def test_unknown_event_type_rejected_fail_closed(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        self.assertEqual(canonical.canonical_event_type("tool_call"), canonical.EventType.TOOL_CALL)
        with self.assertRaises(ValueError):
            canonical.canonical_event_type("quantum_leap")

    def test_loss_report_bounds(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        report = canonical.LossReport(messages=0.5)
        self.assertEqual(report.messages, 0.5)
        with self.assertRaises(ValueError):
            canonical.LossReport(messages=1.5)

    def test_capsule_render_rejects_l0(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        l0 = canonical.CanonicalSession(
            universal_session_id="x",
            workspace_id="w",
            project_id="p",
            source_agent="a",
            source_session_id="s",
            source_format="f",
        )
        with self.assertRaises(ValueError):
            canonical.render_capsule(l0)


class ProviderHandoffTests(unittest.TestCase):
    def _provider(self):
        canonical = _load("canonical.py", "test_session_federation.canonical")
        provider = _load("provider.py", "test_session_federation.provider")

        class _P(provider.SessionProvider):  # type: ignore[misc]
            source_agent = "codex"

            def discover(self, project_id: str):
                return []

            def read(self, ref):
                raise NotImplementedError

            def health(self):
                return {"ok": True}

        return canonical, provider, _P()

    def test_handoff_writes_triple_with_honest_loss_report(self) -> None:
        canonical, provider, p = self._provider()
        session = canonical.CanonicalSession(
            universal_session_id="us-9",
            workspace_id="w",
            project_id="work-lab",
            source_agent="codex",
            source_session_id="c-9",
            source_format="codex-json",
            messages=({"role": "user", "text": "build it"},),
            todos=({"text": "wire tests", "state": "open"},),
            changed_files=("main.py",),
            portability_level=canonical.PortabilityLevel.L1_HANDOFF,
        )
        with tempfile.TemporaryDirectory() as td:
            result = p.handoff(session, td)
            for key in ("handoff", "capsule", "loss_report"):
                self.assertTrue(Path(result[key]).is_file(), key)
            doc = json.loads(Path(result["handoff"]).read_text(encoding="utf-8"))
            self.assertEqual(doc["schema"], "handoff-v1")
            self.assertEqual(doc["from_agent"], "codex")
            loss = json.loads(Path(result["loss_report"]).read_text(encoding="utf-8"))
            self.assertEqual(loss["native_state_available"], False)
            self.assertFalse(loss["system_prompt_transferred"])
            capsule = Path(result["capsule"]).read_text(encoding="utf-8")
            self.assertIn("Session Capsule", capsule)
            self.assertIn("wire tests", capsule)

    def test_export_import_roundtrip(self) -> None:
        canonical, provider, p = self._provider()
        session = canonical.CanonicalSession(
            universal_session_id="us-2",
            workspace_id="w",
            project_id="work-lab",
            source_agent="hermes",
            source_session_id="h-2",
            source_format="hermes-jsonl",
        )
        with tempfile.TemporaryDirectory() as td:
            out = p.export(session, td)
            self.assertTrue(Path(out["exported"]).is_file())
            back = json.loads(Path(out["exported"]).read_text(encoding="utf-8"))
            rehydrated = p.import_session(back, td)
            self.assertEqual(rehydrated.content_digest(), session.content_digest())
            self.assertEqual(rehydrated.universal_session_id, session.universal_session_id)
            self.assertEqual(rehydrated.source_agent, session.source_agent)
            self.assertEqual(rehydrated.to_dict(), session.to_dict())


class HermesProviderTests(unittest.TestCase):
    def test_discover_jsonl_and_read_normalizes_l1(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        provider_mod = _load("provider.py", "test_session_federation.provider")
        sys.modules["services_session_federation_provider"] = provider_mod
        spec = importlib.util.spec_from_file_location(
            "test_session_federation.hermes_provider", SERVICES / "hermes_provider.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / ".hermes"
            sessions = home / "sessions"
            sessions.mkdir(parents=True)
            transcript = sessions / "s-1.jsonl"
            transcript.write_text(
                json.dumps({"session_id": "s-1", "project": "work-lab", "workspace": "w", "type": "user_message", "text": "hi", "ts": "2026-09-01T00:00:00Z"}) + "\n"
                + json.dumps({"type": "assistant_message", "text": "ok", "ts": "2026-09-01T00:00:05Z"}) + "\n"
                + json.dumps({"type": "decision", "choice": "use v2", "reason": "better", "ts": "2026-09-01T00:00:09Z"}) + "\n",
                encoding="utf-8",
            )
            p = module.HermesSessionProvider(home=str(home))
            refs = list(p.discover("work-lab"))
            self.assertEqual(len(refs), 1)
            ref = refs[0]
            self.assertEqual(ref.source_session_id, "s-1")
            self.assertEqual(ref.project_id, "work-lab")
            loaded = p.read(ref)
            self.assertEqual(len(loaded.messages), 2)
            self.assertEqual(loaded.portability_level, canonical.PortabilityLevel.L1_HANDOFF)
            self.assertEqual(loaded.decisions[0]["decision"], "use v2")
            health = p.health()
            # sessions dir exists → provider is reachable; state.db absence is noted
            self.assertTrue(health["ok"])
            self.assertIn("state.db missing", health["notes"])
            self.assertEqual(p.resume_native(loaded), "hermes --resume s-1")

    def test_discover_missing_store_is_soft_empty(self) -> None:
        _load("canonical.py", "test_session_federation.canonical")
        provider_mod = _load("provider.py", "test_session_federation.provider")
        sys.modules["services_session_federation_provider"] = provider_mod
        spec = importlib.util.spec_from_file_location(
            "test_session_federation.hermes_provider2", SERVICES / "hermes_provider.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as td:
            p = module.HermesSessionProvider(home=str(Path(td) / "absent-home"))
            self.assertEqual(list(p.discover("anything")), [])
            self.assertFalse(p.health()["ok"])


class SessionIndexTests(unittest.TestCase):
    """WL-P0-050 unified session history index."""

    def _index(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "test_session_federation.index", SERVICES / "index.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_index_and_search_roundtrip(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        index_mod = self._index()
        with tempfile.TemporaryDirectory() as td:
            idx = index_mod.SessionIndex(Path(td) / "index.sqlite")
            s1 = canonical.CanonicalSession(
                universal_session_id="us-1",
                workspace_id="w",
                project_id="work-lab",
                source_agent="hermes",
                source_session_id="h-1",
                source_format="hermes-jsonl",
                messages=({"role": "user", "text": "build the pipeline"},),
                decisions=({"decision": "use SQLite", "why": "portable"},),
                todos=({"text": "add tests", "state": "open"},),
                changed_files=("pipeline.py",),
                metadata={"model": "agnes"},
                started_at="2026-09-01T00:00:00Z",
                portability_level=canonical.PortabilityLevel.L1_HANDOFF,
            )
            s2 = canonical.CanonicalSession(
                universal_session_id="us-2",
                workspace_id="w",
                project_id="work-lab",
                source_agent="codex",
                source_session_id="c-1",
                source_format="codex-json",
                changed_files=("pipeline.py", "tests.py"),
                metadata={"model": "gpt"},
                started_at="2026-09-02T00:00:00Z",
                portability_level=canonical.PortabilityLevel.L1_HANDOFF,
            )
            self.assertEqual(idx.index_session(s1)["status"], "INDEXED")
            self.assertEqual(idx.index_session(s2)["status"], "INDEXED")

            # FTS search
            results = idx.search("pipeline")
            self.assertGreaterEqual(len(results), 2)
            self.assertTrue(all("pipeline" in r["changed_files"] or "pipeline" in r["semantic_summary"] for r in results))

            # structured filter by agent
            hermes_only = idx.list_sessions(agent="hermes")
            self.assertEqual(len(hermes_only), 1)
            self.assertEqual(hermes_only[0]["universal_session_id"], "us-1")

            # date + model filter
            model_hit = idx.list_sessions(model="agnes")
            self.assertEqual(len(model_hit), 1)
            self.assertEqual(model_hit[0]["source_agent"], "hermes")
            ranged = idx.list_sessions(since="2026-09-02T00:00:00Z", until="2026-09-02T23:59:59Z")
            self.assertEqual(len(ranged), 1)
            self.assertEqual(ranged[0]["universal_session_id"], "us-2")

            # idempotent re-index
            before = idx.health()["sessions"]
            idx.index_session(s1)
            self.assertEqual(idx.health()["sessions"], before)

            # health
            health = idx.health()
            self.assertTrue(health["ok"])
            self.assertEqual(health["sessions"], 2)
            self.assertEqual(health["schema_version"], index_mod.INDEX_SCHEMA_VERSION)
            idx.close()

    def test_decision_and_error_keyword_search(self) -> None:
        canonical = _load("canonical.py", "test_session_federation.canonical")
        index_mod = self._index()
        with tempfile.TemporaryDirectory() as td:
            idx = index_mod.SessionIndex(Path(td) / "index.sqlite")
            s = canonical.CanonicalSession(
                universal_session_id="us-3",
                workspace_id="w",
                project_id="work-lab",
                source_agent="dsh",
                source_session_id="d-1",
                source_format="dsh-jsonl",
                decisions=({"decision": "rollback migration", "why": "CI failed"},),
                events=({"type": "error", "text": "schema drift"},),
                portability_level=canonical.PortabilityLevel.L1_HANDOFF,
            )
            idx.index_session(s)
            hits = idx.search("rollback")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["source_agent"], "dsh")
            # decision keyword shows up in semantic summary
            self.assertIn("rollback migration", hits[0]["semantic_summary"])
            idx.close()


if __name__ == "__main__":
    unittest.main()
