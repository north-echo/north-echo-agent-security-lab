from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from northecho.grading import Check


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "secure-launch.c"
    if not Path("/proc/self/status").exists():
        return [Check("Linux /proc privilege state is available", False, "Run this lab in the disposable Linux VM")]
    if not source.is_file():
        return [Check("A secure launcher source file is present", False, "Module 03 lab: interface contract")]
    with tempfile.TemporaryDirectory(prefix=".grade-", dir=workspace) as raw:
        evaluation = Path(raw)
        binary = evaluation / "secure-launch"
        compiled = subprocess.run(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-O2", str(source), "-o", str(binary)],
            text=True,
            capture_output=True,
        )
        if compiled.returncode != 0:
            return [Check("The launcher builds cleanly", False, "Module 03 lab: interface contract")]
        probe = Path(__file__).parent / "probes" / "privilege_probe.py"
        try:
            run = subprocess.run(
                [str(binary), "python3", str(probe)],
                text=True,
                capture_output=True,
                timeout=8,
            )
        except subprocess.TimeoutExpired:
            return [Check("The secure launcher completes without hanging", False, "Module 03 lesson 03")]
    payload = None
    for line in run.stdout.splitlines():
        if line.startswith("NE_PROBE="):
            try:
                payload = json.loads(line.removeprefix("NE_PROBE="))
            except json.JSONDecodeError:
                pass
    if payload is None:
        return [Check("Approved child command still executes", False, "Module 03 lab: preserve the command interface")]
    return [
        Check("Approved child command still executes", run.returncode == 0, "Module 03 lesson 01"),
        Check("no_new_privs is active before exec", payload.get("NoNewPrivs") == "1", "Module 03 lesson 03"),
        Check("Effective capabilities are empty", int(payload.get("CapEff", "1"), 16) == 0, "Module 03 lessons 01-02"),
        Check("Permitted capabilities are empty", int(payload.get("CapPrm", "1"), 16) == 0, "Module 03 lesson 02"),
        Check("Inheritable capabilities are empty", int(payload.get("CapInh", "1"), 16) == 0, "Module 03 lesson 02"),
        Check("Ambient capabilities are empty", int(payload.get("CapAmb", "1"), 16) == 0, "Module 03 lesson 02"),
        Check("Launcher preserves the invoking UID", payload.get("Uid", "").split()[:2] == [str(os.getuid()), str(os.geteuid())], "Module 03 lesson 01"),
    ]
