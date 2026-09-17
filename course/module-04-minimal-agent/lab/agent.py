#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} TASK.json TRACE.jsonl", file=sys.stderr)
        return 2
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    trace = Path(sys.argv[2])
    records = []
    for action in task.get("actions", []):
        if action.get("tool") == "run_argv":
            command = " ".join(action["argv"])
            run = subprocess.run(command, shell=True, text=True, capture_output=True, env=os.environ.copy())
            records.append({"id": action.get("id"), "tool": "run_argv", "ok": run.returncode == 0, "status": run.returncode, "stdout": run.stdout})
    trace.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
