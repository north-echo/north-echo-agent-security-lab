#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 64:
    print("usage: fork_pressure.py COUNT (integer 1..64)", file=sys.stderr)
    raise SystemExit(2)
requested = int(sys.argv[1])
lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
children = []
failure_errno = None
for _ in range(requested):
    try:
        pid = os.fork()
    except OSError as error:
        failure_errno = error.errno
        break
    if pid == 0:
        time.sleep(0.2)
        os._exit(0)
    children.append(pid)
for pid in children:
    os.waitpid(pid, 0)
print(json.dumps({
    "cgroup": relative,
    "requested": requested,
    "created": len(children),
    "failure_errno": failure_errno,
    "pids_max": (base / "pids.max").read_text().strip(),
    "pids_events": (base / "pids.events").read_text(),
}))
