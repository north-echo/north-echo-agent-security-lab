#!/usr/bin/env python3
"""Synthetic one-weakness oracle: JSON scenario plus one named probe."""
import json, sys
from pathlib import Path

PROBES = ("argv", "credential", "filesystem", "network", "cleanup")
if len(sys.argv) != 3 or sys.argv[2] not in ("inventory", *PROBES):
    raise SystemExit(2)
scenario = json.loads(Path(sys.argv[1]).read_text())
weakness = scenario.get("weakness")
probe = sys.argv[2]
if probe == "inventory":
    value = {"ok": True, "surface": list(PROBES), "next_probe": weakness}
else:
    value = {"ok": True, "probe": probe, "observed": probe == weakness,
             "evidence": f"synthetic-{probe}-effect" if probe == weakness else None}
print(json.dumps(value, sort_keys=True))
