#!/usr/bin/env python3
"""Module 10 starter: functional execution without outer runtime controls."""

import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    command = [spec["guard"], spec["allowed_root"], *spec["command"]]
    run = subprocess.run(command, text=True, capture_output=True, check=False)
    Path(sys.argv[2]).write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": None,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": None,
    }) + "\n", encoding="utf-8")
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
