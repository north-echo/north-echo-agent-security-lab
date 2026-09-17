#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path

relative = next(line.split("::", 1)[1].strip() for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
children = []
for _ in range(int(sys.argv[1])):
    try:
        pid = os.fork()
    except OSError:
        break
    if pid == 0:
        time.sleep(0.2); os._exit(0)
    children.append(pid)
for pid in children:
    os.waitpid(pid, 0)
print(json.dumps({"created": len(children), "pids_max": (base / "pids.max").read_text().strip(), "pids_events": (base / "pids.events").read_text()}))
