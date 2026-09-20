from __future__ import annotations

import secrets
import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, result_object, run_bounded


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "launch.py"
    if not source.is_file():
        return [Check("Launcher source exists", False, "B1.02: edit launch.py in your workspace.")]
    checks = []
    with tempfile.TemporaryDirectory(prefix=".grade-", dir=workspace) as raw:
        directory = Path(raw)
        report = directory / "new report.txt"
        text = "Delivery " + fixture["hostname"] + "\n"
        report.write_text(text, encoding="utf-8")
        hidden_key = "NE_UNLISTED_" + secrets.token_hex(5).upper()
        # An independent worker records what actually arrived. This is not a
        # hostile-student sandbox: same-user code could tamper with the witness.
        for number, style in enumerate(("plain", "upper", "missing")):
            witness = directory / f"witness-{number}.json"
            worker = directory / f"worker {number}.py"
            worker.write_text(
                "import json, os, sys\nfrom pathlib import Path\n"
                f"Path({str(witness)!r}).write_text(json.dumps(dict(os.environ)))\n"
                "try:\n    text = Path(sys.argv[1]).read_text(encoding='utf-8')\n"
                "except OSError:\n    print('Report unavailable.', file=sys.stderr)\n"
                "    raise SystemExit(7)\n"
                "style = os.environ.get('NE_REPORT_STYLE')\n"
                "if style not in ('plain', 'upper'):\n"
                "    print('Style unavailable.', file=sys.stderr)\n    raise SystemExit(2)\n"
                "print(text.upper() if style == 'upper' else text, end='')\n",
                encoding="utf-8")
            public_style = "plain" if style == "missing" else style
            environment = {"PATH": "/usr/bin:/bin", "NE_REPORT_STYLE": public_style,
                           "NE_PRIVATE_TOKEN": fixture["canary"], hidden_key: fixture["canary"],
                           "ORDINARY_PARENT_SETTING": "not-needed"}
            selected_report = directory / "absent.txt" if style == "missing" else report
            run = run_bounded([sys.executable, str(source), str(worker), str(selected_report)],
                              cwd=workspace, env=environment)
            observed = result_object(witness) if witness.is_file() else {}
            checks.append(Check(f"{style}: supplied worker runs with selected public style",
                                observed.get("NE_REPORT_STYLE") == public_style,
                                "B1.02-03: run the supplied worker; retain the public setting's current value."))
            checks.append(Check(f"{style}: unapproved parent settings are absent",
                                bool(observed) and not any(key in observed for key in
                                    ("NE_PRIVATE_TOKEN", hidden_key, "ORDINARY_PARENT_SETTING", "PATH")),
                                "B1.03: select needed settings rather than deleting known private names."))
            expected = text.upper() if style == "upper" else text
            good = (run.returncode == 7 and run.stdout == "" and run.stderr == "Report unavailable.\n"
                    if style == "missing" else
                    run.returncode == 0 and run.stdout == expected and run.stderr == "")
            checks.append(Check(f"{style}: child output and exit status are preserved", good,
                                "B0.02 and B1.03: output is not an exit status; preserve both streams and child status."))
            checks.append(Check(f"{style}: no private value is printed",
                                fixture["canary"] not in run.stdout + run.stderr,
                                "B1.01: inspect presence, never print private settings or the whole environment."))
    return checks
