import os
import sys
from pathlib import Path

style = os.environ.get("NE_REPORT_STYLE")
if style not in ("plain", "upper"):
    print("The reader needs NE_REPORT_STYLE=plain or upper.", file=sys.stderr)
    raise SystemExit(2)
try:
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
except OSError:
    print("Could not read that report.", file=sys.stderr)
    raise SystemExit(1)
if style == "upper":
    text = text.upper()
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
