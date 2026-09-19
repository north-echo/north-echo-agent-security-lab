import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from scripts.northecho.grading import GradingError, evaluate, run_bounded


class GradingRuntimeTests(unittest.TestCase):
    def test_wrong_shape_and_timeout_are_failed_checks(self):
        for error in (AttributeError("shape"), subprocess.TimeoutExpired("student", 1)):
            with self.subTest(error=type(error).__name__):
                grader = SimpleNamespace(grade=Mock(side_effect=error))
                checks = evaluate(grader, Path("."), {})
                self.assertFalse(all(check.passed for check in checks))
                self.assertTrue(checks[0].practice_hint)

    def test_empty_grading_is_not_a_pass(self):
        checks = evaluate(SimpleNamespace(grade=lambda *_: []), Path("."), {})
        self.assertFalse(checks[0].passed)

    def test_bounded_run_preserves_status_and_output(self):
        result = run_bounded([sys.executable, "-c", "print('synthetic'); raise SystemExit(7)"])
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, "synthetic\n")

    def test_bounded_run_enforces_deadline(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            run_bounded([sys.executable, "-c", "import time; time.sleep(1)"], timeout=0.03)

    def test_excessive_output_is_rejected(self):
        with self.assertRaises(GradingError):
            run_bounded([sys.executable, "-c", "print('x' * 1100000)"])
