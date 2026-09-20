from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from northecho.beginner import prepare
from northecho.catalog import CATALOG, course_dir_name, target_dir_name
from northecho.grading import evaluate, fresh_evaluation_fixture, load_grader, run_bounded


# Reference implementations belong to isolated tests, never student workspaces
# shipped by lab-start. These test behavior, not a required source spelling.
READER = '''import sys
from pathlib import Path
if len(sys.argv) != 2:
    print("one path required", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("cannot read", file=sys.stderr)
    raise SystemExit(1)
print(text, end="")
'''
LAUNCHER = '''import os, subprocess, sys
environment = {"NE_REPORT_STYLE": os.environ["NE_REPORT_STYLE"]}
child = subprocess.run([sys.executable, sys.argv[1], sys.argv[2]], env=environment)
raise SystemExit(child.returncode)
'''


class BeginnerGraderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-beginner-test-")
        self.workspace = Path(self.temp.name)
        (self.workspace / "report.txt").write_text("old report\n")

    def tearDown(self):
        self.temp.cleanup()

    def check_source(self, module, source):
        filename = "read_report.py" if module == "b0" else "launch.py"
        (self.workspace / filename).write_text(source)
        return evaluate(load_grader(ROOT, module), self.workspace,
                        fresh_evaluation_fixture(module + ".lab"))

    def test_valid_readers_pass_fresh_evaluations(self):
        for _ in range(2):
            checks = self.check_source("b0", READER)
            self.assertTrue(all(c.passed for c in checks), checks)
        self.assertFalse(list(self.workspace.glob(".grade-*")))

    def test_reader_starter_and_regressions_fail(self):
        starter = (ROOT / "course/module-b0-basics/lab/read_report.py").read_text()
        for source in (starter, READER.replace("end=\"\"", "end=\"\\n\""),
                       READER.replace("SystemExit(1)", "SystemExit(0)"),
                       READER.replace("sys.argv[1]", '"report.txt"')):
            with self.subTest(source=source):
                self.assertFalse(all(c.passed for c in self.check_source("b0", source)))

    def test_text_reader_scope_does_not_imply_binary_preservation(self):
        source = self.workspace / "read_report.py"
        source.write_text(READER)
        report = self.workspace / "other-newlines.txt"
        report.write_bytes(b"first\r\nsecond\r\n")
        run = run_bounded([sys.executable, str(source), str(report)], text=False)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(run.stdout, b"first\nsecond\n")
        self.assertNotEqual(run.stdout, report.read_bytes())

    def test_valid_launcher_passes_fresh_evaluations(self):
        for _ in range(2):
            checks = self.check_source("b1", LAUNCHER)
            self.assertTrue(all(c.passed for c in checks), checks)
        self.assertFalse(list(self.workspace.glob(".grade-*")))

    def test_launcher_fails_incomplete_environment_repairs(self):
        for environment in ("{}", "dict(os.environ)",
                            '{k: v for k, v in os.environ.items() if k != "NE_PRIVATE_TOKEN"}',
                            '{"NE_REPORT_STYLE": "plain"}'):
            with self.subTest(environment=environment):
                source = LAUNCHER.replace('{"NE_REPORT_STYLE": os.environ["NE_REPORT_STYLE"]}', environment)
                self.assertFalse(all(c.passed for c in self.check_source("b1", source)))

    def test_launcher_output_only_and_swallowed_failure_are_rejected(self):
        for source in ('print("Private setting received: False")\n',
                       LAUNCHER.replace("child.returncode", "0"),
                       LAUNCHER.replace("env=environment", "env=environment, capture_output=True")):
            with self.subTest(source=source):
                self.assertFalse(all(c.passed for c in self.check_source("b1", source)))

    def test_missing_or_malformed_sources_fail_closed(self):
        for module in ("b0", "b1"):
            checks = evaluate(load_grader(ROOT, module), self.workspace,
                              fresh_evaluation_fixture(module + ".lab"))
            self.assertFalse(all(c.passed for c in checks))
            self.assertFalse(all(c.passed for c in self.check_source(module, "not valid python :\n")))


class BeginnerLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-beginner-lifecycle-")
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            ".git", ".student", ".fixtures", ".runtime", ".state", "output",
            "__pycache__", "*.pyc", "dist-*"))
        for name in (".student", ".fixtures", ".runtime", ".state"):
            (self.root / name).mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, command, *arguments, expected=0):
        run = subprocess.run([sys.executable, str(self.root / "scripts/labctl.py"),
                              command, *arguments], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        return run

    def test_all_pilot_targets_resume_replay_and_reset_scopes(self):
        for target in CATALOG:
            if target.startswith(("b0.", "b1.")):
                self.cli("start", target)
                workspace = self.root / ".student" / target
                self.assertTrue((workspace / "README.md").is_file())
                self.assertTrue((workspace / "weekend report.txt").is_file())
        report = self.root / ".student/b0.01/report.txt"
        first = report.read_text()
        report.write_text("student edit")
        self.cli("start", "b0.01")
        self.assertEqual(report.read_text(), "student edit")
        self.cli("reset", "b0.01", "--dry-run")
        self.assertEqual(report.read_text(), "student edit")
        self.cli("reset", "b0.01", "--yes")
        self.assertFalse(report.exists())
        self.cli("start", "b0.01")
        self.assertNotEqual(report.read_text(), first)
        self.cli("reset", "module-b0", "--yes")
        self.assertFalse(list((self.root / ".student").glob("b0.*")))
        self.assertTrue((self.root / ".student/b1.01").exists())
        self.cli("reset", "--all", "--yes")
        for name in (".student", ".fixtures", ".runtime"):
            self.assertEqual(list((self.root / name).iterdir()), [])
        self.assertNotIn("student edit", (self.root / ".state/progress.json").read_text())

    def test_starter_feedback_reference_pass_and_exam_reduction(self):
        for module, filename, solution in (("b0", "read_report.py", READER),
                                            ("b1", "launch.py", LAUNCHER)):
            target = "module-" + module
            self.cli("start", target)
            practice = self.cli("grade", target, expected=1)
            exam = self.cli("grade", target, "--mode", "exam", expected=1)
            self.assertIn("NOT PASSED", practice.stdout)
            self.assertGreater(len(practice.stdout), len(exam.stdout))
            workspace = self.root / ".student" / (module + ".lab")
            (workspace / filename).write_text(solution)
            self.assertIn("RESULT: PASSED", self.cli("grade", target).stdout)
            self.assertIn("RESULT: PASSED", self.cli("grade", target, "--mode", "exam").stdout)
            self.cli("reset", target, "--yes")
            self.assertFalse(workspace.exists())
        self.assertNotIn("subprocess.run", (self.root / ".state/progress.json").read_text())

    def test_beginner_tamper_blocks_start(self):
        source = self.root / "course/module-b1-first-boundary/lesson-01/read_report.py"
        source.write_text("print('changed')\n")
        self.assertIn("changed canonical file", self.cli("start", "b1.01", expected=2).stderr)


class BeginnerGuidedTests(unittest.TestCase):
    def test_documented_observations_and_repairs(self):
        with tempfile.TemporaryDirectory(prefix="ne-guided-") as raw:
            root = Path(raw)
            for target in ("b0.01", "b0.02", "b0.03", "b1.01", "b1.02", "b1.03"):
                module = target.split(".")[0]
                workspace = root / target
                shutil.copytree(ROOT / "course" / course_dir_name(module) / target_dir_name(target), workspace)
                prepare(workspace, target, {"synthetic_user": "student-test", "fixture_id": "synthetic-123"})
            directory = root / "b0.01/notes"
            self.assertFalse((directory / "report.txt").exists())
            self.assertIn("One parcel", (directory / "../weekend report.txt").read_text())
            for arguments, code in (([], 0), (["fail"], 7)):
                run = run_bounded([sys.executable, "identify.py", *arguments], cwd=root / "b0.02")
                self.assertEqual(run.returncode, code)
                self.assertIn("Process ID:", run.stdout)
            directory = root / "b0.03"
            run = run_bounded([sys.executable, "read_report.py", "weekend report.txt"], cwd=directory)
            self.assertIn("Three parcels", run.stdout)
            source = directory / "read_report.py"
            source.write_text(source.read_text().replace('Path("report.txt")', "Path(sys.argv[1])"))
            run = run_bounded([sys.executable, "read_report.py", "weekend report.txt"], cwd=directory)
            self.assertIn("One parcel", run.stdout)
            for args, code in ((["absent.txt"], 1), (["."], 1), ([], 2)):
                self.assertEqual(run_bounded([sys.executable, "read_report.py", *args], cwd=directory).returncode, code)
            for private, expected in (({}, "False"), ({"NE_PRIVATE_TOKEN": "pretend-red"}, "True"),
                                      ({"NE_PRIVATE_TOKEN": ""}, "True")):
                run = run_bounded([sys.executable, "read_report.py", "report.txt"], cwd=root / "b1.01", env=private)
                self.assertIn("received: " + expected, run.stdout)
            env = {"NE_REPORT_STYLE": "upper", "NE_PRIVATE_TOKEN": "pretend-red", "NE_OTHER_PRIVATE": "pretend-blue"}
            for target, worker_args in (("b1.02", []), ("b1.03", ["inspect_reader.py"])):
                directory = root / target
                source = directory / "launch.py"
                initial = source.read_text()
                argv = [sys.executable, "launch.py", *worker_args, "weekend report.txt"]
                run = run_bounded(argv, cwd=directory, env=env)
                self.assertIn("received: True", run.stdout)
                if target == "b1.02":
                    source.write_text(initial.replace("dict(os.environ)", "{}"))
                    empty = run_bounded(argv, cwd=directory, env=env)
                    self.assertEqual(empty.returncode, 2)
                    self.assertEqual(empty.stdout, "")  # no observation is not observed False
                    self.assertIn("NE_REPORT_STYLE", empty.stderr)
                source.write_text(initial.replace("dict(os.environ)", '{"NE_REPORT_STYLE": os.environ["NE_REPORT_STYLE"]}'))
                for style in ("plain", "upper"):
                    env["NE_REPORT_STYLE"] = style
                    run = run_bounded(argv, cwd=directory, env=env)
                    self.assertEqual(run.returncode, 0)
                    self.assertNotIn("received: True", run.stdout)
                    self.assertIn("ONE PARCEL" if style == "upper" else "One parcel", run.stdout)
                argv[-1] = "absent.txt"
                self.assertEqual(run_bounded(argv, cwd=directory, env=env).returncode, 1)


class BeginnerDocumentationTests(unittest.TestCase):
    def test_each_guided_source_has_read_access_before_its_listing(self):
        # Mechanical guard for the reported omission, not a pedagogy evaluator.
        with tempfile.TemporaryDirectory(prefix="ne-source-access-") as raw:
            for readme in sorted((ROOT / "course").glob("module-b*/lesson-*/README.md")):
                text = readme.read_text()
                workspace = Path(raw) / readme.parent.parent.name / readme.parent.name
                shutil.copytree(readme.parent, workspace)
                for source in workspace.glob("*.py"):
                    relative = (readme.parent / source.name).relative_to(ROOT).as_posix()
                    marker = "<!-- source: " + relative + " format=code -->"
                    self.assertIn(marker, text)
                    before = text[:text.index(marker)]
                    blocks = re.findall(r"```bash\n(.*?)```", before, flags=re.DOTALL)
                    commands = [line.strip() for block in blocks for line in block.splitlines()]
                    self.assertIn("pwd", commands)
                    self.assertIn("cat " + source.name, commands)
                    self.assertTrue(any(line.startswith("ls -l ") and source.name in line.split()
                                        for line in commands), str(source))
                    listed = run_bounded(["ls", "-l", source.name], cwd=workspace)
                    displayed = run_bounded(["cat", source.name], cwd=workspace)
                    self.assertEqual(listed.returncode, 0)
                    self.assertEqual(displayed.returncode, 0)
                    self.assertEqual(displayed.stdout, source.read_text())

    def test_each_pilot_lesson_and_lab_has_sources_and_scope(self):
        # Human review in BEGINNER_SOURCE_REVIEW.md establishes relevance;
        # this assertion only prevents accidental removal of that documentation.
        for readme in sorted((ROOT / "course").glob("module-b*/*/README.md")):
            text = readme.read_text()
            self.assertIn("## Sources and scope", text, str(readme))
            section = text.split("## Sources and scope", 1)[1]
            self.assertRegex(section, r"\]\(https://[^)]+\)")
        b0 = (ROOT / "course/module-b0-basics/lab/README.md").read_text()
        b1 = (ROOT / "course/module-b1-first-boundary/lab/README.md").read_text()
        self.assertIn("Unix LF", b0)
        self.assertIn("Signal forwarding is outside", b1)
