from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "scripts"))
sys.path.insert(0, str(SOURCE / "graders"))

import module_10  # noqa: E402


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux containment validation")
class Module10GraderTests(unittest.TestCase):
    fixture = {"hostname": "grade-test10", "canary": "GRADE-test-only"}

    def test_starter_runs_but_fails_composition_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-10-complete-runtime/lab/complete_runtime.py", workspace / "complete_runtime.py")
            checks = module_10.grade(workspace, self.fixture)
        self.assertFalse(all(check.passed for check in checks))
        self.assertFalse(next(c.passed for c in checks if c.name == "CPU, memory, swap, and PID limits are effective"))

    def test_guided_launcher_passes_all_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-10-complete-runtime/lesson-03/complete_runtime.py", workspace / "complete_runtime.py")
            checks = module_10.grade(workspace, self.fixture)
        self.assertTrue(all(check.passed for check in checks), json.dumps([(c.name, c.passed) for c in checks]))

    def test_systemd_environment_expansion_is_not_literal_argv(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            source = (SOURCE / "course/module-10-complete-runtime/lesson-03/complete_runtime.py").read_text()
            source = source.replace('"--expand-environment=no", ', '')
            (workspace / "complete_runtime.py").write_text(source)
            checks = module_10.grade(workspace, self.fixture)
        literal = next(c for c in checks if c.name == "Literal paths are preserved without shell evaluation")
        self.assertFalse(literal.passed)


if __name__ == "__main__":
    unittest.main()
