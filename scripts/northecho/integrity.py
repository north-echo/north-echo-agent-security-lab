from __future__ import annotations

import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def build_manifest(root: Path) -> dict[str, str]:
    course = root / "course"
    return {
        str(path.relative_to(root)): digest(path)
        for path in sorted(course.rglob("*"))
        if path.is_file() and path.name != ".course-manifest.json"
    }


def verify(root: Path) -> list[str]:
    manifest_path = root / "course" / ".course-manifest.json"
    if not manifest_path.exists():
        return ["course manifest is missing"]
    expected = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = build_manifest(root)
    problems = []
    for name in sorted(set(expected) | set(actual)):
        if name not in expected:
            problems.append(f"unexpected canonical file: {name}")
        elif name not in actual:
            problems.append(f"missing canonical file: {name}")
        elif expected[name] != actual[name]:
            problems.append(f"changed canonical file: {name}")
    return problems
