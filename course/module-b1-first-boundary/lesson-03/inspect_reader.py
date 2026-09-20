import os
import sys
from pathlib import Path

style = os.environ.get("NE_REPORT_STYLE")
if style not in ("plain", "upper"):
    print("Missing or invalid report style.", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
if style == "upper":
    text = text.upper()
print(text, end="")
print("Original private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
print("New private setting received:", "NE_OTHER_PRIVATE" in os.environ)
