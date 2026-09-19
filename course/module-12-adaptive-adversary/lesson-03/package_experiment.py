#!/usr/bin/env python3
"""Bundle explicit local inputs and sources for replay from a clean directory."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: package_experiment.py RESULT SPEC RUNNER CANDIDATE_ID DIRECTORY")
    result_path, spec_path, runner = map(Path, sys.argv[1:4])
    result = json.loads(result_path.read_text())
    spec = json.loads(spec_path.read_text())
    command = spec["oracle_command"]
    if not isinstance(command, list) or len(command) != 3:
        raise SystemExit("packaging supports only the explicit local Python oracle plus scenario interface")
    oracle, scenario = map(Path, command[1:])
    trace = result.get("trace", [])
    if (result.get("schema") != 1 or result.get("status") not in {"observed", "not_observed"}
            or result.get("run_id") != spec["run_id"]
            or result.get("actions_used") != len(trace) or not 1 <= len(trace) <= spec["budget"]):
        raise SystemExit("invalid result, run identity, or budget")
    files = {"runner.py": runner.read_bytes(), "oracle.py": oracle.read_bytes(),
             "scenario.json": scenario.read_bytes(), "expected.json": result_path.read_bytes()}
    portable = dict(spec, oracle_command=["python3", "oracle.py", "scenario.json"])
    files["spec.json"] = (json.dumps(portable, indent=2, sort_keys=True) + "\n").encode()
    package = {"schema": 2, "candidate_id": sys.argv[4], "run_id": spec["run_id"],
               "hypothesis": "The recorded local scenario permits the reported observation within this budget.",
               "result_status": result["status"], "claim": result["claim"],
               "limits": ["synthetic local oracle", "single run", "bounded probe set", "non-discovery is not proof"],
               "replay": ["python3", "runner.py", "spec.json", "result.json"],
               "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    output = Path(sys.argv[5])
    output.mkdir()  # Never overwrite an existing experiment or student work.
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "package.json").write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
