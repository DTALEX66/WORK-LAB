#!/usr/bin/env python3
"""Unit tests for the pressed-state motion gate — the instrument, not the browser.

This gate had no test file at all, which is how it could go red on a CI runner (PR #220's `observer` job)
for a reason that had nothing to do with the product: `CSS.forcePseudoState` starts an 80ms transition, and
one computed-style read taken right after the force can land on the transition's FIRST frame
(`matrix(1, 0, 0, 1, 0, 0)`) instead of its end state (`matrix(0.99, ...)`). The runner read the frame and
convicted a correct render; the same command on the development host settles at 0.99.

These cases pin the two things that make that reading honest now: the sampler waits for the paint to stop
moving, and a value that is neither the untouched paint nor the token's end state is reported as
UNMEASURABLE rather than as a product failure.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "pressed_state_motion_via_cdp.py"

spec = importlib.util.spec_from_file_location("pressed_gate", str(SCRIPT))
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def page_state(transform: str, selector: str = ".nav button", count: int = 1) -> str:
    """The harvest expression's own shape, so the sampler is tested against what it really reads."""
    return json.dumps({"selectors": [{"selector": selector, "count": count,
                                      "transform": transform, "transitionDuration": "0.08s"}],
                       "tokens": {"pressedScale": ".99", "motionPressed": "80ms"},
                       "reducedMotion": False})


class FakeCdp:
    """A session whose animation either ticks or does not — the two CI outcomes."""

    def __init__(self, transforms: list[str]) -> None:
        self.transforms = transforms
        self.sent: list[tuple[str, dict]] = []

    def evaluate(self, expr: str) -> str:
        index = min(self.reads, len(self.transforms) - 1)
        self.reads += 1
        return page_state(self.transforms[index])

    def send(self, method: str, params: dict | None = None) -> dict:
        self.sent.append((method, params or {}))
        return {}

    @property
    def reads(self) -> int:
        return getattr(self, "_reads", 0)

    @reads.setter
    def reads(self, value: int) -> None:
        self._reads = value


class SettledSamplerTests(unittest.TestCase):
    def test_a_transition_that_ticks_is_read_at_its_end_value(self) -> None:
        cdp = FakeCdp(["matrix(1, 0, 0, 1, 0, 0)",        # t=0 frame, must not be the answer
                       "matrix(0.995, 0, 0, 0.995, 0, 0)",
                       "matrix(0.99, 0, 0, 0.99, 0, 0)",
                       "matrix(0.99, 0, 0, 0.99, 0, 0)"])
        cdp.reads = 0
        with mock.patch.object(gate.time, "sleep", lambda _s: None):
            transform, waited = gate.settled_transform(cdp, "EXPRESSION", budget_s=5.0, poll_s=0.01)
        self.assertEqual(transform, "matrix(0.99, 0, 0, 0.99, 0, 0)",
                         "the sampler has to return the state the operator sees, not the first frame")
        self.assertGreater(cdp.reads, 3, "it should have kept reading until two samples agreed")

    def test_a_frozen_animation_reports_the_value_it_kept_seeing(self) -> None:
        # The CI failure mode: the runner never advanced the transition, so every read is the identity.
        # Two identical samples means "stable", and stability at a non-end value is the verdict's problem
        # to classify — the sampler must not spin forever.
        cdp = FakeCdp(["matrix(1, 0, 0, 1, 0, 0)"])
        cdp.reads = 0
        with mock.patch.object(gate.time, "sleep", lambda _s: None):
            transform, waited = gate.settled_transform(cdp, "EXPRESSION", budget_s=1.0, poll_s=0.06)
        self.assertEqual(transform, "matrix(1, 0, 0, 1, 0, 0)")
        self.assertLessEqual(waited, 1.0, "the wait is bounded; a hung instrument must still answer")


class VerdictClassificationTests(unittest.TestCase):
    """A frame is not a state: the gate must call it unmeasurable instead of convicting the product."""

    def _readings(self, pressed_transform: str) -> dict:
        row = {"selector": ".nav button", "count": 1, "transitionDuration": "0.08s",
               "transform": pressed_transform, "tag": "button", "label": "Projects"}
        idle = {"selectors": [dict(row, transform="none")],
                "tokens": {"pressedScale": ".99", "motionPressed": "80ms"}, "reducedMotion": False}
        pressed = {"selectors": [dict(row, transform=pressed_transform)],
                   "tokens": idle["tokens"], "reducedMotion": False}
        return {"console": {"required": ".nav button", "idle": idle, "pressed": pressed}}

    def _check(self, result: dict, name: str) -> dict:
        return next(c for c in result["checks"] if c["check"] == name)

    def test_a_first_frame_read_is_unmeasurable_not_a_product_failure(self) -> None:
        result = gate.verdict(self._readings("matrix(1, 0, 0, 1, 0, 0)"))
        self.assertEqual(result["unmeasurable"], ["console/.nav button"])
        self.assertFalse(self._check(result, "pressed-paint-read-was-settled[console:.nav button]")["pass"])
        detail = self._check(result, "active-transform-matches-token[console:.nav button]")["detail"]
        self.assertIn("settledRead=False", detail,
                      "the paint check must say the read was not a settled state, so a reader does not "
                      "conclude the stylesheet lost its pressed rule")

    def test_the_end_value_is_settled_and_passes(self) -> None:
        result = gate.verdict(self._readings("matrix(0.99, 0, 0, 0.99, 0, 0)"))
        self.assertEqual(result["unmeasurable"], [])
        self.assertTrue(self._check(result, "pressed-paint-read-was-settled[console:.nav button]")["pass"])
        self.assertTrue(self._check(result, "active-transform-matches-token[console:.nav button]")["pass"])

    def test_no_painted_change_is_still_a_real_failure(self) -> None:
        # If the rule stopped reaching the element altogether, the read is stable AT the idle value: that
        # is settled, and the paint-change check is the one that has to convict it.
        result = gate.verdict(self._readings("none"))
        self.assertEqual(result["unmeasurable"], [], "an unchanged paint is measurable, just wrong")
        self.assertFalse(self._check(result, "pressed-state-changes-the-paint[console:.nav button]")["pass"])


class TokenExpectationTests(unittest.TestCase):
    def test_the_expected_scale_comes_from_the_token_not_a_literal(self) -> None:
        scale, duration, problems = gate.token_expectations(
            {"pressedScale": ".99", "motionPressed": "80ms"})
        self.assertEqual((scale, duration), (0.99, 0.08))
        self.assertEqual(problems, [])

    def test_an_unparseable_token_is_named_instead_of_defaulting(self) -> None:
        scale, _duration, problems = gate.token_expectations({"pressedScale": "auto", "motionPressed": "80ms"})
        self.assertIsNone(scale)
        self.assertTrue(any("pressedScale" in p for p in problems), problems)

    def test_a_missing_token_is_not_silently_zero(self) -> None:
        scale, duration, problems = gate.token_expectations({})
        self.assertIsNone(scale)
        self.assertIsNone(duration)
        self.assertEqual(len(problems), 2, "both tokens must be reported missing, not assumed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
