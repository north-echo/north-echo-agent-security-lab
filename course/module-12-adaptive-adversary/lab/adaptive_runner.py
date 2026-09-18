#!/usr/bin/env python3
"""Module 12 starter: inventory only, with a calibrated non-discovery claim."""
import json, subprocess, sys
from pathlib import Path

if len(sys.argv) != 3: raise SystemExit(2)
spec = json.loads(Path(sys.argv[1]).read_text())
run = subprocess.run([*spec["oracle_command"], "inventory"], text=True, capture_output=True)
observation = json.loads(run.stdout)
Path(sys.argv[2]).write_text(json.dumps({"schema":1,"run_id":spec["run_id"],"budget":spec["budget"],
 "actions_used":1,"status":"not_observed","finding":None,
 "claim":"no effect observed within this bounded probe budget; security is not established",
 "trace":[{"action":1,"probe":"inventory","observation":observation}]})+"\n")
