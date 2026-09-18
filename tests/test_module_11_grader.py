from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "scripts"))
sys.path.insert(0, str(SOURCE / "graders"))
import module_11  # noqa: E402


class Module11GraderTests(unittest.TestCase):
    fixture = {"hostname": "grade-test11", "canary": "GRADE-test-only"}

    def test_starter_fails_multi_weakness_variants(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-11-break-fix-research/lab/repair_variant.py", workspace / "repair_variant.py")
            checks = module_11.grade(workspace, self.fixture)
        self.assertFalse(all(item.passed for item in checks))
        self.assertFalse(next(item.passed for item in checks if item.name == "All simultaneous seeded weaknesses are repaired"))

    def test_guided_repair_passes_all_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            shutil.copy2(SOURCE / "course/module-11-break-fix-research/lesson-03/repair_variant.py", workspace / "repair_variant.py")
            checks = module_11.grade(workspace, self.fixture)
        self.assertTrue(all(item.passed for item in checks), json.dumps([(item.name, item.passed) for item in checks]))

    def test_vulnerable_filesystem_mode_reproduces_protected_read(self):
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            plan = work / "plan.json"
            evidence = work / "evidence.json"
            plan.write_text(json.dumps({
                "schema": 1, "variant_id": "symlink-regression",
                "workload": {"operation": "read", "resource": "record:test", "literal": "literal"},
                "controls": dict(module_11.SECURE, filesystem="lexical"),
            }))
            run = subprocess.run([
                sys.executable,
                str(SOURCE / "course/module-11-break-fix-research/lesson-01/variant_harness.py"),
                str(plan), str(evidence), str(work / "harness"),
            ], check=False)
            observed = json.loads(evidence.read_text())
        self.assertEqual(run.returncode, 0)
        self.assertTrue(observed["protected_read"])


if __name__ == "__main__":
    unittest.main()
