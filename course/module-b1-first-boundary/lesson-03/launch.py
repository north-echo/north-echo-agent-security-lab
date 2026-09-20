import os
import subprocess
import sys

# A partial repair: it removes one known name, not other private settings.
child_environment = dict(os.environ)
child_environment.pop("NE_PRIVATE_TOKEN", None)
result = subprocess.run(
    [sys.executable, sys.argv[1], sys.argv[2]],
    env=child_environment,
)
raise SystemExit(result.returncode)
