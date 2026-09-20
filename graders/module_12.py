"""Assess a bounded synthetic oracle protocol using independently recorded calls."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, evaluate, result_object, run_bounded

ORACLE = '''import json, sys
from pathlib import Path
weakness, log, probe = sys.argv[1:]
allowed = ["argv", "credential", "filesystem", "network", "cleanup"]
if probe == "inventory":
    result = {"ok": True, "surface": allowed, "next_probe": None if weakness == "none" else weakness}
elif probe in allowed:
    result = {"ok": True, "probe": probe, "observed": probe == weakness,
              "evidence": "synthetic-" + probe + "-effect" if probe == weakness else None}
else:
    result = {"ok": False}
with Path(log).open("a") as stream:
    stream.write(json.dumps({"probe": probe, "observation": result}) + "\\n")
print(json.dumps(result))
'''


def _grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "adaptive_runner.py"
    if not source.is_file():
        return [Check("An adaptive runner is present", False, "Module 12 lab contract")]
    values = dict.fromkeys(("valid", "budget", "discover", "allowed", "trace", "calibrated", "deterministic", "preserve"), True)
    with tempfile.TemporaryDirectory(prefix="ne12-") as raw:
        work = Path(raw)
        agent, oracle = work / "runner.py", work / "oracle.py"
        shutil.copy2(source, agent)
        oracle.write_text(ORACLE)
        for weakness in ("argv", "credential", "filesystem", "network", "cleanup", "none"):
            log, spec_path, output = work / "calls.jsonl", work / "spec.json", work / "result.json"
            spec = {"oracle_command": [sys.executable, str(oracle), weakness, str(log)],
                    "budget": 2, "run_id": f"{fixture['hostname']}-{weakness}"}
            spec_path.write_text(json.dumps(spec))
            original = spec_path.read_bytes()
            results = []
            for _ in range(2):
                log.unlink(missing_ok=True)
                output.unlink(missing_ok=True)
                run = run_bounded([sys.executable, str(agent), str(spec_path), str(output)], timeout=8)
                result = result_object(output)
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                trace = result.get("trace", [])
                expected_trace = [dict(call, action=index) for index, call in enumerate(calls, 1)]
                values["valid"] &= run.returncode == 0 and result.get("schema") == 1
                values["budget"] &= 1 <= len(calls) <= spec["budget"] and result.get("actions_used") == len(calls)
                values["allowed"] &= all(call["probe"] in {"inventory", "argv", "credential", "filesystem", "network", "cleanup"} for call in calls)
                values["trace"] &= trace == expected_trace and bool(calls) and calls[0]["probe"] == "inventory"
                values["preserve"] &= spec_path.read_bytes() == original and result.get("run_id") == spec["run_id"]
                if weakness == "none":
                    values["calibrated"] &= result.get("status") == "not_observed" and "not established" in result.get("claim", "") and result.get("finding") is None
                else:
                    finding = result.get("finding")
                    values["discover"] &= result.get("status") == "observed" and isinstance(finding, dict) and finding in expected_trace and finding.get("probe") == weakness and finding.get("observation", {}).get("observed") is True
                results.append(result)
            values["deterministic"] &= results[0] == results[1]
    labels = {
        "valid": "Results are structured", "preserve": "Run identity and input are preserved",
        "budget": "Observed oracle calls respect the two-action budget",
        "discover": "Every supplied synthetic hint is followed within budget",
        "allowed": "Only allowlisted oracle calls are observed",
        "trace": "Trace exactly matches independently recorded observations",
        "calibrated": "Non-discovery is explicitly not a security claim",
        "deterministic": "Identical inputs produce identical results",
    }
    return [Check(label, bool(values[key]), "Module 12 lessons 01-03") for key, label in labels.items()]


def grade(workspace: Path, fixture: dict) -> list[Check]:
    from types import SimpleNamespace
    return evaluate(SimpleNamespace(grade=_grade), workspace, fixture)
