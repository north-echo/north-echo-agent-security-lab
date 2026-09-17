from __future__ import annotations

import importlib.util
import secrets
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Check:
    name: str
    passed: bool
    practice_hint: str = ""


def load_grader(root: Path, module: str):
    path = root / "graders" / f"module_{module}.py"
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
