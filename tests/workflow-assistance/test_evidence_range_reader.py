"""Gate: a large evidence artifact can be cited by an exact byte interval (REQ-RANGE).

The chain already had per-artifact sha256 and a cost budget, but reading was all-or-nothing: the only
"slice" in the code was a prefix truncate, which cannot say where it stopped, whether more exists, or
whether the shown bytes still belong to the recorded digest.

This gate proves the four properties that make an interval citable, and refuses the four ways a range
reader can quietly become a full-file reader or a silent-truncator:

* adjacent intervals concatenate to exactly the whole file (offset arithmetic is right or the citation is
  wrong);
* the reader never computes the whole-file digest itself — asking for identity verification without
  supplying the recorded digest is REFUSED, which is what keeps a range read from secretly reading
  everything;
* a mismatched digest returns NO content;
* over-limit, non-positive, past-end, outside-boundary and unreadable handles are each their own typed
  answer, never an empty success.

Cost is measured against a real project-local log rather than asserted. All fixtures are created inside
`.project-local/runs` and released by the bounded fixture helper.
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "client-neutral-core" / "scripts"))

import evidence_range_reader as err  # noqa: E402
from project_temp import fixture_dir  # noqa: E402

LARGE_BYTES = 8 * 1024 * 1024
# A path one level above the repository that no test creates. The reader decides the boundary
# before opening anything, so an uncreated name is enough to prove it will not be followed.
OUTSIDE_PROBE = ROOT.parent / "work-lab-range-boundary-probe.log"


class IntervalArithmeticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = fixture_dir(prefix="range-reader-")
        self.text = "".join(f"line-{index:05d} payload\n" for index in range(400))
        self.path = self.dir / "artifact.log"
        self.path.write_text(self.text, encoding="utf-8")
        self.raw = self.path.read_bytes()
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def read(self, offset: int, limit: int, **over):
        return err.read_range(handle=str(self.path), root=ROOT, offset=offset, limit=limit, **over)

    def test_an_interval_returns_exactly_its_bytes(self) -> None:
        result = self.read(10, 20)
        self.assertEqual(result["status"], err.STATUS_OK)
        self.assertEqual(result["content"].encode("utf-8"), self.raw[10:30])
        self.assertEqual(result["offset"], 10)
        self.assertEqual(result["endOffset"], 30)
        self.assertFalse(result["eofReached"])
        self.assertEqual(result["sliceDigest"], hashlib.sha256(self.raw[10:30]).hexdigest())

    def test_adjacent_intervals_concatenate_to_the_whole_file(self) -> None:
        """If the offset math is off by one anywhere, this fails — that is the citation guarantee."""
        size = len(self.raw)
        pieces = []
        offset = 0
        while offset < size:
            result = self.read(offset, 997)
            self.assertEqual(result["status"], err.STATUS_OK)
            pieces.append(result["content"].encode("utf-8"))
            self.assertEqual(result["endOffset"], offset + len(pieces[-1]))
            offset = result["endOffset"]
        self.assertEqual(b"".join(pieces), self.raw)
        self.assertEqual(offset, size)

    def test_the_last_interval_reports_eof_and_stops(self) -> None:
        tail = self.read(len(self.raw) - 16, 4096)
        self.assertTrue(tail["eofReached"])
        self.assertEqual(tail["content"].encode("utf-8"), self.raw[-16:])
        self.assertEqual(tail["bytesRequested"], 16)

    def test_reading_the_same_interval_twice_is_stable(self) -> None:
        self.assertEqual(self.read(33, 64)["sliceDigest"], self.read(33, 64)["sliceDigest"])

    def test_cost_is_reported_against_the_file_size(self) -> None:
        result = self.read(0, 64)
        self.assertEqual(result["cost"]["bytesRead"], 64)
        self.assertEqual(result["cost"]["fileSize"], len(self.raw))
        self.assertFalse(result["cost"]["wholeFileWasRead"])


class IdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = fixture_dir(prefix="range-identity-")
        self.path = self.dir / "artifact.bin"
        self.path.write_bytes(b"abcdefgh" * 8)
        self.raw = self.path.read_bytes()
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def read(self, **over):
        kwargs = {"handle": str(self.path), "root": ROOT, "offset": 0, "limit": 16}
        kwargs.update(over)
        return err.read_range(**kwargs)

    def test_a_matching_digest_is_carried_into_the_result(self) -> None:
        result = self.read(expected_digest=self.digest, whole_digest=self.digest)
        self.assertEqual(result["status"], err.STATUS_OK)
        self.assertEqual(result["identity"]["wholeDigest"], self.digest)
        self.assertEqual(result["identity"]["digestSource"], "caller-supplied")

    def test_a_mismatched_digest_returns_no_content(self) -> None:
        result = self.read(expected_digest="f" * 64, whole_digest=self.digest)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], "DIGEST_MISMATCH")
        self.assertIsNone(result["content"])

    def test_verification_without_a_digest_to_compare_is_refused_not_computed(self) -> None:
        """The proof that a range read never secretly becomes a whole-file hash."""
        result = self.read(expected_digest=self.digest)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], "DIGEST_UNAVAILABLE")
        self.assertIsNone(result["content"])

    def test_a_malformed_digest_shape_is_refused(self) -> None:
        for bad in ("abc", "z" * 64, "!" * 64):
            with self.subTest(digest=bad):
                result = self.read(expected_digest=bad)
                self.assertEqual(result["reason_code"], "DIGEST_SHAPE")


class RefusalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = fixture_dir(prefix="range-refusal-")
        self.path = self.dir / "small.log"
        self.path.write_text("x" * 100, encoding="utf-8")

    def read(self, **over):
        kwargs = {"handle": str(self.path), "root": ROOT, "offset": 0, "limit": 10}
        kwargs.update(over)
        return err.read_range(**kwargs)

    def test_every_refusal_is_typed_and_carries_no_content(self) -> None:
        cases = [
            ({}, "HANDLE_REQUIRED", {"handle": "  "}),
            ({}, "ABSOLUTE_PATH_REQUIRED", {"handle": "relative/file.log"}),
            ({}, "OUT_OF_BOUNDARY", {"handle": str(OUTSIDE_PROBE)}),
            ({}, "OUT_OF_EVIDENCE_SURFACE", {"handle": str(ROOT)}),
            ({}, "NOT_A_FILE", {"handle": str(self.dir)}),
            ({}, "NOT_A_FILE", {"handle": str(self.dir / "never-created.log")}),
            ({}, "LIMIT_TOO_LARGE", {"limit": err.MAX_LIMIT + 1}),
            ({}, "OFFSET_PAST_END", {"offset": 500}),
            ({}, "OFFSET_NEGATIVE", {"offset": -1}),
            ({}, "LIMIT_NON_POSITIVE", {"limit": 0}),
        ]
        for _ctx, code, over in cases:
            with self.subTest(code=code):
                result = self.read(**{"handle": over.get("handle", str(self.path)),
                                      "offset": over.get("offset", 0),
                                      "limit": over.get("limit", 10)})
                self.assertIn(result["status"], ("REFUSED", err.STATUS_OUT_OF_RANGE))
                self.assertEqual(result["reason_code"], code)
                self.assertIsNone(result["content"])
                self.assertTrue(result["reason"].strip())

    def test_an_out_of_boundary_handle_is_named_not_followed(self) -> None:
        """The refusal must not depend on the file existing: boundary is decided before any open().

        tempfile.gettempdir() is NOT a valid outside probe — under the canonical gate runner the whole
        project binds TMP/TEMP/TMPDIR into `.project-local/runs/tmp`, i.e. inside the repository, and
        that is exactly how this test first passed locally and failed in the batch.
        """
        self.assertFalse(OUTSIDE_PROBE.exists(), "the probe must stay uncreated")
        result = self.read(handle=str(OUTSIDE_PROBE))
        self.assertEqual(result["reason_code"], "OUT_OF_BOUNDARY")
        self.assertIsNone(result["content"])
        self.assertFalse(OUTSIDE_PROBE.exists(), "the reader created the file it was refusing to read")

    def test_a_directory_handle_is_refused_as_not_a_file(self) -> None:
        self.assertEqual(self.read(handle=str(self.dir))["reason_code"], "NOT_A_FILE")

    def test_the_repository_root_is_not_an_evidence_surface(self) -> None:
        """Inside the Git root is a spill rule, not a reading licence.

        The first version of this reader stopped at `is_relative_to(root)` and therefore served any file in
        the repository over HTTP: `.hermes/task-runtime/**/canonical.sqlite` (a task/session database), a
        restored `hermes/config.yaml` backup, and anything named `.env*` all sat inside that boundary and
        answered READ_OK. The reviewer reproduced all three.
        """
        result = self.read(handle=str(ROOT))
        self.assertEqual(result["reason_code"], "OUT_OF_EVIDENCE_SURFACE")
        self.assertIsNone(result["content"])


class EvidenceSurfaceTests(unittest.TestCase):
    """Staying inside the project is necessary and not sufficient — the surface and the name both decide."""

    def setUp(self) -> None:
        self.dir = fixture_dir(prefix="range-surface-")
        self.path = self.dir / "run.log"
        self.path.write_text("evidence bytes", encoding="utf-8")

    def read(self, handle: str, **over):
        return err.read_range(handle=handle, root=ROOT, offset=0, limit=64, **over)

    def test_a_file_on_a_declared_evidence_surface_reads(self) -> None:
        self.assertEqual(self.read(str(self.path))["reason_code"], "READ_OK")

    def test_source_inside_the_repository_is_not_evidence(self) -> None:
        for probe in (ROOT / "services" / "orchestration" / "sidecar.py",
                      ROOT / ".project" / "governance" / "project-authority-index.json",
                      ROOT / "config" / "config-ownership.json"):
            with self.subTest(probe=str(probe)):
                result = self.read(str(probe))
                self.assertEqual(result["reason_code"], "OUT_OF_EVIDENCE_SURFACE")
                self.assertIsNone(result["content"])

    def test_credential_shaped_names_are_refused_even_under_an_evidence_root(self) -> None:
        # The refusal is decided from the path alone, so these names stay uncreated: no test may plant a
        # .env or a session database in the project just to prove it will not be read.
        for name in (".env", "hermes-config.yaml", "canonical.sqlite", "id_rsa",
                     "cookies.sqlite", "browser_data.session", "server.pem"):
            with self.subTest(name=name):
                probe = self.dir / "never-created" / name
                self.assertFalse(probe.exists())
                result = self.read(str(probe))
                self.assertEqual(result["reason_code"], "SENSITIVE_NAME", result["reason"])
                self.assertIsNone(result["content"])

    def test_a_narrowed_surface_refuses_a_file_that_the_default_surface_allows(self) -> None:
        """An unset surface must fail closed, not fall back to the whole repository."""
        self.assertEqual(self.read(str(self.path), evidence_roots=())["reason_code"],
                         "OUT_OF_EVIDENCE_SURFACE")
        self.assertEqual(self.read(str(self.path), evidence_roots=(".project-local/artifacts",))["reason_code"],
                         "OUT_OF_EVIDENCE_SURFACE")
        self.assertEqual(self.read(str(self.path))["reason_code"], "READ_OK")

    def test_the_declared_roots_come_from_the_boundary_authority(self) -> None:
        declared = err.declared_evidence_roots(ROOT)
        self.assertIn(".project-local/artifacts", declared)
        self.assertIn(".project-local/runs", declared)
        # A machine without the declaration falls back to the narrow default, never to "everything".
        self.assertEqual(err.declared_evidence_roots(ROOT / "no-such-place"), err.DEFAULT_EVIDENCE_ROOTS)


class LargeArtifactCostTests(unittest.TestCase):
    """The trigger the register row names: a real large log where whole reads are measurably costly."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.dir = fixture_dir(prefix="range-large-")
        cls.path = cls.dir / "big-gate.log"
        line = b"[00:00:00] INFO worker tick heartbeat\n"
        with cls.path.open("wb") as handle:
            written = 0
            while written < LARGE_BYTES:
                handle.write(line)
                written += len(line)
        cls.size = cls.path.stat().st_size

    def test_an_middle_slice_reads_a_fraction_and_reports_the_ratio(self) -> None:
        middle = self.size // 2
        started = time.perf_counter()
        result = err.read_range(handle=str(self.path), root=ROOT, offset=middle, limit=4096)
        elapsed = time.perf_counter() - started
        self.assertEqual(result["status"], err.STATUS_OK)
        self.assertEqual(result["cost"]["bytesRead"], 4096)
        self.assertEqual(result["cost"]["fileSize"], self.size)
        self.assertLess(result["cost"]["bytesRead"] / self.size, 0.001)
        self.assertFalse(result["cost"]["wholeFileWasRead"])
        self.assertLess(elapsed, 1.0, f"a 4 KiB slice of {self.size} bytes took {elapsed:.3f}s")

    def test_a_whole_read_is_offered_as_the_comparison_not_assumed(self) -> None:
        """Measured against the same file, so the cost claim is a number, not a word."""
        whole_started = time.perf_counter()
        self.path.read_bytes()
        whole_elapsed = time.perf_counter() - whole_started
        slice_started = time.perf_counter()
        err.read_range(handle=str(self.path), root=ROOT, offset=self.size // 2, limit=4096)
        slice_elapsed = time.perf_counter() - slice_started
        self.assertLess(slice_elapsed, whole_elapsed,
                        f"slice {slice_elapsed:.6f}s was not cheaper than whole {whole_elapsed:.6f}s")
        print(f"\nREQ_RANGE_COST size={self.size} whole_s={whole_elapsed:.4f} "
              f"slice_s={slice_elapsed:.6f} ratio={4096 / self.size:.6f}")


class SidecarRouteTests(unittest.TestCase):
    """The capability has to be reachable where a reader actually is: the read-only sidecar route."""

    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(ROOT / "services" / "orchestration"))
        import sidecar as sidecar_module
        cls.runtime = fixture_dir(prefix="range-route-")
        cls.instance = sidecar_module.WorkflowSidecar(ROOT, cls.runtime)
        cls.server = sidecar_module.create_server(cls.instance, "127.0.0.1", 0, live_updates=False)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.instance.close()

    def get(self, query: str):
        with urllib.request.urlopen(f"{self.base}/api/v1/evidence-range{query}", timeout=8) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_the_route_returns_an_exact_interval_of_a_project_artifact(self) -> None:
        artifact = self.runtime / "route-artifact.log"
        artifact.write_bytes(b"0123456789" * 40)
        status, result = self.get(f"?handle={urllib.parse.quote(str(artifact))}&offset=15&limit=10")
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], err.STATUS_OK)
        self.assertEqual(result["content"], "5678901234")
        self.assertEqual(result["cost"]["bytesRead"], 10)
        self.assertEqual(result["cost"]["fileSize"], 400)

    def test_the_route_refuses_a_handle_outside_the_project(self) -> None:
        _status, result = self.get(f"?handle={urllib.parse.quote(str(OUTSIDE_PROBE))}")
        self.assertEqual(result["reason_code"], "OUT_OF_BOUNDARY")
        self.assertIsNone(result["content"])

    def test_verification_without_a_digest_is_refused_over_http_too(self) -> None:
        artifact = self.runtime / "route-digest.log"
        artifact.write_bytes(b"abc" * 50)
        _status, result = self.get(f"?handle={urllib.parse.quote(str(artifact))}"
                                   f"&expectedDigest={'1' * 64}")
        self.assertEqual(result["reason_code"], "DIGEST_UNAVAILABLE")

    def test_a_non_numeric_query_is_400_not_a_silent_default(self) -> None:
        try:
            self.get("?handle=anything&offset=abc")
            self.fail("a malformed offset was accepted")
        except urllib.error.HTTPError as error:
            self.assertEqual(error.code, 400)
            body = json.loads(error.read().decode("utf-8"))
            self.assertEqual(body["reason_code"], "BAD_QUERY")

    def test_the_route_is_read_only(self) -> None:
        request = urllib.request.Request(f"{self.base}/api/v1/evidence-range", data=b"{}", method="POST")
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                code = response.status
        except urllib.error.HTTPError as error:
            code = error.code
        self.assertEqual(code, 405, "the Observer grew a write method on its read route")


if __name__ == "__main__":
    unittest.main(verbosity=2)
