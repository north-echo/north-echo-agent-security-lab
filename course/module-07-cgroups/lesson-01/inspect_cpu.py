#!/usr/bin/env python3
import json, time
from pathlib import Path

relative = next(line.split("::", 1)[1].strip() for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
base = Path("/sys/fs/cgroup") / relative.lstrip("/")
before = (base / "cpu.stat").read_text()
end = time.monotonic() + 1.0
count = 0
while time.monotonic() < end:
    count += 1
print(json.dumps({"cgroup": relative, "cpu_max": (base / "cpu.max").read_text().strip(), "iterations": count, "cpu_stat_before": before}))
