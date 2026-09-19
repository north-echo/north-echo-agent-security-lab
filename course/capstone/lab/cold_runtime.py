#!/usr/bin/env python3
"""Runnable batch starter. Direct execution deliberately lacks outer controls."""
import json
from pathlib import Path
import subprocess
import sys

batch = json.loads(Path(sys.argv[1]).read_text())
rows = []
for job in batch["jobs"]:
    spec = job["runtime"]
    run = subprocess.run([spec["guard"], spec["allowed_root"], *spec["command"]],
                         text=True, capture_output=True, timeout=20)
    rows.append({"id": job["id"], "result": {
        "schema": 1, "status": run.returncode, "stdout": run.stdout,
        "stderr": run.stderr, "unit": None, "attestation": None,
    }})
Path(sys.argv[2]).write_text(json.dumps({"schema": 2, "jobs": rows}) + "\n")
raise SystemExit(any(row["result"]["status"] != 0 for row in rows))
