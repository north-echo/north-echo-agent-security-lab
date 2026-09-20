from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, run_bounded


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "read_report.py"
    if not source.is_file():
        return [Check("Reader source exists", False, "B0.03: edit read_report.py in your workspace.")]
    checks = []
    # The student is not given the operator's environment or real credentials.
    with tempfile.TemporaryDirectory(prefix=".grade-", dir=workspace) as raw:
        directory = Path(raw)
        for name, text in (("daily report.txt", fixture["canary"] + "\nArrived.\n"),
                           ("other.txt", "No final newline: " + fixture["hostname"])):
            report = directory / name
            report.write_text(text, encoding="utf-8")
            run = run_bounded([sys.executable, str(source), str(report)], cwd=workspace,
                              env={"PATH": "/usr/bin:/bin"})
            checks.append(Check(f"Reads supplied {name} exactly", run.returncode == 0 and
                                run.stdout == text and run.stderr == "",
                                "B0.03: use the argument, preserve spaces, and avoid adding a newline."))
        for label, arguments in (("missing report", [str(directory / "absent.txt")]),
                                 ("missing argument", []),
                                 ("directory instead of report", [str(directory)])):
            run = run_bounded([sys.executable, str(source), *arguments], cwd=workspace,
                              env={"PATH": "/usr/bin:/bin"})
            checks.append(Check(f"Reports failure for {label}", run.returncode != 0 and
                                run.stdout == "" and bool(run.stderr.strip()),
                                "B0.03: check argument count and report read errors on stderr."))
    return checks
