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

import module_06  # noqa: E402


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class Module06GraderTests(unittest.TestCase):
    fixture = {"hostname": "grade-test06", "canary": "GRADE-test-only"}

    def test_starter_runs_but_fails_confinement(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-06-seccomp/lab/seccomp_guard.c", workspace / "seccomp_guard.c")
            checks = module_06.grade(workspace, self.fixture)
        self.assertFalse(all(check.passed for check in checks))
        self.assertFalse(next(c.passed for c in checks if c.name == "An unlisted harmless syscall returns EPERM"))

    def test_guided_default_deny_design_passes_lab_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-06-seccomp/lesson-03/allowlist.c", workspace / "seccomp_guard.c")
            checks = module_06.grade(workspace, self.fixture)
        self.assertTrue(all(check.passed for check in checks), json.dumps([(c.name, c.passed) for c in checks]))


if __name__ == "__main__":
    unittest.main()
