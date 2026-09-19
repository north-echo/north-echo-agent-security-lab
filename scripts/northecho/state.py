from __future__ import annotations

import json
import os
import tempfile
import fcntl
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .paths import SafetyError, safe_child


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(root: Path) -> dict:
    path = safe_child(root, ".state", "progress.json")
    if not path.exists():
        return {"schema": 1, "targets": {}}
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or value.get("schema") != 1 or not isinstance(value.get("targets"), dict):
        raise SafetyError("invalid progress schema; preserve the file for recovery")
    if any(not isinstance(record, dict) for record in value["targets"].values()):
        raise SafetyError("invalid progress entry; preserve the file for recovery")
    return value


def save(root: Path, value: dict) -> None:
    destination = safe_child(root, ".state", "progress.json")
    directory = root / ".state"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="progress.", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def entry(progress: dict, target: str) -> dict:
    record = progress["targets"].setdefault(
        target,
        {"starts": 0, "resets": 0, "grade_attempts": 0, "passed": False},
    )
    record.setdefault("ever_passed", bool(record.get("passed")))
    return record


@contextmanager
def lifecycle_lock(root: Path):
    """Serialize whole CLI transactions, not just the final atomic rename."""
    path = safe_child(root, ".state", "lifecycle.lock")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def record_grade(record: dict, passed: bool, mode: str, failed_properties: list[str]) -> None:
    record["grade_attempts"] += 1
    record["last_graded_at"] = now()
    record["last_graded_attempt"] = record["starts"]
    record["last_result"] = "passed" if passed else "failed"
    record["last_mode"] = mode
    record["failed_properties"] = list(failed_properties)
    record["ever_passed"] = bool(record.get("ever_passed") or record.get("passed") or passed)
    record["passed"] = record["ever_passed"]  # Backward-compatible achievement field.
    if passed:
        record["passed_at"] = now()
