import os
import subprocess
import sys

child_environment = dict(os.environ)
result = subprocess.run(
    [sys.executable, "read_report.py", sys.argv[1]],
    env=child_environment,
)
raise SystemExit(result.returncode)
