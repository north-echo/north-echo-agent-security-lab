"""Replay the credential lessons using only their fixed synthetic material."""
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


ROOT = Path(__file__).resolve().parents[1]


class CapabilityMechanismTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "course/module-09-credential-brokering/lesson-02/capability.py"
        self.tool = types.ModuleType("guided_capability")
        exec(compile(path.read_text(), str(path), "exec"), self.tool.__dict__)
        self.key = b"FAKE-TEST-KEY-NOT-FOR-REAL-AUTHORITY"

    def test_binding_is_distinct_from_valid_authentication(self):
        token = self.tool.mint(self.key, "read", "record:alpha", "lesson", "run", 60, "{}")
        claims = self.tool.verify(self.key, token, "read", "record:alpha", "lesson", "run", "{}")
        self.assertEqual(claims["operation"], "read")
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            self.tool.verify(self.key, token, "read", "record:beta", "lesson", "run", "{}")
        self.assertEqual(self.tool.verify(
            self.key, token, "read", "record:alpha", "lesson", "run", "{}"), claims)

    def test_serialization_convention_and_mint_bounds(self):
        self.assertEqual(self.tool.input_digest('{"a":1,"b":2}'),
                         self.tool.input_digest('{ "b": 2, "a": 1 }'))
        for ttl in (0, 301):
            with self.subTest(ttl=ttl), self.assertRaises(ValueError):
                self.tool.mint(self.key, "read", "record:alpha", "lesson", "run", ttl, "{}")
        with self.assertRaises(ValueError):
            self.tool.input_digest('{"value": NaN}')


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux owned user services")
class CredentialGuidedTests(unittest.TestCase):
    def setUp(self):
        available = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True)
        if available.returncode:
            self.skipTest("delegated user manager unavailable")
        self.temp = tempfile.TemporaryDirectory(prefix="ne-cred-guided-")
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

    def test_environment_disclosure_deliberate_regression_and_repair(self):
        workspace, blocks = self.prepare("09.01")
        self.assertEqual(len(blocks), 6)
        _, inherited, clean, regressed, repaired, checkpoint = blocks
        change = """python3 - <<'PY'
from pathlib import Path
p = Path("clean_launch.py")
p.write_text(p.read_text().replace("env=clean", "env=os.environ.copy()"))
PY"""
        restore = """python3 - <<'PY'
from pathlib import Path
p = Path("clean_launch.py")
p.write_text(p.read_text().replace("env=os.environ.copy()", "env=clean"))
PY"""
        run = self.execute(workspace, [inherited, clean, change, regressed,
                                      restore, repaired, checkpoint])
        self.assertIn("CREDENTIAL INHERITANCE AND REPAIR: PASS", run.stdout)

    def test_readable_claims_binding_expiry_and_repeat_verification(self):
        workspace, blocks = self.prepare("09.02")
        run = self.execute(workspace, blocks[1:])
        self.assertIn("BINDING, EXPIRY, AND REPLAY LIMIT: PASS", run.stdout)

    def test_operation_broker_nonce_consumption_binding_and_cleanup(self):
        workspace, blocks = self.prepare("09.03")
        run = self.execute(workspace, blocks[1:])
        self.assertIn("OPERATION BINDING AND PROCESS-LIFETIME REPLAY: PASS", run.stdout)
        self.assertEqual(json.loads((workspace / "approved.json").read_text()),
                         {"ok": True, "result": {"value": "synthetic-record-value"}})


if __name__ == "__main__":
    unittest.main()
