import hashlib
import runpy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "course/module-12-adaptive-adversary"


class EvidenceTests(unittest.TestCase):
    def test_incomplete_evidence_is_not_a_pass(self):
        reviewer = runpy.run_path(str(MODULE / "lesson-02/review_evidence.py"))
        cases = json.loads((MODULE / "lesson-02/evidence-cases.json").read_text())
        self.assertEqual([reviewer["review"](case)["status"] for case in cases],
                         ["passed_observations", "observed_failure", "inconclusive", "inconclusive"])
        cases[0]["case_id"] = "misleading-name"
        self.assertEqual(reviewer["review"](cases[0])["status"], "passed_observations")

    def test_package_replays_from_a_separate_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            runner = MODULE / "lesson-02/adaptive_runner.py"
            spec = {"oracle_command": [sys.executable, str(MODULE / "lesson-01/local_oracle.py"),
                                        str(MODULE / "lesson-01/network-scenario.json")],
                    "budget": 2, "run_id": "synthetic-replay"}
            (work / "spec.json").write_text(json.dumps(spec))
            subprocess.run([sys.executable, str(runner), "spec.json", "original.json"], cwd=work, check=True, timeout=10)
            packager = MODULE / "lesson-03/package_experiment.py"
            subprocess.run([sys.executable, str(packager), "original.json", "spec.json", str(runner), "example", "package"], cwd=work, check=True, timeout=10)
            portable = work / "relocated"
            (work / "package").rename(portable)
            subprocess.run([sys.executable, "runner.py", "spec.json", "result.json"], cwd=portable, check=True, timeout=10)
            self.assertEqual(json.loads((portable / "expected.json").read_text()),
                             json.loads((portable / "result.json").read_text()))
            manifest = json.loads((portable / "package.json").read_text())
            self.assertNotIn(str(ROOT), json.dumps(manifest))
            for name, digest in manifest["sha256"].items():
                self.assertEqual(hashlib.sha256((portable / name).read_bytes()).hexdigest(), digest)
