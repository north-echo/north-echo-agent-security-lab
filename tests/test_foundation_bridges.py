"""Execute the foundation bridges and the deliberately incomplete variants."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class FoundationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-foundation-")
        self.work = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def run_command(self, argv, **kwargs):
        return subprocess.run(argv, cwd=self.work, text=True, capture_output=True,
                              timeout=10, **kwargs)

    def compile_source(self, relative, transform=None):
        source = (ROOT / relative).read_text()
        if transform:
            source = transform(source)
        local = self.work / "example.c"
        local.write_text(source)
        binary = self.work / "example"
        run = self.run_command(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                                "-O2", str(local), "-o", str(binary)])
        self.assertEqual(run.returncode, 0, run.stderr)
        return str(binary)

    def require_namespace(self):
        run = self.run_command(["unshare", "--user", "--map-root-user", "true"])
        if run.returncode:
            self.skipTest("unprivileged user namespaces unavailable: " + run.stderr)

    def test_explicit_environment_excludes_unknown_inputs(self):
        binary = self.compile_source("course/module-01-process-authority/lesson-02/clean-env.c")
        env = dict(os.environ, NE_LAB_TOKEN="synthetic", NE_OTHER_INPUT="synthetic")
        run = self.run_command([binary], env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(set(run.stdout.splitlines()), {"PATH=/usr/bin:/bin", "LANG=C.UTF-8"})

    def test_descriptor_closure_and_missing_control(self):
        source = "course/module-01-process-authority/lesson-03/close-extra.c"
        binary = self.compile_source(source)
        run = self.run_command([binary])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("stdout still works", run.stdout)
        block = '''    if (close_range(3, ~0U, 0) != 0) {
        perror("close_range");
        return 1;
    }
'''
        self.assertIn(block, (ROOT / source).read_text())
        binary = self.compile_source(source, lambda text: text.replace(block, ""))
        run = self.run_command([binary])
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Expected the descriptor to be closed", run.stderr)

    def test_capability_clear_is_not_just_an_already_empty_input(self):
        self.require_namespace()
        source = "course/module-03-privilege/lesson-02/clear-current.c"
        binary = self.compile_source(source)
        for prefix in ([], ["unshare", "--user", "--map-root-user"]):
            run = self.run_command([*prefix, binary])
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(dict(line.split("=") for line in run.stdout.splitlines()),
                             {key: "0" * 16 for key in ("effective", "permitted", "inheritable")})
        block = '''    if (syscall(SYS_capset, &header, data) != 0) {
        perror("capset");
        return 1;
    }
'''
        self.assertIn(block, (ROOT / source).read_text())
        binary = self.compile_source(source, lambda text: text.replace(block, ""))
        run = self.run_command(["unshare", "--user", "--map-root-user", binary])
        self.assertEqual(run.returncode, 0, run.stderr)
        masks = dict(line.split("=") for line in run.stdout.splitlines())
        self.assertNotEqual(int(masks["effective"], 16), 0)
        self.assertNotEqual(int(masks["permitted"], 16), 0)

    def test_guided_namespace_capability_command_is_valid_as_written(self):
        self.require_namespace()
        lesson = (ROOT / "course/module-03-privilege/lesson-01/README.md").read_text()
        blocks = re.findall(r"```bash\n(.*?)\n```", lesson, re.S)
        commands = [block for block in blocks if "unshare" in block]
        self.assertEqual(len(commands), 1)
        run = self.run_command(["bash", "-c", commands[0]])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("uid=0", run.stdout)
        self.assertIn("CapEff:", run.stdout)
        self.assertNotIn("awk:", run.stderr)

    def test_guided_pid_wait_collects_the_intentional_status(self):
        self.require_namespace()
        lesson = (ROOT / "course/module-02-namespaces/lesson-03/README.md").read_text()
        block, = [block for block in re.findall(r"```bash\n(.*?)\n```", lesson, re.S)
                  if 'wait "$child"' in block]
        run = self.run_command(["bash", "-c", block])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r"waited for child=\d+ status=7")

    def test_guided_argument_vector_keeps_spaces_and_exposes_unquoted_failure(self):
        lesson = (ROOT / "course/module-02-namespaces/lesson-02/README.md").read_text()
        block, = [block for block in re.findall(r"```bash\n(.*?)\n```", lesson, re.S)
                  if "NE_PRACTICE_LABEL=example" in block]
        run = self.run_command(["bash", "-c", block])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.splitlines()[-2:], ["<two words>", "<final>"])
        run = self.run_command(["bash", "-c", block.replace('exec "$@"', 'exec $@')])
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.splitlines()[-3:], ["<two>", "<words>", "<final>"])


if __name__ == "__main__":
    unittest.main()
