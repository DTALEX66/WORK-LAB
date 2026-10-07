"""Gate: the Control Surface service is the only write boundary, and it answers honestly.

P1-06 / AG-15 / T04. What this pins, in the order the product can be lied about:

1. a request that does not fit the contract is REFUSED before anything runs;
2. an operation with no native capability answers NOT_IMPLEMENTED with its own reason and an EMPTY
   receipt — it cannot return a success shape, and evidence_level cannot be raised by the caller;
3. a real write goes through the existing permission gate, into the ONE canonical store the Observer
   also reads, and is then re-read: a handler return is not a verified write;
4. idempotent replay returns the same record instead of a second one, and a foreign idempotency key on
   an existing task_id is refused rather than overwriting someone else's work unit;
5. a boundary outside this repository — including E:/F: — is refused by name;
6. every result validates against ``control-operation-result.schema.json``, so the two languages cannot
   drift into two different stories;
7. the transport is loopback-only, and the write method set is exactly POST /api/control/operations.

Discovered dynamically by ``run_quality_gate.py governance``.
"""
from __future__ import annotations

import json
import re
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "services" / "control", ROOT / "services" / "orchestration",
              ROOT / "services" / "task-governance", ROOT / "packages" / "client-neutral-core" / "scripts"):
    sys.path.insert(0, str(entry))

import jsonschema  # noqa: E402
import control_service  # noqa: E402
from project_temp import fixture_dir  # noqa: E402
from snapshot_api import project_task_record  # noqa: E402

RESULT_SCHEMA = json.loads((ROOT / "packages/contracts/schemas/workflow/"
                            "control-operation-result.schema.json").read_text(encoding="utf-8"))
RESULT_VALIDATOR = jsonschema.Draft202012Validator(RESULT_SCHEMA, format_checker=jsonschema.FormatChecker())


def request_payload(**over):
    payload = {
        "schema_version": "worklab/control-operation/v1",
        "operation": "work-unit.create",
        "project_id": "work-lab",
        "task_id": "WL-CONTROL-1",
        "revision": None,
        "attempt": None,
        "scope": {"boundaries": ["D:/All projects/WORK-LAB"], "granted_by": "owner 2026-10-08 授权批次 C"},
        "expected_version": None,
        "idempotency_key": "idem-control-0001",
        "actor": "qoder-session",
        "requested_at": "2026-10-08T00:00:00Z",
        "payload": {"goal": "把 Control 首条写链接到 Observer 读回"},
    }
    payload.update(over)
    return payload


class ControlPlaneTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = fixture_dir(prefix="control-plane-")
        self.plane = control_service.build_plane(self.runtime, ROOT)

    def tearDown(self) -> None:
        self.plane.store.close()

    def assert_result_shape(self, result: dict) -> None:
        errors = list(RESULT_VALIDATOR.iter_errors(result))
        self.assertEqual(errors, [], json.dumps({"errors": [e.message for e in errors],
                                                 "result": result}, ensure_ascii=False)[:900])

    # -- 1 contract first ---------------------------------------------------
    def test_a_request_that_does_not_fit_the_contract_never_runs(self) -> None:
        missing_key = request_payload()
        del missing_key["idempotency_key"]
        result = self.plane.execute(missing_key)
        self.assert_result_shape(result)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], "INVALID_REQUEST")
        self.assertIn("idempotency_key", result["reason"])
        self.assertEqual(self.plane.store.list_tasks(), [], "an unauthorised request produced a row")

    def test_an_unknown_verb_is_refused_not_invented(self) -> None:
        result = self.plane.execute(request_payload(operation="work-unit.teleport"))
        self.assert_result_shape(result)
        self.assertNotEqual(result["status"], "ACCEPTED")
        self.assertIn(result["status"], ("REFUSED", "NOT_IMPLEMENTED"))

    def test_extra_properties_are_not_silently_accepted(self) -> None:
        smuggled = request_payload()
        smuggled["as_root"] = True
        result = self.plane.execute(smuggled)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], "INVALID_REQUEST")

    # -- 2 NOT_IMPLEMENTED is a real answer ---------------------------------
    def test_operations_without_a_native_capability_refuse_success(self) -> None:
        for operation in ("work-unit.dispatch", "approval.decide", "execution.cancel",
                          "config.apply", "config.rollback", "work-unit.revise", "execution.resume",
                          "execution.retry", "config.readback", "config.discover"):
            with self.subTest(operation=operation):
                result = self.plane.execute(request_payload(operation=operation,
                                                            task_id="WL-CONTROL-1"))
                self.assert_result_shape(result)
                self.assertEqual(result["status"], "NOT_IMPLEMENTED")
                self.assertIsNone(result["receipt"], "an unimplemented operation returned a receipt")
                self.assertTrue(result["reason"].strip())
                self.assertTrue(result["next_action"])
        self.assertEqual(self.plane.store.list_tasks(), [], "a refused operation wrote state")

    # -- 3 the real write chain --------------------------------------------
    def test_create_writes_then_rereads_and_is_visible_to_the_observer_projection(self) -> None:
        result = self.plane.execute(request_payload())
        self.assert_result_shape(result)
        self.assertEqual(result["status"], "ACCEPTED", result["reason"])
        self.assertEqual(result["evidence_level"], "SYNTHETIC",
                         "an in-repo fixture store may not claim more than SYNTHETIC")
        self.assertEqual(result["readback"]["status"], "QUEUED")
        self.assertEqual(len(result["receipt"]["digest"]), 64)

        rows = self.plane.store.list_tasks()
        self.assertEqual([row["task_id"] for row in rows], ["WL-CONTROL-1"])
        projected = project_task_record(rows[0])
        self.assertEqual(projected, {k: v for k, v in result["readback"].items() if k != "replayed"})

    def test_the_goal_text_stays_in_the_store_and_out_of_the_projection(self) -> None:
        goal = "读取我的私人会话并总结"
        result = self.plane.execute(request_payload(payload={"goal": goal}))
        self.assertEqual(result["status"], "ACCEPTED")
        serialised = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(goal, serialised, "a control result leaked the goal into the read side")
        stored = self.plane.store.list_tasks()[0]
        self.assertEqual(stored["checkpoint"]["goal"], goal, "the store is the right place for the goal")

    def test_a_missing_goal_is_refused_instead_of_creating_an_empty_unit(self) -> None:
        result = self.plane.execute(request_payload(payload={"goal": "   "}))
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], "GOAL_REQUIRED")

    def test_a_write_that_cannot_be_read_back_is_not_reported_as_success(self) -> None:
        """Fail-closed proof: if the readback disappears, the answer is READBACK_MISMATCH."""
        original = self.plane.store.list_tasks

        def lying_store(*args, **kwargs):
            rows = original(*args, **kwargs)
            return [] if rows else rows

        self.plane.store.list_tasks = lying_store
        try:
            result = self.plane.execute(request_payload())
        finally:
            self.plane.store.list_tasks = original
        self.assert_result_shape(result)
        self.assertEqual(result["status"], "READBACK_MISMATCH")

    # -- 4 idempotency ------------------------------------------------------
    def test_replaying_the_same_key_returns_the_same_record(self) -> None:
        first = self.plane.execute(request_payload())
        again = self.plane.execute(request_payload())
        self.assertEqual(first["status"], "ACCEPTED")
        self.assertEqual(again["readback"]["replayed"], True)
        self.assertEqual(again["receipt"]["kind"], "REPLAY")
        self.assertEqual(len(self.plane.store.list_tasks()), 1)

    def test_a_foreign_idempotency_key_on_an_existing_task_is_refused(self) -> None:
        self.plane.execute(request_payload())
        hijack = self.plane.execute(request_payload(idempotency_key="idem-other-owner-2",
                                                   payload={"goal": "改掉别人的工作单元"}))
        self.assertEqual(hijack["status"], "REFUSED")
        self.assertEqual(hijack["reason_code"], "IDEMPOTENCY_CONFLICT")
        stored = self.plane.store.list_tasks()[0]
        self.assertEqual(stored["checkpoint"]["idempotency_key"], "idem-control-0001",
                         "a refused replay overwrote the original identity")

    # -- 5 boundaries -------------------------------------------------------
    def test_protected_and_outside_boundaries_are_refused_by_name(self) -> None:
        for boundary, code in (("E:/somewhere", "FORBIDDEN_ROOT"),
                              ("F:/somewhere", "FORBIDDEN_ROOT"),
                              ("D:/All projects/OTHER-PROJECT", "OUT_OF_PROJECT_SCOPE"),
                              (" ", "EMPTY_BOUNDARY")):
            with self.subTest(boundary=boundary):
                result = self.plane.execute(request_payload(scope={"boundaries": [boundary],
                                                                  "granted_by": "owner"}))
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["reason_code"], code)
        self.assertEqual(self.plane.store.list_tasks(), [])

    def test_a_relative_boundary_stays_allowed_and_is_recorded(self) -> None:
        result = self.plane.execute(request_payload(scope={"boundaries": ["services/control"],
                                                          "granted_by": "owner"}))
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertEqual(self.plane.store.list_tasks()[0]["checkpoint"]["boundaries"], ["services/control"])

    # -- 6 the plan-only config path ---------------------------------------
    def test_config_diff_returns_a_plan_and_says_it_did_not_write(self) -> None:
        result = self.plane.execute(request_payload(
            operation="config.diff",
            payload={"target_file": "services/control/control_service.py", "field": "SCHEMA_VERSION",
                     "value": "worklab/control-service/v2"},
        ))
        self.assert_result_shape(result)
        self.assertEqual(result["status"], "PLANNED", result["reason"])
        self.assertIsNone(result["receipt"], "a plan is not a receipt")
        self.assertTrue(result["readback"]["plan_only"])
        self.assertIs(result["readback"]["written"], False)
        # the field exists in that file, so the plan must say present_before — proof it read the real target
        change = result["readback"]["changes"][0]
        self.assertTrue(change["present_before"], result["readback"]["target"])
        self.assertEqual(result["readback"]["target"], "services/control/control_service.py")

    def test_config_diff_refuses_a_target_outside_the_repository(self) -> None:
        result = self.plane.execute(request_payload(
            operation="config.diff", payload={"target_file": "C:/Users/anyone/config.yaml", "field": "a"},
        ))
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], "TARGET_OUT_OF_PROJECT")

    def test_receipts_are_tracked_in_the_runtime_root(self) -> None:
        goal = "把回执写进运行根"
        self.plane.execute(request_payload(payload={"goal": goal}))
        receipts = (self.runtime / control_service.RECEIPTS_PATH)
        self.assertTrue(receipts.is_file())
        line = json.loads(receipts.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(line["receipt"]["kind"], "WORK_UNIT_QUEUED")
        serialised = json.dumps(line["record"], ensure_ascii=False)
        # the design: key NAMES and a digest travel to the read side, the VALUES never do
        self.assertNotIn(goal, serialised)
        self.assertIn("goal", line["record"]["checkpointKeys"])
        self.assertEqual(len(line["record"]["checkpointDigest"]), 64)


class ControlTransportTests(unittest.TestCase):
    """The loopback boundary is behaviour, not a comment."""

    def setUp(self) -> None:
        self.runtime = fixture_dir(prefix="control-http-")
        self.plane = control_service.build_plane(self.runtime, ROOT)
        self.server = control_service.ControlServer(self.plane)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.bound_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.plane.store.close()

    def _get(self, path: str, headers: dict | None = None):
        req = urllib.request.Request(self.base + path, headers=headers or {})
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def _post(self, path: str, body: dict, headers: dict | None = None):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", **(headers or {})},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def _status_of_rejected_method(self, method: str) -> int:
        req = urllib.request.Request(self.base + "/api/control/operations", data=b"{}", method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    def test_binds_loopback_and_publishes_a_dynamic_endpoint_descriptor(self) -> None:
        self.assertEqual(self.server.host, "127.0.0.1")
        self.assertGreater(self.server.bound_port, 0)
        descriptor_path = self.runtime / control_service.DESCRIPTOR_PATH
        descriptor = self.server.write_descriptor(descriptor_path)
        self.assertEqual(json.loads(descriptor_path.read_text(encoding="utf-8")), descriptor)
        self.assertEqual(descriptor["port"], self.server.bound_port)
        self.assertEqual(descriptor["transport"], "loopback-only")
        self.assertIn("evidence_ceiling", descriptor)

    def test_a_non_loopback_host_header_is_refused(self) -> None:
        code = self._status_of_request_with_host("example.com")
        self.assertEqual(code, 403)

    def _status_of_request_with_host(self, host: str) -> int:
        req = urllib.request.Request(self.base + "/api/control/descriptor", headers={"Host": host})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    def test_a_foreign_origin_is_refused(self) -> None:
        try:
            self._get("/api/control/descriptor", headers={"Origin": "https://evil.example"})
            self.fail("a non-loopback origin was served")
        except urllib.error.HTTPError as error:
            self.assertEqual(error.code, 403)

    def test_write_methods_other_than_the_single_post_are_405(self) -> None:
        for method in ("PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self._status_of_rejected_method(method), 405)

    def test_descriptor_lists_every_operation_with_its_own_support_level(self) -> None:
        status, descriptor = self._get("/api/control/descriptor")
        self.assertEqual(status, 200)
        self.assertEqual(descriptor["schema_version"], control_service.SCHEMA_VERSION)
        listed = {entry["operation"]: entry for entry in descriptor["operations"]}
        self.assertEqual(set(listed), set(control_service.OPERATIONS))
        self.assertEqual(listed["work-unit.create"]["support"], "IMPLEMENTED")
        self.assertEqual(listed["approval.decide"]["support"], "NOT_IMPLEMENTED")
        self.assertTrue(listed["approval.decide"]["reason_code"])

    def _raw_get(self, path: str):
        req = urllib.request.Request(self.base + path)
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8")

    def test_the_shell_is_served_by_the_write_origin_and_offers_no_auth_surface(self) -> None:
        """The boundary the owner set: local use, no login / token / key / account field, ever."""
        status, headers, html = self._raw_get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn("default-src 'none'", headers.get("Content-Security-Policy", ""))
        lowered = html.lower()
        # prose may mention these words (the page states the boundary); a CONTROL may not be one of them
        controls = re.findall(r"<input\b[^>]*>", lowered)
        self.assertTrue(controls, "the create form should have inputs")
        for forbidden in ("password", "api key", "api_key", "token", "oauth", "jwt", "vault", "credential",
                          "login", "锁屏"):
            for control in controls:
                self.assertNotIn(forbidden, control, f"the shell grew an auth control: {control}")
        self.assertIn('src="/control-shell.js"', html, "no inline script may satisfy a 'script-src self' CSP")
        script_status, _, script = self._raw_get("/control-shell.js")
        self.assertEqual(script_status, 200)
        self.assertNotIn("http://", script, "the shell must not reach outside its own origin")
        self.assertNotIn("https://", script)

    def test_an_unknown_read_path_is_404_not_a_open_proxy(self) -> None:
        try:
            self._raw_get("/proxy?target=https://example.com")
            self.fail("an unknown read path was served")
        except urllib.error.HTTPError as error:
            self.assertEqual(error.code, 404)

    def test_a_write_through_http_lands_in_the_store_the_observer_reads(self) -> None:
        status, result = self._post("/api/control/operations", request_payload())
        self.assertEqual(status, 200)
        errors = list(RESULT_VALIDATOR.iter_errors(result))
        self.assertEqual(errors, [])
        self.assertEqual(result["status"], "ACCEPTED", result["reason"])
        rows = self.plane.store.list_tasks()
        self.assertEqual([row["task_id"] for row in rows], ["WL-CONTROL-1"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
