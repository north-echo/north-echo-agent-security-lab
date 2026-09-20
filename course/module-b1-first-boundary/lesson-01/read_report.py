import os
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
print(text, end="")
print("Private setting received:", "NE_PRIVATE_TOKEN" in os.environ)
