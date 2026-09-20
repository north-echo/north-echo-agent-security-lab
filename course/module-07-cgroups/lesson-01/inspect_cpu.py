#!/usr/bin/env python3
import json
import time
from pathlib import Path

lines = Path("/proc/self/cgroup").read_text().splitlines()
relative = next(line.split("::", 1)[1] for line in lines if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
before = (base / "cpu.stat").read_text()
end = time.monotonic() + 1.0
count = 0
while time.monotonic() < end:
    count += 1
after = (base / "cpu.stat").read_text()
print(json.dumps({
    "cgroup": relative,
    "cpu_max": (base / "cpu.max").read_text().strip(),
    "iterations": count,
    "cpu_stat_before": before,
    "cpu_stat_after": after,
}))
