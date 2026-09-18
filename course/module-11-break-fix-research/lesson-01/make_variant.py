#!/usr/bin/env python3
"""Create a reproducible vulnerable plan from an explicit integer seed."""

import json
import random
import sys
from pathlib import Path

SECURE = {"execution": "argv", "environment": "minimal", "filesystem": "resolved",
          "network": "broker_only", "cleanup": "owned"}
WEAK = {"execution": "shell", "environment": "inherit", "filesystem": "lexical",
        "network": "direct", "cleanup": "prefix"}

if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} SEED OUTPUT.json")
rng = random.Random(int(sys.argv[1]))
controls = dict(SECURE)
for name in rng.sample(sorted(WEAK), rng.randint(2, 4)):
    controls[name] = WEAK[name]
plan = {
    "schema": 1,
    "variant_id": f"seed-{sys.argv[1]}",
    "workload": {"operation": "read", "resource": "record:alpha",
                 "literal": "literal $(touch shell-marker)"},
    "controls": controls,
}
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
