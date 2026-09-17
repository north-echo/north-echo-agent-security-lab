from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
from pathlib import Path

from .paths import SafetyError, contained


def expected_user_unit_description(root: Path, target: str) -> str:
    workspace = (root / ".student" / target).resolve()
    return f"North Echo {target} workspace={workspace}"


def validate_user_unit_name(target: str, uid: int, raw: object) -> str:
    if not isinstance(raw, str):
        raise SafetyError("refusing non-string user unit registry entry")
    prefix = f"north-echo-{uid}-{target.replace('.', '-')}-"
    pattern = rf"{re.escape(prefix)}[a-z0-9]{{8,32}}\.service"
    if re.fullmatch(pattern, raw) is None:
        raise SafetyError(f"refusing unrelated user unit: {raw}")
    return raw


def validate_user_unit_state(root: Path, target: str, uid: int, unit: str, properties: dict[str, str]) -> str:
    if properties.get("Description") != expected_user_unit_description(root, target):
        raise SafetyError(f"refusing user unit {unit}: ownership description mismatch")
    control_group = properties.get("ControlGroup", "")
    expected_prefix = f"/user.slice/user-{uid}.slice/user@{uid}.service/"
    if not control_group.startswith(expected_prefix) or not control_group.endswith("/" + unit):
        raise SafetyError(f"refusing user unit {unit}: cgroup is outside the delegated user manager")
    return control_group


def _user_unit_properties(unit: str) -> dict[str, str] | None:
    run = subprocess.run(
        [
            "systemctl", "--user", "show", unit,
            "--property=LoadState", "--property=Description", "--property=ControlGroup",
        ],
        text=True,
        capture_output=True,
    )
    if run.returncode != 0:
        return None
    properties = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    return None if properties.get("LoadState") == "not-found" else properties


def register_user_unit(root: Path, target: str, unit: str) -> Path:
    validate_user_unit_name(target, os.getuid(), unit)
    workspace = contained(root / ".student", root / ".student" / target)
    if not workspace.is_dir():
        raise SafetyError(f"cannot register a unit without an active workspace: {target}")
    runtime_base = (root / ".runtime").resolve()
    runtime_dir = contained(runtime_base, runtime_base / target)
    runtime_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    registry_path = runtime_dir / "resources.json"
    registry: dict[str, list] = {
        "pids": [], "mounts": [], "cgroups": [], "user_units": [], "temp_paths": []
    }
    if registry_path.exists():
        loaded = json.loads(registry_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise SafetyError("runtime registry is not an object")
        registry.update(loaded)
    units = registry.get("user_units")
    if not isinstance(units, list):
        raise SafetyError("runtime user_units registry is not a list")
    if unit not in units:
        units.append(unit)
    temporary = runtime_dir / "resources.json.tmp"
    temporary.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(registry_path)
    return registry_path


def _mountpoints() -> set[str]:
    path = Path("/proc/self/mountinfo")
    if not path.exists():
        return set()
    points = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) > 4:
            points.add(fields[4].replace("\\040", " "))
    return points


def cleanup_target(root: Path, target: str, dry_run: bool = False) -> list[str]:
    runtime_base = (root / ".runtime").resolve()
    runtime_dir = contained(runtime_base, runtime_base / target)
    if not runtime_dir.exists():
        return []
    registry_path = runtime_dir / "resources.json"
    registry = {"pids": [], "mounts": [], "cgroups": [], "user_units": [], "temp_paths": []}
    if registry_path.exists():
        registry.update(json.loads(registry_path.read_text(encoding="utf-8")))
    actions: list[str] = []

    for raw in registry.get("pids", []):
        pid = int(raw)
        cmdline = Path(f"/proc/{pid}/cmdline")
        if not cmdline.exists():
            continue
        command = cmdline.read_bytes().replace(b"\x00", b" ").decode(errors="replace")
        workspace = str((root / ".student" / target).resolve())
        if workspace not in command:
            raise SafetyError(f"refusing to signal PID {pid}: command is not bound to {workspace}")
        actions.append(f"terminate pid {pid}")
        if not dry_run:
            os.kill(pid, signal.SIGTERM)

    mounted = _mountpoints()
    for raw in sorted(registry.get("mounts", []), key=len, reverse=True):
        mount = contained(root / ".student", Path(raw))
        if str(mount) in mounted:
            actions.append(f"unmount {mount}")
            if not dry_run:
                subprocess.run(["umount", str(mount)], check=True)

    if registry.get("cgroups", []):
        raise SafetyError("refusing direct cgroup cleanup: register the owning delegated user unit")

    uid = os.getuid()
    for raw in registry.get("user_units", []):
        unit = validate_user_unit_name(target, uid, raw)
        properties = _user_unit_properties(unit)
        if properties is None:
            continue
        control_group = validate_user_unit_state(root, target, uid, unit, properties)
        actions.append(f"stop owned user unit {unit}")
        if not dry_run:
            subprocess.run(["systemctl", "--user", "stop", unit], check=True)
            subprocess.run(
                ["systemctl", "--user", "reset-failed", unit],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            cgroup = Path("/sys/fs/cgroup" + control_group)
            if cgroup.exists():
                raise SafetyError(f"owned user unit stopped but cgroup remains: {cgroup}")

    for raw in registry.get("temp_paths", []):
        path = contained(runtime_dir, Path(raw))
        actions.append(f"remove temp {path}")
        if not dry_run:
            shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)

    actions.append(f"remove runtime registry {runtime_dir}")
    if not dry_run:
        shutil.rmtree(runtime_dir)
    return actions
