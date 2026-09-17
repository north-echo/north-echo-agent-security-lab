#!/usr/bin/env python3
import os
import subprocess

# Intentional mistake: copying the full parent environment copies its authority.
child_env = os.environ.copy()
subprocess.run(["python3", "show-env.py"], env=child_env, check=True)
