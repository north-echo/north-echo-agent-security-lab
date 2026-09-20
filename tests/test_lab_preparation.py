"""Follow independent-lab preparation commands, excluding the interactive editor."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LabPreparationTests(unittest.TestCase):
    def test_every_lab_preparation_enters_its_actual_workspace(self):
        with tempfile.TemporaryDirectory(prefix="ne-lab-preparation-") as raw:
            root = Path(raw) / "repo"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(
                ".git", ".student", ".fixtures", ".runtime", ".state",
                "__pycache__", "*.pyc", "output", "dist-*"))
            readmes = sorted((root / "course").glob("*/lab/README.md"))
            self.assertEqual(len(readmes), 15)
            for path in readmes:
                with self.subTest(lab=path.parent.parent.name):
                    blocks = re.findall(r"```bash\n(.*?)\n```", path.read_text(), re.S)
                    prepare = blocks[0]
                    self.assertIn("./lab-start ", prepare)
                    command = "\n".join(line for line in prepare.splitlines()
                                        if not line.startswith("nano "))
                    command += '\npython3 -c "from pathlib import Path; assert Path(\'.north-echo.json\').is_file(); print(Path.cwd().name)"'
                    run = subprocess.run(["bash", "-e", "-c", command], cwd=root,
                                         capture_output=True, text=True, timeout=15)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    name = path.parent.parent.name
                    expected = "capstone" if name == "capstone" else name.split("-")[1] + ".lab"
                    self.assertEqual(run.stdout.splitlines()[-1], expected)


if __name__ == "__main__":
    unittest.main()
