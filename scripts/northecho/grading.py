from __future__ import annotations

import importlib.util
import json
import os
import secrets
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Check:
    name: str
    passed: bool
    practice_hint: str = ""


class GradingError(ValueError):
    """A student execution or result cannot be evaluated reliably."""


def result_object(path: Path, limit: int = 1024 * 1024) -> dict:
    if path.stat().st_size > limit:
        raise GradingError("result exceeds the one-MiB limit")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GradingError("result must be a JSON object")
    return value


def run_bounded(argv, *, timeout=10, text=True, capture_output=True, check=False, **kwargs):
    """Own one process session, cap captured output, and always collect children.

    This is a reliability supervisor inside the disposable VM, not a sandbox.
    Services started through systemd need separate exact-unit cleanup.
    """
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr,
                                   start_new_session=True, **kwargs)
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                if stdout.tell() + stderr.tell() > 1024 * 1024:
                    raise GradingError("process output exceeds the one-MiB limit")
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(argv, timeout)
                time.sleep(0.01)
            if stdout.tell() + stderr.tell() > 1024 * 1024:
                raise GradingError("process output exceeds the one-MiB limit")
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
        stdout.seek(0)
        stderr.seek(0)
        out, err = stdout.read(), stderr.read()
        if text:
            out, err = out.decode(errors="replace"), err.decode(errors="replace")
        result = subprocess.CompletedProcess(argv, process.returncode, out, err)
        if check:
            result.check_returncode()
        return result


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def evaluate(grader, workspace: Path, fixture: dict) -> list[Check]:
    try:
        checks = grader.grade(workspace, fixture)
        if not checks or not all(isinstance(c, Check) and type(c.passed) is bool for c in checks):
            raise GradingError("grader returned an invalid or empty check set")
        return checks
    except subprocess.TimeoutExpired:
        return [Check("Student execution completed within its deadline", False,
                      "Check for waiting input, an infinite loop, or a child that never exits.")]
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError):
        # Do not print raw payloads: a student result can contain synthetic secrets.
        return [Check("Student result satisfies the execution and JSON contract", False,
                      "Check syntax, process exit status, required files, JSON object shape and field types.")]


def load_grader(root: Path, module: str):
    path = root / "graders" / ("capstone.py" if module == "capstone" else f"module_{module}.py")
    spec = importlib.util.spec_from_file_location(f"north_echo_grader_{module}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load grader: {path}")
    module_obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_obj)
    return module_obj


def fresh_evaluation_fixture(target: str) -> dict:
    return {
        "target": target,
        "canary": f"GRADE-{secrets.token_hex(16)}",
        "hostname": f"grade-{secrets.token_hex(3)}",
    }
