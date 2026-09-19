"""Transfer assessment: ordered batches, independent limits, failure recovery."""
import importlib.util
import json
import os
import secrets
import shutil
import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, result_object, run_bounded

spec = importlib.util.spec_from_file_location("capstone_kernel_checks", Path(__file__).with_name("module_10.py"))
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "cold_runtime.py"
    if not source.is_file():
        return [Check("A batch runtime implementation is present", False)]
    checks = []
    with tempfile.TemporaryDirectory(prefix="ne-capstone-") as raw:
        work = Path(raw)
        student = work / "cold_runtime.py"
        shutil.copy2(source, student)
        # Adapt trusted kernel assertions to the new learner batch protocol.
        adapter = work / "complete_runtime.py"
        adapter.write_text(
            "import json,subprocess,sys\nfrom pathlib import Path\n"
            "p=Path(sys.argv[1]); q=Path(sys.argv[2])\n"
            "b=p.with_suffix('.batch'); r=q.with_suffix('.batch-result')\n"
            "b.write_text(json.dumps({'schema':2,'jobs':[{'id':'single','runtime':json.loads(p.read_text())}]}))\n"
            f"run=subprocess.run([sys.executable,{str(student)!r},str(b),str(r)],timeout=23)\n"
            "if r.exists():\n"
            " value=json.loads(r.read_text())\n"
            " if value.get('schema')==2 and len(value.get('jobs',[]))==1 and value['jobs'][0].get('id')=='single':\n"
            "  q.write_text(json.dumps(value['jobs'][0]['result']))\n"
            "sys.exit(run.returncode)\n"
        )
        for index, profile in enumerate((
            {"memory_max": 67108864, "tasks_max": 12, "cpu_percent": 30},
            {"memory_max": 100663296, "tasks_max": 24, "cpu_percent": 70},
        ), 1):
            case = dict(fixture, runtime_profile=profile)
            checks.extend(Check(f"Profile {index}: {c.name}", c.passed) for c in kernel.grade(work, case))
        allowed = work / "allowed"
        allowed.mkdir()
        worker_c = work / "worker.c"
        worker_c.write_text('#include <stdlib.h>\n#include <stdio.h>\nint main(int n,char **v){puts("batch-work");return n>1?atoi(v[1]):0;}\n')
        worker, guard = allowed / "worker", work / "guard"
        canonical = Path(__file__).resolve().parents[1] / "course/module-10-complete-runtime/lesson-02/runtime_guard.c"
        if not kernel._compile(worker_c, worker) or not kernel._compile(canonical, guard, "-lseccomp"):
            return checks + [Check("Batch workload compiles", False)]
        jobs = []
        ids = [secrets.token_hex(4) for _ in range(3)]
        for identity, status in zip(ids, (0, 7, 0)):
            jobs.append({"id": identity, "runtime": {
                "guard": str(guard), "allowed_root": str(allowed),
                "command": [str(worker), str(status)], "memory_max": 67108864,
                "tasks_max": 16, "cpu_percent": 40,
            }})
        batch, output = work / "batch.json", work / "result.json"
        batch.write_text(json.dumps({"schema": 2, "jobs": jobs}))
        run = run_bounded([sys.executable, str(student), str(batch), str(output)], timeout=70)
        result = result_object(output)
        rows = result.get("jobs", [])
        checks.append(Check("Ordered jobs preserve identity and continue after a failure",
                            run.returncode != 0 and result.get("schema") == 2 and
                            [row.get("id") for row in rows] == ids and
                            [row.get("result", {}).get("status") for row in rows] == [0, 7, 0]))
        unit_names = [row.get("result", {}).get("unit") for row in rows]
        checks.append(Check("Each job has a distinct owned unit",
                            len(unit_names) == 3 and all(isinstance(unit, str) for unit in unit_names) and
                            len(set(unit_names)) == 3))
        bad_runtime = dict(jobs[1], runtime=dict(jobs[1]["runtime"], tasks_max=0))
        invalid_cases = (
            ("duplicate identity", [jobs[0], jobs[0]]),
            ("empty batch", []),
            ("oversized batch", [dict(jobs[0], id=str(index)) for index in range(9)]),
            ("extra job field", [dict(jobs[0], unexpected=True)]),
            ("empty identity", [dict(jobs[0], id="")]),
            ("later runtime", [jobs[0], bad_runtime]),
        )
        for label, invalid in invalid_cases:
            batch.write_text(json.dumps({"schema": 2, "jobs": invalid}))
            output.unlink(missing_ok=True)
            run = run_bounded([sys.executable, str(student), str(batch), str(output)], timeout=10)
            checks.append(Check(f"Invalid {label} is rejected without a result", run.returncode != 0 and not output.exists()))
        units = run_bounded(["systemctl", "--user", "list-units", "--all", "--plain", "--no-legend",
                             f"north-echo-{os.getuid()}-10-lab-*.service"])
        checks.append(Check("Batch completion leaves no runtime unit", units.returncode == 0 and not units.stdout.strip()))
    return checks
