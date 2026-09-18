#!/usr/bin/env python3
"""Package a runner result as a replayable candidate experiment."""
import json, sys
from pathlib import Path

if len(sys.argv) != 4: raise SystemExit(2)
result = json.loads(Path(sys.argv[1]).read_text())
if result.get("schema") != 1 or result.get("status") not in {"observed", "not_observed"}:
    raise SystemExit("invalid result")
package = {"schema": 1, "candidate_id": sys.argv[2],
           "hypothesis": "a bounded focused probe can reproduce the indicated synthetic boundary effect",
           "result_status": result["status"], "claim": result["claim"], "trace": result["trace"],
           "limits": ["synthetic local oracle", "single run", "bounded probe set", "non-discovery is not proof"],
           "replay": ["python3", "adaptive_runner.py", "SPEC.json", "RESULT.json"]}
Path(sys.argv[3]).write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
