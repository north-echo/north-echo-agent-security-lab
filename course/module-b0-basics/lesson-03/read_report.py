import sys
from pathlib import Path

if len(sys.argv) != 2:
    print("usage: python3 read_report.py REPORT", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path("report.txt").read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
print(text, end="")
