import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SOURCE / "scripts"), str(SOURCE / "graders")]
import capstone
from northecho.grading import evaluate


def reference_source():
    single = (SOURCE / "course/module-10-complete-runtime/lesson-03/complete_runtime.py").read_text()
    single = single.rsplit('if __name__ == "__main__":', 1)[0].replace('def main()', 'def run_single()')
    return single + '''
import tempfile
def main():
    args = sys.argv[:]
    try:
        batch = json.loads(Path(args[1]).read_text())
        if set(batch) != {"schema", "jobs"} or batch["schema"] != 2: return 1
        jobs = batch["jobs"]
        if not isinstance(jobs, list) or not 1 <= len(jobs) <= 8: return 1
        ids = []
        for job in jobs:
            if set(job) != {"id", "runtime"} or not isinstance(job["id"], str) or not job["id"]: return 1
            if set(job["runtime"]) != {"guard", "allowed_root", "command", "memory_max", "tasks_max", "cpu_percent"}: return 1
            validated(job["runtime"])
            ids.append(job["id"])
        if len(set(ids)) != len(ids): return 1
    except (ValueError, TypeError, KeyError, OSError): return 1
    rows = []
    with tempfile.TemporaryDirectory() as raw:
        spec, output = Path(raw) / "spec.json", Path(raw) / "result.json"
        for job in jobs:
            spec.write_text(json.dumps(job["runtime"]))
            output.unlink(missing_ok=True)
            sys.argv = [args[0], str(spec), str(output)]
            run_single()
            rows.append({"id": job["id"], "result": json.loads(output.read_text())})
    sys.argv = args
    Path(args[2]).write_text(json.dumps({"schema": 2, "jobs": rows}))
    return int(any(row["result"]["status"] != 0 for row in rows))
if __name__ == "__main__": raise SystemExit(main())
'''


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux containment")
class CapstoneTests(unittest.TestCase):
    fixture = {"hostname": "cold-test", "canary": "COLD-only"}

    def test_starter_and_unmodified_module_ten_do_not_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            for source in ("course/capstone/lab/cold_runtime.py",
                           "course/module-10-complete-runtime/lesson-03/complete_runtime.py"):
                shutil.copy2(SOURCE / source, work / "cold_runtime.py")
                self.assertFalse(all(c.passed for c in evaluate(capstone, work, self.fixture)))

    def test_independent_batch_composition_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            (work / "cold_runtime.py").write_text(reference_source())
            checks = evaluate(capstone, work, self.fixture)
        self.assertTrue(all(c.passed for c in checks), json.dumps([(c.name, c.passed) for c in checks]))

    def test_early_execution_before_later_validation_is_detected(self):
        eager = '''
        if len(jobs) == 2 and jobs[1].get("runtime", {}).get("tasks_max") == 0:
            early = jobs[0]["runtime"]
            subprocess.run([early["guard"], early["allowed_root"], *early["command"]], timeout=5)
'''
        source = reference_source().replace("        ids = []", eager + "        ids = []")
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw)
            (work / "cold_runtime.py").write_text(source)
            checks = evaluate(capstone, work, self.fixture)
        check = next(c for c in checks if c.name == "A later invalid job prevents earlier guard entry")
        self.assertFalse(check.passed)
