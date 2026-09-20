#!/usr/bin/env python3
"""Run the same fixed probes in the same order for every scenario."""
import json, subprocess, sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit(2)
oracle, scenario, output = sys.argv[1:]
trace = []
for probe in ("argv", "credential", "filesystem"):
    run = subprocess.run([sys.executable, oracle, scenario, probe], text=True,
                         capture_output=True, check=True, timeout=3)
    observation = json.loads(run.stdout)
    trace.append({"probe": probe, "observation": observation})
finding = next((row for row in trace if row["observation"].get("observed")), None)
Path(output).write_text(json.dumps({"strategy": "scripted", "status": "observed" if finding else "not_observed",
                                   "trace": trace}, indent=2, sort_keys=True) + "\n")
