#!/usr/bin/env python3
"""Use one inventory observation to choose one bounded focused probe."""
import json, subprocess, sys
from pathlib import Path

ALLOWED = {"inventory", "argv", "credential", "filesystem", "network", "cleanup"}

def main():
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(spec, dict) or set(spec) != {"oracle_command", "budget", "run_id"}:
        return 1
    command, budget = spec["oracle_command"], spec["budget"]
    if not isinstance(command, list) or not command or any(not isinstance(x, str) for x in command):
        return 1
    if type(budget) is not int or not 1 <= budget <= 8 or not isinstance(spec["run_id"], str):
        return 1
    trace = []
    for probe in ("inventory",):
        run = subprocess.run([*command, probe], text=True, capture_output=True, timeout=3, check=False)
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        trace.append({"action": len(trace) + 1, "probe": probe, "observation": observation})
    suggested = trace[0]["observation"].get("next_probe")
    if suggested is not None and budget > 1:
        if suggested not in ALLOWED or suggested == "inventory": return 1
        run = subprocess.run([*command, suggested], text=True, capture_output=True, timeout=3, check=False)
        try: observation = json.loads(run.stdout)
        except json.JSONDecodeError: return 1
        trace.append({"action": 2, "probe": suggested, "observation": observation})
    finding = next((row for row in trace if row["observation"].get("observed") is True), None)
    result = {"schema": 1, "run_id": spec["run_id"], "budget": budget,
              "actions_used": len(trace), "status": "observed" if finding else "not_observed",
              "finding": finding, "claim": "bounded probe observed a synthetic effect" if finding else
              "no effect observed within this bounded probe budget; security is not established", "trace": trace}
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
