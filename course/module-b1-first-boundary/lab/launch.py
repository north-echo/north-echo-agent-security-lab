import os
import subprocess
import sys

# Intentionally copies more than the reader requires.
child_environment = dict(os.environ)
result = subprocess.run(
    [sys.executable, sys.argv[1], sys.argv[2]],
    env=child_environment,
)
raise SystemExit(result.returncode)
