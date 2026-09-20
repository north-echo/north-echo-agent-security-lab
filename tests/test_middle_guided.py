"""Behavioral checks for revised guided examples, not just their headings."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GuidedWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-guided-")
        self.work = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def copy_lesson(self, relative):
        shutil.copytree(ROOT / "course" / relative, self.work, dirs_exist_ok=True)

    def run_command(self, argv, **kwargs):
        return subprocess.run(argv, cwd=self.work, text=True, capture_output=True,
                              timeout=10, **kwargs)

    def compile_source(self, source, output, *flags):
        run = self.run_command(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                                "-O2", source, "-o", output, *flags])
        self.assertEqual(run.returncode, 0, run.stderr)


class ToolLoopGuidedTests(GuidedWorkspace):
    def test_trace_effect_and_practiced_failure_aggregation(self):
        self.copy_lesson("module-04-minimal-agent/lesson-01")
        run = self.run_command([sys.executable, "agent_loop.py", "task.json", "trace.jsonl"])
        self.assertEqual(run.returncode, 0, run.stderr)
        records = [json.loads(line) for line in (self.work / "trace.jsonl").read_text().splitlines()]
        self.assertEqual([record["id"] for record in records], ["read-1", "write-1"])
        self.assertTrue(all(record["ok"] for record in records))
        self.assertEqual((self.work / "output.txt").read_text(), "synthetic result\n")
        (self.work / "failure-task.json").write_text(json.dumps({"actions": [
            {"id": "unknown-1", "tool": "not_a_tool"},
            {"id": "later-success", "tool": "read_file", "path": "input.txt"},
        ]}))
        args = [sys.executable, "agent_loop.py", "failure-task.json", "failure-trace.jsonl"]
        self.assertEqual(self.run_command(args).returncode, 0)  # stated initial limitation
        path = self.work / "agent_loop.py"
        source = path.read_text().replace('    with trace_path.open(', '    failed = False\n    with trace_path.open(')
        source = source.replace('            trace.write(', '            failed = failed or not record["ok"]\n            trace.write(')
        source = source.replace('    return 0\n', '    return 1 if failed else 0\n')
        path.write_text(source)
        run = self.run_command(args)
        self.assertEqual(run.returncode, 1, run.stderr)
        records = [json.loads(line) for line in (self.work / "failure-trace.jsonl").read_text().splitlines()]
        self.assertEqual([record["ok"] for record in records], [False, True])

    def test_child_status_is_preserved_and_runner_status_is_distinct(self):
        self.copy_lesson("module-04-minimal-agent/lesson-02")
        (self.work / "failure-task.json").write_text(json.dumps({
            "argv": [sys.executable, "-c", "import sys; print('failure-message', file=sys.stderr); sys.exit(7)"]
        }))
        run = self.run_command([sys.executable, "argv_runner.py", "failure-task.json"])
        self.assertEqual(run.returncode, 1)
        result = json.loads(run.stdout)
        self.assertEqual(result["status"], 7)
        self.assertIn("failure-message", result["stderr"])


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class KernelGuidedTests(GuidedWorkspace):
    def test_anchored_writer_creates_and_truncates_exact_payload(self):
        self.copy_lesson("module-05-filesystem-landlock/lesson-02")
        self.compile_source("safe_write.c", "safe-write")
        allowed = self.work / "allowed"
        allowed.mkdir()
        args = ["./safe-write", str(allowed), "created.txt"]
        run = self.run_command(args)
        self.assertEqual(run.returncode, 0, run.stderr)
        expected = "created through an anchored descriptor\n"
        self.assertEqual((allowed / "created.txt").read_text(), expected)
        (allowed / "created.txt").write_text("old" * 100)
        run = self.run_command(args)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((allowed / "created.txt").read_text(), expected)
        self.assertNotEqual(self.run_command(["./safe-write", str(allowed), "../outside.txt"]).returncode, 0)
        self.assertFalse((self.work / "outside.txt").exists())

    def test_landlock_example_keeps_functionality_and_stops_on_descriptor_setup_error(self):
        self.copy_lesson("module-05-filesystem-landlock/lesson-03")
        allowed = self.work / "allowed"
        allowed.mkdir()
        (allowed / "note.txt").write_text("allowed\n")
        self.compile_source("fd_probe.c", "allowed/fd-probe", "-static")
        self.compile_source("landlock_launch.c", "landlock-launch")
        args = ["./landlock-launch", str(allowed), str(allowed / "fd-probe"), "path", str(allowed / "note.txt")]
        run = self.run_command(args)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, "allowed\n")
        path = self.work / "landlock_launch.c"
        source = path.read_text()
        operation = 'return syscall(SYS_close_range, 3U, ~0U, CLOSE_RANGE_CLOEXEC);'
        self.assertIn(operation, source)
        path.write_text(source.replace(operation, 'errno = ENOSYS; return -1;'))
        self.compile_source("landlock_launch.c", "landlock-launch")
        run = self.run_command(args)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, "")
        self.assertIn("close inherited descriptors", run.stderr)

    def test_seccomp_example_reports_effective_state_and_rejects_unknown_mode(self):
        self.copy_lesson("module-06-seccomp/lesson-03")
        flags = self.run_command(["pkg-config", "--cflags", "--libs", "libseccomp"])
        self.assertEqual(flags.returncode, 0, flags.stderr)
        self.compile_source("policy_probe.c", "policy-probe", "-static")
        self.compile_source("allowlist.c", "allowlist", *flags.stdout.split())
        run = self.run_command(["./allowlist", "./policy-probe", "status"])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r"NoNewPrivs:\s+1")
        self.assertRegex(run.stdout, r"Seccomp:\s+2")
        run = self.run_command(["./allowlist", "./policy-probe", "unexpected"])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "result=-1 errno=1")
        self.copy_lesson("module-06-seccomp/lesson-02")
        self.compile_source("deny_socket.c", "deny-socket", *flags.stdout.split())
        run = self.run_command(["./deny-socket", "typo", "/usr/bin/true"])
        self.assertEqual(run.returncode, 2, run.stderr)


if __name__ == "__main__":
    unittest.main()
