#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    run = subprocess.run(spec["command"], text=True, capture_output=True, check=False)
    Path(sys.argv[2]).write_text(
        json.dumps({"status": run.returncode, "stdout": run.stdout, "stderr": run.stderr}) + "\n",
        encoding="utf-8",
    )
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
