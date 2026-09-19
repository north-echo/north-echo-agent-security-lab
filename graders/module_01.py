from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from northecho.grading import Check, run_bounded


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "launcher.c"
    if not source.is_file():
        return [Check("A launcher source file is present", False, "Module 01 lessons 02-03")]
    with tempfile.TemporaryDirectory(prefix=".grade-", dir=workspace) as raw:
        evaluation = Path(raw)
        binary = evaluation / "launcher"
        compiled = run_bounded(
            ["cc", "-std=c11", "-Wall", "-Wextra", "-O2", str(source), "-o", str(binary)],
            text=True,
            capture_output=True,
        )
        if compiled.returncode != 0:
            return [Check("The launcher builds cleanly", False, "Module 01 lab: interface contract")]

        protected = evaluation / "protected.txt"
        protected.write_text(fixture["canary"] + "\n", encoding="utf-8")
        probe = Path(__file__).parent / "probes" / "authority_probe.py"
        environment = os.environ.copy()
        environment["NE_LAB_TOKEN"] = fixture["canary"]
        descriptor = os.open(protected, os.O_RDONLY)
        try:
            run = run_bounded(
                [str(binary), "python3", str(probe)],
                env=environment,
                pass_fds=(descriptor,),
                text=True,
                capture_output=True,
                timeout=8,
            )
        except subprocess.TimeoutExpired:
            return [Check("The launcher completes without hanging", False, "Module 01 lesson 03")]
        finally:
            os.close(descriptor)

    output = run.stdout + run.stderr
    return [
        Check("Approved child command still executes", run.returncode == 0 and "PROBE_ALIVE" in output, "Module 01 lesson 01"),
        Check("Synthetic parent environment authority is not inherited", "ENV_LEAK" not in output and fixture["canary"] not in output, "Module 01 lesson 02"),
        Check("Pre-opened protected descriptor is not inherited", "FD_LEAK" not in output and fixture["canary"] not in output, "Module 01 lesson 03"),
        Check("The launcher reports no internal secret material", fixture["canary"] not in output, "Module 01 lessons 02-03"),
    ]
