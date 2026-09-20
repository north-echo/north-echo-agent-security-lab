"""Run the documented bounded cgroup observations in prepared owned workspaces."""
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


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux cgroups")
class CgroupGuidedTests(unittest.TestCase):
    def setUp(self):
        available = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True)
        if available.returncode:
            self.skipTest("delegated user manager unavailable")
        self.temp = tempfile.TemporaryDirectory(prefix="ne-cgroup-guided-")
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
        run = subprocess.run(["bash", "-c", "\n".join(blocks)], cwd=workspace,
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return run

    def test_cpu_effective_limit_from_documented_commands(self):
        workspace, blocks = self.prepare("07.01")
        helper, = [block for block in blocks if "new_cpu_unit()" in block]
        launch, = [block for block in blocks if ' > limited.json' in block]
        checkpoint, = [block for block in blocks if 'CPU STATE: PASS' in block]
        run = self.execute(workspace, [helper, launch, checkpoint])
        self.assertIn("CPU STATE: PASS", run.stdout)
        self.assertEqual(json.loads((workspace / "limited.json").read_text())["cpu_max"], "50000 100000")

    def test_memory_limit_requires_specific_oom_evidence(self):
        workspace, blocks = self.prepare("07.02")
        helper, = [block for block in blocks if "new_memory_unit()" in block]
        launch, = [block for block in blocks if "NE_MEMORY_STATUS=0" in block]
        checkpoint, = [block for block in blocks if "MEMORY LIMIT AND OOM EVIDENCE: PASS" in block]
        run = self.execute(workspace, [helper, launch, checkpoint])
        self.assertIn("MEMORY LIMIT AND OOM EVIDENCE: PASS", run.stdout)
        for invalid in ("0", "97", "-1", "many"):
            result = subprocess.run([sys.executable, "memory_hog.py", invalid], cwd=workspace,
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("allocated_mib", result.stdout)

    def test_task_limit_event_and_timeout_cleanup_are_observed(self):
        workspace, blocks = self.prepare("07.03")
        helper, = [block for block in blocks if "new_task_unit()" in block]
        launch, = [block for block in blocks if " > task-output.json" in block]
        checkpoint, = [block for block in blocks if "TASK LIMIT AND REJECTION EVENT: PASS" in block]
        timeout_case, = [block for block in blocks if "NE_CLIENT_STATUS=0" in block]
        run = self.execute(workspace, [helper, launch, checkpoint, timeout_case,
                                      'test "$NE_CLIENT_STATUS" -eq 124'])
        self.assertIn("TASK LIMIT AND REJECTION EVENT: PASS", run.stdout)
        self.assertIn("LoadState=not-found", run.stdout)
        for invalid in ("0", "65", "-1", "many"):
            result = subprocess.run([sys.executable, "fork_pressure.py", invalid], cwd=workspace,
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('"created"', result.stdout)


if __name__ == "__main__":
    unittest.main()
