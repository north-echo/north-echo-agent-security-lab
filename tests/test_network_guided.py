"""Replay documented synthetic networking exercises and verify policy parsing."""
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


class NetworkPolicyTests(unittest.TestCase):
    def setUp(self):
        source = ROOT / "course/module-08-network-egress/lesson-03/egress_broker.py"
        self.broker = types.ModuleType("guided_egress")
        exec(compile(source.read_text(), str(source), "exec"), self.broker.__dict__)
        self.policy = {"run_id": "test-run", "destinations": {
            "allowed.test": {"address": "127.0.0.1", "ports": frozenset({45123})}
        }}

    def test_authorization_returns_only_the_policy_address(self):
        address, authority, port, path = self.broker.authorize(
            self.policy, "test-run", "http://ALLOWED.test:45123/ok?view=small")
        self.assertEqual((address, authority, port, path),
                         ("127.0.0.1", "allowed.test:45123", 45123, "/ok?view=small"))
        for url in ("http://allowed.test:0/ok", "http://allowed.test:45123/ok\n",
                    "http://[invalid", "https://allowed.test:45123/ok"):
            with self.subTest(url=url), self.assertRaises(self.broker.Denied):
                self.broker.authorize(self.policy, "test-run", url)

    def test_policy_root_must_be_an_object_before_listening(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "policy.json"
            for value in (None, [], True, "policy"):
                path.write_text(json.dumps(value))
                with self.subTest(value=value), self.assertRaises(self.broker.Denied):
                    self.broker.load_policy(path)


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux network namespaces")
class NetworkGuidedTests(unittest.TestCase):
    def setUp(self):
        available = subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True)
        if available.returncode:
            self.skipTest("delegated user manager unavailable")
        self.temp = tempfile.TemporaryDirectory(prefix="ne-net-guided-")
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

    def test_parent_and_private_loopback_documented_observations(self):
        workspace, blocks = self.prepare("08.01")
        run = self.execute(workspace, blocks[1:])
        self.assertIn("NETWORK VIEW AND CONNECTION EVIDENCE: PASS", run.stdout)

    def test_one_shot_denial_requires_fresh_broker_for_repair(self):
        workspace, blocks = self.prepare("08.02")
        self.assertEqual(len(blocks), 7)
        _, helper, launch, direct, denial, repair, checkpoint = blocks
        run = self.execute(workspace, [helper, launch, direct, launch, denial,
                                      launch, repair, checkpoint])
        self.assertIn("DIRECT DENIAL AND MEDIATED REPAIR: PASS", run.stdout)

    def test_redirect_policy_changes_require_reload_and_cleanup(self):
        workspace, blocks = self.prepare("08.03")
        self.assertEqual(len(blocks), 10)
        (_, policy, helper, launch, observe, broaden_policy, broaden_call,
         repair_policy, repair_call, checkpoint) = blocks
        run = self.execute(workspace, [policy, helper, launch, observe, broaden_policy,
                                      launch, broaden_call, repair_policy, launch,
                                      repair_call, checkpoint])
        self.assertIn("REDIRECT REAUTHORIZATION AND POLICY REPAIR: PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
