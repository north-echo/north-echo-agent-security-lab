from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="north-echo-test-")
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE, self.root, ignore=shutil.ignore_patterns(".student", ".fixtures", ".runtime", ".state", "__pycache__", "*.pyc"))
        for name in (".student", ".fixtures", ".runtime", ".state"):
            (self.root / name).mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, command: str, *args: str, expected: int = 0):
        run = subprocess.run(
            [sys.executable, str(self.root / "scripts" / "labctl.py"), command, *args],
            cwd=self.root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        return run

    def test_replay_rotates_fixture_and_preserves_only_metadata(self):
        self.run_cli("start", "01.01")
        first = json.loads((self.root / ".student" / "01.01" / ".north-echo.json").read_text())
        solution = self.root / ".student" / "01.01" / "my-solution.txt"
        solution.write_text("student work")
        self.run_cli("reset", "01.01", "--yes")
        self.assertFalse(solution.exists())
        self.run_cli("start", "01.01")
        second = json.loads((self.root / ".student" / "01.01" / ".north-echo.json").read_text())
        self.assertNotEqual(first["fixture_id"], second["fixture_id"])
        progress = json.loads((self.root / ".state" / "progress.json").read_text())
        self.assertEqual(progress["targets"]["01.01"]["starts"], 2)
        self.assertEqual(progress["targets"]["01.01"]["resets"], 1)
        self.assertNotIn("student work", json.dumps(progress))

    def test_module_scope_and_dry_run(self):
        self.run_cli("start", "01.01")
        self.run_cli("start", "01.02")
        dry = self.run_cli("reset", "module-01", "--dry-run")
        self.assertIn("DRY RUN", dry.stdout)
        self.assertTrue((self.root / ".student" / "01.01").exists())
        self.run_cli("reset", "module-01", "--yes")
        self.assertFalse((self.root / ".student" / "01.01").exists())
        self.assertFalse((self.root / ".student" / "01.02").exists())

    def test_canonical_change_blocks_start(self):
        lesson = self.root / "course" / "module-01-process-authority" / "lesson-01" / "README.md"
        lesson.write_text(lesson.read_text() + "\nchanged\n")
        run = self.run_cli("start", "01.01", expected=2)
        self.assertIn("changed canonical file", run.stderr)

    def test_symlink_escape_is_rejected(self):
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep")
        os.symlink(outside, self.root / ".student" / "01.01")
        run = self.run_cli("reset", "01.01", "--yes", expected=2)
        self.assertIn("outside lab root", run.stderr)
        self.assertEqual((outside / "keep.txt").read_text(), "keep")

    def test_starter_module_one_fails_security_properties(self):
        self.run_cli("start", "module-01")
        run = self.run_cli("grade", "module-01", expected=1)
        self.assertIn("RESULT: NOT PASSED", run.stdout)
        self.assertTrue(
            "environment authority" in run.stdout or "launcher builds cleanly" in run.stdout,
            run.stdout,
        )

    def test_status_and_scaffold_messages(self):
        status = self.run_cli("status")
        self.assertIn("01.01", status.stdout)
        scaffold = self.run_cli("start", "05.03", expected=3)
        self.assertIn("scaffolded", scaffold.stdout)
        capstone = self.run_cli("start", "capstone", "--cold", expected=3)
        self.assertIn("not implemented", capstone.stdout)

    def test_cleanup_registry_dry_run_and_removal(self):
        runtime = self.root / ".runtime" / "01.01"
        temporary = runtime / "owned-temp"
        temporary.mkdir(parents=True)
        (temporary / "marker").write_text("synthetic")
        (runtime / "resources.json").write_text(json.dumps({"temp_paths": [str(temporary)]}))
        dry = self.run_cli("cleanup", "01.01", "--dry-run")
        self.assertIn("remove temp", dry.stdout)
        self.assertTrue(temporary.exists())
        self.run_cli("cleanup", "01.01")
        self.assertFalse(runtime.exists())

    def test_cleanup_registry_rejects_external_path(self):
        outside = Path(self.temporary.name) / "outside-cleanup"
        outside.mkdir()
        marker = outside / "keep"
        marker.write_text("keep")
        runtime = self.root / ".runtime" / "01.01"
        runtime.mkdir(parents=True)
        (runtime / "resources.json").write_text(json.dumps({"temp_paths": [str(outside)]}))
        run = self.run_cli("cleanup", "01.01", expected=2)
        self.assertIn("outside lab root", run.stderr)
        self.assertEqual(marker.read_text(), "keep")

    def test_reset_preserves_pass_metadata(self):
        self.run_cli("start", "01.01")
        progress_path = self.root / ".state" / "progress.json"
        progress = json.loads(progress_path.read_text())
        progress["targets"]["01.01"]["passed"] = True
        progress_path.write_text(json.dumps(progress))
        self.run_cli("reset", "01.01", "--yes")
        preserved = json.loads(progress_path.read_text())
        self.assertTrue(preserved["targets"]["01.01"]["passed"])

    def test_exam_mode_withholds_lesson_references(self):
        self.run_cli("start", "module-01", "--mode", "exam")
        run = self.run_cli("grade", "module-01", expected=1)
        self.assertIn("EXAM MODE", run.stdout)
        self.assertNotIn("Review:", run.stdout)

    def test_every_guided_lesson_has_local_line_explanations(self):
        lessons = sorted((SOURCE / "course").glob("module-0[1-3]-*/lesson-*/README.md"))
        self.assertEqual(len(lessons), 9)
        for lesson in lessons:
            text = lesson.read_text(encoding="utf-8")
            self.assertIn("### Line by line", text, str(lesson))

    def test_field_manual_is_self_contained_and_substantial(self):
        manual = (SOURCE / "docs" / "MANUAL_MODULES_01_03.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(manual.split()), 8000)
        for phrase in (
            "Reading command and code blocks",
            "Complete source:",
            "Troubleshooting and checkpoint",
            "Module 01 independent practical",
            "Module 02 independent practical",
            "Module 03 independent practical",
            "Integrated understanding",
            "Glossary",
        ):
            self.assertIn(phrase, manual)


if __name__ == "__main__":
    unittest.main()
