"""Replay the fixed local model; do not turn model choices into kernel claims."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "course/module-11-break-fix-research"


class ModelGuidedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-model-guided-")
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

    def test_seeded_effects_and_replay(self):
        self.replay("11.01", "FIXED LOCAL EFFECTS AND REPLAY: PASS")

    def test_incomplete_evidence_is_not_negative(self):
        self.replay("11.02", "INVARIANT MATRIX AND MISSING-EVIDENCE REFUSAL: PASS")

    def test_complete_and_partial_repair(self):
        self.replay("11.03", "COMPLETE MODEL REPAIR, PRESERVATION, AND IDEMPOTENCE: PASS")


class ModelRepairValidationTests(unittest.TestCase):
    def test_invalid_types_preserve_existing_destination(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan = json.loads((COURSE / "lesson-03/vulnerable-plan.json").read_text())
            plan["controls"]["execution"] = ["argv"]
            source, output = root / "input.json", root / "output.json"
            source.write_text(json.dumps(plan))
            output.write_text("existing operator content")
            run = subprocess.run([sys.executable, str(COURSE / "lesson-03/repair_variant.py"),
                                  str(source), str(output)], capture_output=True, timeout=5)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(output.read_text(), "existing operator content")
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["input.json", "output.json"])

    def test_input_alias_and_symlink_destination_are_refused(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "input.json"
            shutil.copy2(COURSE / "lesson-03/vulnerable-plan.json", source)
            before = source.read_bytes()
            alias = root / "alias.json"
            alias.symlink_to(source)
            for output in (source, alias):
                run = subprocess.run([sys.executable, str(COURSE / "lesson-03/repair_variant.py"),
                                      str(source), str(output)], capture_output=True, timeout=5)
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(source.read_bytes(), before)
            self.assertTrue(alias.is_symlink())


if __name__ == "__main__":
    unittest.main()
