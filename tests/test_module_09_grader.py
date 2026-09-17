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

import module_09  # noqa: E402


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux Unix-socket validation")
class Module09GraderTests(unittest.TestCase):
    fixture = {"hostname": "grade-test09", "canary": "GRADE-test-only"}

    def test_starter_is_runnable_but_fails_capability_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-09-credential-brokering/lab/capability_broker.py", workspace / "capability_broker.py")
            checks = module_09.grade(workspace, self.fixture)
        self.assertFalse(all(check.passed for check in checks))
        self.assertFalse(next(c.passed for c in checks if c.name == "Valid operation capability reaches the synthetic upstream"))

    def test_guided_broker_passes_all_lab_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-09-credential-brokering/lesson-03/capability_broker.py", workspace / "capability_broker.py")
            checks = module_09.grade(workspace, self.fixture)
        self.assertTrue(all(check.passed for check in checks), json.dumps([(c.name, c.passed) for c in checks]))


if __name__ == "__main__":
    unittest.main()
