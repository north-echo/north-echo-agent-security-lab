"""Exercise only the fixed label fixtures and non-executing evidence review."""
from __future__ import annotations

import json
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "course/module-12-adaptive-adversary"


class EvidenceGuidedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-evidence-guided-")
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            ".git", ".student", ".fixtures", ".runtime", ".state", "__pycache__",
            "*.pyc", "output", "dist-*"))

    def tearDown(self):
        self.temp.cleanup()

    def replay(self, target, checkpoint):
        run = subprocess.run([sys.executable, str(self.root / "scripts/labctl.py"),
                              "start", target], cwd=self.root, capture_output=True,
                             text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        workspace = self.root / ".student" / target
        blocks = re.findall(r"```bash\n(.*?)\n```", (workspace / "README.md").read_text(), re.S)
        run = subprocess.run(["bash", "-e", "-c", "\n".join(blocks[1:])],
                             cwd=workspace, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(checkpoint, run.stdout)

    def test_fixed_schedule_does_not_answer_omitted_question(self):
        self.replay("12.01", "FIXED SCHEDULE AND OMITTED-QUESTION LIMIT: PASS")

    def test_budget_and_offline_evidence_distinctions(self):
        self.replay("12.02", "BUDGET, FAILURE, AND MISSING-EVIDENCE DISTINCTIONS: PASS")

    def test_package_integrity_failure_repair_and_relocation(self):
        self.replay("12.03", "PORTABLE REPLAY AND NON-EXECUTING INTEGRITY CHECKS: PASS")


class EvidenceValidationTests(unittest.TestCase):
    def test_malformed_rows_are_not_classified_as_measurements(self):
        review = runpy.run_path(str(COURSE / "lesson-02/review_evidence.py"))["review"]
        valid = {"case_id": "test", "budget": 3,
                 "observations": [{"check": "allowed_work", "outcome": "success"}]}
        for case in (
            dict(valid, budget=True),
            dict(valid, observations=[{"check": "allowed_work", "outcome": False}]),
            dict(valid, observations=[{"check": [], "outcome": "success"}]),
            dict(valid, observations=valid["observations"] * 2),
        ):
            with self.subTest(case=case), self.assertRaises(ValueError):
                review(case)

    def test_inventory_rejects_extra_paths_before_reading_them(self):
        verify = runpy.run_path(str(COURSE / "lesson-03/verify_package.py"))["verify"]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "package.json").write_text(json.dumps({"sha256": {"../outside": "0" * 64}}))
            with self.assertRaisesRegex(ValueError, "unexpected package inventory"):
                verify(root)


if __name__ == "__main__":
    unittest.main()
