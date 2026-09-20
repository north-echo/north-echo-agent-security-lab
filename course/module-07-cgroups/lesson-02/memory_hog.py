#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

if len(sys.argv) != 2 or not sys.argv[1].isdigit() or not 1 <= int(sys.argv[1]) <= 96:
    print("usage: memory_hog.py MIB (integer 1..96)", file=sys.stderr)
    raise SystemExit(2)
mebibytes = int(sys.argv[1])
lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
print(json.dumps({
    "cgroup": relative,
    "memory_max": (base / "memory.max").read_text().strip(),
    "memory_swap_max": (base / "memory.swap.max").read_text().strip(),
    "requested_mib": mebibytes,
}), flush=True)
blocks = []
for index in range(mebibytes):
    blocks.append(bytearray(1024 * 1024))
    if index % 8 == 0:
        print(f"allocated_mib={index + 1}", flush=True)
print("allocation completed", flush=True)
time.sleep(1)
