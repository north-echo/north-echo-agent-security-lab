from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(root: Path) -> dict:
    path = root / ".state" / "progress.json"
    if not path.exists():
        return {"schema": 1, "targets": {}}
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def save(root: Path, value: dict) -> None:
    directory = root / ".state"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="progress.", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / "progress.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def entry(progress: dict, target: str) -> dict:
    return progress["targets"].setdefault(
        target,
        {"starts": 0, "resets": 0, "grade_attempts": 0, "passed": False},
    )
