from __future__ import annotations

import sys
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "scripts"))

from graders.module_02 import _pid_namespace_isolated


class Module02GraderTests(unittest.TestCase):
    def test_accepts_pid_one_reported_from_namespace_local_procfs(self):
        payload = {"pid_inode": 200, "nspid": [1]}
        self.assertTrue(_pid_namespace_isolated(payload, grader_pid_inode=100))

    def test_rejects_grader_pid_namespace(self):
        payload = {"pid_inode": 100, "nspid": [1]}
        self.assertFalse(_pid_namespace_isolated(payload, grader_pid_inode=100))

    def test_rejects_child_that_is_not_namespace_pid_one(self):
        payload = {"pid_inode": 200, "nspid": [7]}
        self.assertFalse(_pid_namespace_isolated(payload, grader_pid_inode=100))


if __name__ == "__main__":
    unittest.main()
