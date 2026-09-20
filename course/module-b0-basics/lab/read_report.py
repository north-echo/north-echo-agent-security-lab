import sys
from pathlib import Path

# A running but incomplete starting point. Read the lab contract before editing.
text = Path("report.txt").read_text(encoding="utf-8")
print(text, end="")
