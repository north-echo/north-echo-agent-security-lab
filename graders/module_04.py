from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, run_bounded


def _records(path: Path) -> list[dict] | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines]
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _field(record: dict, name: str):
    if name in record:
        return record[name]
    result = record.get("result")
    return result.get(name) if isinstance(result, dict) else None


def _run(agent: Path, task: Path, trace: Path, cwd: Path, environment: dict) -> subprocess.CompletedProcess[str] | None:
    try:
        return run_bounded(
            [sys.executable, str(agent), str(task), str(trace)],
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=8,
        )
    except subprocess.TimeoutExpired:
        return None


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "agent.py"
    if not source.is_file():
        return [Check("An agent source file is present", False, "Module 04 lab: interface contract")]

    with tempfile.TemporaryDirectory(prefix="north-echo-grade-04-") as raw:
        evaluation = Path(raw)
        submission = evaluation / "submission"
        work = evaluation / "work"
        submission.mkdir()
        work.mkdir()
        agent = submission / "agent.py"
        shutil.copy2(source, agent)
        agent.chmod(0o444)

        input_text = f"input-{fixture['hostname']}\n"
        output_text = f"output-{fixture['hostname']}\n"
        literal = f"literal {fixture['hostname']} $(touch SHELL_MARKER)"
        (work / "input.txt").write_text(input_text, encoding="utf-8")
        (work / "probe.py").write_text(
            "import json, os, sys\n"
            "print(json.dumps({'argv': sys.argv[1:], 'secret': os.environ.get('NE_AGENT_SECRET', '<absent>')}))\n",
            encoding="utf-8",
        )
        task = work / "task.json"
        trace = work / "trace.jsonl"
        task.write_text(
            json.dumps(
                {
                    "actions": [
                        {"id": "read-check", "tool": "read_file", "path": "input.txt"},
                        {"id": "write-check", "tool": "write_file", "path": "output.txt", "content": output_text},
                        {"id": "argv-check", "tool": "run_argv", "argv": [sys.executable, "probe.py", literal]},
                    ]
                }
            ),
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["NE_AGENT_SECRET"] = fixture["canary"]
        success = _run(agent, task, trace, work, environment)
        records = _records(trace)
        combined = "" if success is None else success.stdout + success.stderr
        serialized = "" if records is None else json.dumps(records, sort_keys=True)

        ordered = records is not None and [r.get("id") for r in records] == ["read-check", "write-check", "argv-check"]
        shaped = ordered and all(
            r.get("tool") == tool and isinstance(r.get("ok"), bool)
            for r, tool in zip(records, ("read_file", "write_file", "run_argv"))
        )
        read_ok = shaped and records[0]["ok"] is True and _field(records[0], "content") == input_text
        write_ok = (
            shaped
            and records[1]["ok"] is True
            and _field(records[1], "bytes_written") == len(output_text.encode())
            and (work / "output.txt").read_text(encoding="utf-8") == output_text
        )
        argv_stdout = _field(records[2], "stdout") if shaped else None
        argv_ok = (
            shaped
            and records[2]["ok"] is True
            and _field(records[2], "status") == 0
            and isinstance(argv_stdout, str)
            and literal in argv_stdout
        )
        secret_safe = fixture["canary"] not in combined and fixture["canary"] not in serialized and '"secret": "<absent>"' in (argv_stdout or "")
        shell_safe = not (work / "SHELL_MARKER").exists()

        failure_task = work / "failure-task.json"
        failure_trace = work / "failure-trace.jsonl"
        failure_task.write_text(
            json.dumps({"actions": [{"id": "failure-check", "tool": "run_argv", "argv": [sys.executable, "-c", "import sys; print('failure-signal', file=sys.stderr); sys.exit(7)"]}]}),
            encoding="utf-8",
        )
        failure = _run(agent, failure_task, failure_trace, work, environment)
        failure_records = _records(failure_trace)
        failure_ok = (
            failure is not None
            and failure.returncode != 0
            and failure_records is not None
            and len(failure_records) == 1
            and failure_records[0].get("ok") is False
            and _field(failure_records[0], "status") == 7
            and "failure-signal" in (_field(failure_records[0], "stderr") or "")
        )

        unknown_task = work / "unknown-task.json"
        unknown_trace = work / "unknown-trace.jsonl"
        unknown_task.write_text(json.dumps({"actions": [{"id": "unknown-check", "tool": "not_a_tool"}]}), encoding="utf-8")
        unknown = _run(agent, unknown_task, unknown_trace, work, environment)
        unknown_records = _records(unknown_trace)
        unknown_ok = (
            unknown is not None
            and unknown.returncode != 0
            and unknown_records is not None
            and len(unknown_records) == 1
            and unknown_records[0].get("id") == "unknown-check"
            and unknown_records[0].get("ok") is False
        )

    return [
        Check("Approved deterministic task completes", success is not None and success.returncode == 0, "Module 04 lesson 01"),
        Check("Trace has one ordered typed record per action", bool(shaped), "Module 04 lesson 01"),
        Check("read_file reports the observed content", bool(read_ok), "Module 04 lesson 01"),
        Check("write_file performs and records the exact write", bool(write_ok), "Module 04 lesson 01"),
        Check("run_argv preserves the literal argument vector", bool(argv_ok), "Module 04 lesson 02"),
        Check("Shell metacharacters are not interpreted", shell_safe, "Module 04 lesson 02"),
        Check("Synthetic ambient environment authority is absent", secret_safe, "Module 04 lesson 03"),
        Check("Nonzero tool status is recorded and propagated", failure_ok, "Module 04 lesson 02"),
        Check("Unknown tools fail closed with a trace record", unknown_ok, "Module 04 lesson 01"),
    ]
