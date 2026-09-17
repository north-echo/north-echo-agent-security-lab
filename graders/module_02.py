from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from northecho.grading import Check


def _inode(namespace: str) -> int:
    return os.stat(f"/proc/self/ns/{namespace}").st_ino


def grade(workspace: Path, fixture: dict) -> list[Check]:
    launcher = workspace / "sandbox.sh"
    if not Path("/proc/self/ns").exists():
        return [Check("Linux namespace interfaces are available", False, "Run this lab in the disposable Linux VM")]
    if not launcher.is_file():
        return [Check("A namespace launcher is present", False, "Module 02 lab: interface contract")]
    launcher.chmod(launcher.stat().st_mode | 0o100)
    probe = Path(__file__).parent / "probes" / "namespace_probe.py"
    environment = os.environ.copy()
    environment["NE_EXPECTED_HOSTNAME"] = fixture["hostname"]
    try:
        run = subprocess.run(
            [str(launcher), "python3", str(probe)],
            cwd=workspace,
            env=environment,
            text=True,
            capture_output=True,
            timeout=12,
        )
    except subprocess.TimeoutExpired:
        return [Check("The namespace launcher completes without hanging", False, "Module 02 lesson 03")]
    payload = None
    for line in run.stdout.splitlines():
        if line.startswith("NE_PROBE="):
            try:
                payload = json.loads(line.removeprefix("NE_PROBE="))
            except json.JSONDecodeError:
                pass
    if payload is None:
        return [
            Check("The probe executes inside the launcher", False, "Module 02 lab: preserve the command interface"),
            Check("Namespace setup succeeds on this VM", False, "Check unprivileged user-namespace prerequisites in README.md"),
        ]
    nspid = payload.get("nspid", [])
    return [
        Check("Approved child command still executes", run.returncode == 0, "Module 02 lesson 01"),
        Check("Child has a distinct UTS namespace", payload.get("uts_inode") != _inode("uts"), "Module 02 lesson 02"),
        Check("Child uses the randomized synthetic hostname", payload.get("hostname") == fixture["hostname"], "Module 02 lesson 02"),
        Check("Child has a distinct PID namespace", payload.get("pid_inode") != _inode("pid") and len(nspid) >= 2 and nspid[-1] == 1, "Module 02 lesson 03"),
        Check("Child has a distinct mount namespace", payload.get("mnt_inode") != _inode("mnt"), "Module 02 lesson 03"),
        Check("/proc reflects the child PID namespace", payload.get("proc_one_is_self") is True, "Module 02 lesson 03"),
    ]
