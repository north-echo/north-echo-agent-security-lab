"""Exercise the runtime walkthrough and fail-closed owned-unit collection."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class RuntimeOwnershipTests(unittest.TestCase):
    def setUp(self):
        source = ROOT / "course/module-10-complete-runtime/lesson-03/complete_runtime.py"
        self.runtime = types.ModuleType("guided_runtime")
        exec(compile(source.read_text(), str(source), "exec"), self.runtime.__dict__)
        self.owner = {"unit": "north-echo-1000-10-lab-12345678.service", "uid": 1000,
                      "description": "North Echo 10.lab workspace=/tmp/owned", "record": None}

    def test_prepared_independent_lab_uses_the_course_registry(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw) / ".student/10.lab"
            workspace.mkdir(parents=True)
            self.runtime.__file__ = str(workspace / "complete_runtime.py")
            with patch.object(self.runtime.subprocess, "run") as run:
                owner = self.runtime.register_owner({"PATH": "/usr/bin:/bin"})
            self.assertEqual(run.call_args.args[0][2:4], ["register-unit", "10.lab"])
            self.assertIsNone(owner["record"])
            self.assertFalse((workspace / ".runtime").exists())

    def test_foreign_description_is_not_stopped(self):
        response = subprocess.CompletedProcess([], 0,
            "LoadState=loaded\nDescription=another owner\n"
            "ControlGroup=/user.slice/user-1000.slice/user@1000.service/app.slice/"
            "north-echo-1000-10-lab-12345678.service\n", "")
        with patch.object(self.runtime.subprocess, "run", return_value=response) as run:
            with self.assertRaisesRegex(RuntimeError, "ownership mismatch"):
                self.runtime.collect_owned(self.owner, {})
        self.assertEqual(run.call_count, 1)
        self.assertIn("show", run.call_args.args[0])

    def test_manager_error_is_not_absence_and_keeps_record(self):
        with tempfile.TemporaryDirectory() as raw:
            record = Path(raw) / "owner.json"
            record.write_text("{}")
            self.owner["record"] = record
            response = subprocess.CompletedProcess([], 1, "", "user manager unavailable")
            with patch.object(self.runtime.subprocess, "run", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "could not be established"):
                    self.runtime.collect_owned(self.owner, {})
            self.assertTrue(record.exists())
            absent = subprocess.CompletedProcess([], 0, "LoadState=not-found\n", "")
            with patch.object(self.runtime.subprocess, "run", return_value=absent):
                self.runtime.collect_owned(self.owner, {})
            self.assertFalse(record.exists())


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux containment")
class RuntimeGuidedTests(unittest.TestCase):
    def setUp(self):
        available = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True)
        if available.returncode:
            self.skipTest("delegated user manager unavailable")
        self.temp = tempfile.TemporaryDirectory(prefix="ne-rt-guided-")
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            ".git", ".student", ".fixtures", ".runtime", ".state", "__pycache__",
            "*.pyc", "output", "dist-*"))

    def tearDown(self):
        if not hasattr(self, "temp"):
            return
        cleanup = subprocess.run([sys.executable, str(self.root / "scripts/labctl.py"),
                                  "cleanup", "--all"], cwd=self.root,
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(cleanup.returncode, 0, cleanup.stdout + cleanup.stderr)
        self.temp.cleanup()

    def prepare(self, target):
        run = subprocess.run([sys.executable, str(self.root / "scripts/labctl.py"),
                              "start", target], cwd=self.root, capture_output=True,
                             text=True, timeout=10)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        workspace = self.root / ".student" / target
        blocks = re.findall(r"```bash\n(.*?)\n```", (workspace / "README.md").read_text(), re.S)
        return workspace, blocks

    def execute(self, workspace, blocks):
        run = subprocess.run(["bash", "-e", "-c", "\n".join(blocks)], cwd=workspace,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return run

    def test_dependency_mistakes_and_repair_are_distinct_from_execution(self):
        workspace, blocks = self.prepare("10.01")
        self.assertEqual(len(blocks), 5)
        _, initial, challenge, repaired, checkpoint = blocks
        edit = """python3 - <<'PY'
import json
from pathlib import Path
p = Path("challenge-plan.json")
steps = json.loads(p.read_text())
steps.remove("enter_cgroup")
steps.insert(steps.index("enter_namespaces"), "enter_cgroup")
p.write_text(json.dumps(steps))
PY"""
        run = self.execute(workspace, [initial, challenge, edit, repaired, checkpoint])
        self.assertIn("LAUNCH DEPENDENCIES: PASS", run.stdout)

    def test_inner_guard_preserves_allowed_work_and_denies_two_operations(self):
        workspace, blocks = self.prepare("10.02")
        run = self.execute(workspace, blocks[1:])
        self.assertIn("FILESYSTEM AND SYSCALL COMPOSITION: PASS", run.stdout)

    def test_complete_composition_and_faded_single_job_sequence(self):
        workspace, blocks = self.prepare("10.03")
        run = self.execute(workspace, blocks[1:])
        self.assertIn("COMPOSED EFFECTS AND EXACT COLLECTION: PASS", run.stdout)
        demos = list(workspace.glob("d.*"))
        self.assertEqual(len(demos), 1)
        demo = demos[0]
        for index, expected_status in enumerate((0, 7, 0), start=1):
            result = json.loads((demo / f"job-{index}-result.json").read_text())
            self.assertEqual(result["status"], expected_status)
            self.assertEqual(result["attestation"]["requested_status"], expected_status)
            self.assertEqual(result["attestation"]["memory"], 33554432 if index == 2 else 50331648)
            state = subprocess.run(["systemctl", "--user", "show", result["unit"],
                                    "--property=LoadState"], text=True, capture_output=True)
            self.assertEqual(state.stdout.strip(), "LoadState=not-found")
        self.assertFalse((demo / "allowed/broker.sock").exists())


if __name__ == "__main__":
    unittest.main()
