#!/usr/bin/env python3
"""Module 11 starter: repairs only one visible weakness."""

import json
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit(2)
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
plan["controls"]["execution"] = "argv"
Path(sys.argv[2]).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
