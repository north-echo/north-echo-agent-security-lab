import json
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SOURCE / "scripts"), str(SOURCE / "graders")]
import module_12


class Module12Tests(unittest.TestCase):
    fixture = {"hostname": "grade12", "canary": "GRADE-only"}

    def assess(self, source):
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            (work / "adaptive_runner.py").write_text(source)
            return module_12.grade(work, self.fixture)

    def reference(self):
        return (SOURCE / "course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py").read_text()

    def test_inventory_only_starter_misses_hinted_observations(self):
        source = (SOURCE / "course/module-12-adaptive-adversary/lab/adaptive_runner.py").read_text()
        self.assertFalse(all(check.passed for check in self.assess(source)))

    def test_reference_passes(self):
        checks = self.assess(self.reference())
        self.assertTrue(all(check.passed for check in checks), json.dumps([(c.name, c.passed) for c in checks]))

    def test_unreported_oracle_call_is_detected(self):
        # An extra harmless inventory request leaves the runner's claimed trace
        # unchanged; the independently recorded call sequence must catch it.
        extra_call = '''
spec = json.loads(Path(sys.argv[1]).read_text())
subprocess.run(spec["oracle_command"] + ["inventory"], capture_output=True, timeout=2)
'''
        source = self.reference().replace('if __name__ == "__main__":', extra_call + '\nif __name__ == "__main__":')
        checks = self.assess(source)
        self.assertTrue(any(not c.passed and "Observed oracle calls" in c.name for c in checks))
        self.assertTrue(any(not c.passed and "Trace exactly" in c.name for c in checks))
