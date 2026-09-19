from __future__ import annotations

from pathlib import Path


class SafetyError(RuntimeError):
    pass


def repo_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    if not (root / ".north-echo-root").is_file():
        raise SafetyError("refusing to run outside a marked North Echo repository")
    return root


def contained(base: Path, candidate: Path) -> Path:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve(strict=False)
    if candidate_resolved == base_resolved or base_resolved not in candidate_resolved.parents:
        raise SafetyError(f"refusing path outside lab root: {candidate}")
    return candidate_resolved


def safe_child(root: Path, area: str, target: str) -> Path:
    if area not in {".student", ".fixtures", ".runtime", ".state"}:
        raise SafetyError(f"unknown managed area: {area}")
    if not target or any(part in target for part in ("/", "\\", "..")):
        raise SafetyError(f"unsafe target name: {target!r}")
    if (root / area).is_symlink() or (root / area / target).is_symlink():
        raise SafetyError(f"refusing symlink outside lab root ownership: {area}/{target}")
    base = contained(root, root / area)
    return contained(base, base / target)
