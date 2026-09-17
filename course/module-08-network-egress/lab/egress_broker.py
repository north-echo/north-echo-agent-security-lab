#!/usr/bin/env python3
"""Starter: validate arguments, but do not expose an unmediated fallback."""

import sys

if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
    raise SystemExit(2)
print("broker policy is not implemented", file=sys.stderr)
raise SystemExit(1)
