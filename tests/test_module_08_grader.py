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

import module_08  # noqa: E402


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class Module08GraderTests(unittest.TestCase):
    fixture = {"hostname": "grade-test08", "canary": "GRADE-test-only"}

    def test_starter_fails_closed_and_does_not_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-08-network-egress/lab/egress_broker.py", workspace / "egress_broker.py")
            checks = module_08.grade(workspace, self.fixture)
        self.assertFalse(all(check.passed for check in checks))
        self.assertFalse(next(c.passed for c in checks if c.name == "Approved synthetic request succeeds"))

    def test_guided_broker_passes_lab_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-08-network-egress/lesson-03/egress_broker.py", workspace / "egress_broker.py")
            checks = module_08.grade(workspace, self.fixture)
        self.assertTrue(all(check.passed for check in checks), json.dumps([(c.name, c.passed) for c in checks]))


if __name__ == "__main__":
    unittest.main()
