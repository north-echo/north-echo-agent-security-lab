"""Strict release validation must actually execute a nonempty successful suite."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


class StrictRunnerTests(unittest.TestCase):
    def invoke(self, count, skipped=(), successful=True):
        source = Path(__file__).resolve().parents[1] / "scripts/run_tests.py"
        spec = importlib.util.spec_from_file_location("strict_runner_under_test", source)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        result = mock.Mock(testsRun=count, skipped=list(skipped))
        result.wasSuccessful.return_value = successful
        with mock.patch.object(runner.sys, "argv", [str(source), "--require-no-skips"]), \
                mock.patch.object(runner.sys, "path", list(runner.sys.path)), \
                mock.patch.object(runner.unittest.defaultTestLoader, "discover"), \
                mock.patch.object(runner.unittest, "TextTestRunner") as factory, \
                contextlib.redirect_stderr(io.StringIO()):
            factory.return_value.run.return_value = result
            return runner.main()

    def test_empty_discovery_is_a_strict_failure(self):
        self.assertEqual(self.invoke(0), 1)

    def test_only_exercised_success_without_skips_passes(self):
        self.assertEqual(self.invoke(1), 0)
        self.assertEqual(self.invoke(1, skipped=[("case", "unsupported")]), 1)
        self.assertEqual(self.invoke(1, successful=False), 1)
