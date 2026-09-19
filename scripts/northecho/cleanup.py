from __future__ import annotations

import json
import os
import re
import shutil
import signal
import select
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .paths import SafetyError, contained, safe_child


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
        timeout=10,
    )
    properties = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    if properties.get("LoadState") == "not-found":
        return None
    if run.returncode != 0 or not properties.get("LoadState"):
        raise SafetyError(f"cannot establish user unit state: {unit}; registry retained")
    return properties


def register_user_unit(root: Path, target: str, unit: str) -> Path:
    validate_user_unit_name(target, os.getuid(), unit)
    workspace = safe_child(root, ".student", target)
    if not workspace.is_dir():
        raise SafetyError(f"cannot register a unit without an active workspace: {target}")
    runtime_dir = safe_child(root, ".runtime", target)
    runtime_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    registry_path = runtime_dir / "resources.json"
    if registry_path.is_symlink():
        raise SafetyError("refusing a symlinked runtime registry")
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
    fd, name = tempfile.mkstemp(prefix="resources.", dir=runtime_dir)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(registry, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.replace(registry_path)
    finally:
        temporary.unlink(missing_ok=True)
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


@dataclass
class CleanupPlan:
    root: Path
    target: str
    runtime_dir: Path
    actions: list[str] = field(default_factory=list)
    pids: list[tuple[int, str]] = field(default_factory=list)
    mounts: list[Path] = field(default_factory=list)
    units: list[tuple[str, str]] = field(default_factory=list)
    temps: list[Path] = field(default_factory=list)


def _pid_identity(pid: int, workspace: Path) -> str | None:
    try:
        directory = Path(f"/proc/{pid}")
        fields = (directory / "stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return None
        argv = (directory / "cmdline").read_bytes().split(b"\0")
        prefix = str(workspace).encode()
        if not any(arg == prefix or arg.startswith(prefix + b"/") for arg in argv):
            raise SafetyError(f"PID {pid} is not bound to the exact target workspace")
        return fields[19]  # /proc/PID/stat field 22: process start time
    except FileNotFoundError:
        return None


def plan_cleanup(root: Path, target: str) -> CleanupPlan:
    runtime_dir = safe_child(root, ".runtime", target)
    workspace = safe_child(root, ".student", target)
    plan = CleanupPlan(root, target, runtime_dir)
    if not runtime_dir.exists():
        return plan
    registry_path = runtime_dir / "resources.json"
    if registry_path.is_symlink():
        raise SafetyError("refusing a symlinked runtime registry")
    registry = {"pids": [], "mounts": [], "cgroups": [], "user_units": [], "temp_paths": []}
    if registry_path.exists():
        loaded = json.loads(registry_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or set(loaded) - set(registry):
            raise SafetyError("invalid runtime registry schema")
        registry.update(loaded)
    if any(not isinstance(value, list) for value in registry.values()):
        raise SafetyError("runtime resource collections must be lists")
    if registry["cgroups"]:
        raise SafetyError("refusing direct cgroup cleanup: register the owning delegated user unit")
    for pid in registry["pids"]:
        if type(pid) is not int or pid <= 1:
            raise SafetyError("invalid registered PID")
        identity = _pid_identity(pid, workspace)
        if identity is not None:
            if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
                raise SafetyError("PID cleanup requires Linux pidfd support")
            plan.pids.append((pid, identity))
            plan.actions.append(f"terminate and wait for pid {pid}")
    if any(not isinstance(raw, str) for raw in registry["mounts"] + registry["temp_paths"]):
        raise SafetyError("registered paths must be strings")
    mounted = _mountpoints()
    for raw in sorted(registry["mounts"], key=len, reverse=True):
        mount = contained(workspace, Path(raw))
        if str(mount) in mounted:
            plan.mounts.append(mount)
            plan.actions.append(f"unmount {mount}")
    uid = os.getuid()
    for raw in registry["user_units"]:
        unit = validate_user_unit_name(target, uid, raw)
        properties = _user_unit_properties(unit)
        if properties is None:
            continue
        control_group = validate_user_unit_state(root, target, uid, unit, properties)
        plan.units.append((unit, control_group))
        plan.actions.append(f"stop owned user unit {unit}")
    for raw in registry["temp_paths"]:
        path = contained(runtime_dir, Path(raw))
        plan.temps.append(path)
        plan.actions.append(f"remove temp {path}")
    plan.actions.append(f"remove runtime registry {runtime_dir}")
    return plan


def execute_cleanup(plan: CleanupPlan, dry_run: bool = False) -> list[str]:
    if dry_run or not plan.actions:
        return plan.actions
    workspace = safe_child(plan.root, ".student", plan.target)
    for pid, identity in plan.pids:
        if _pid_identity(pid, workspace) is None:
            continue
        descriptor = os.pidfd_open(pid)
        try:
            if _pid_identity(pid, workspace) != identity:
                raise SafetyError(f"PID {pid} changed identity; registry retained")
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            if not select.select([descriptor], [], [], 5)[0]:
                raise SafetyError(f"PID {pid} did not exit; registry retained")
        finally:
            os.close(descriptor)
    for mount in plan.mounts:
        subprocess.run(["umount", str(mount)], check=True, timeout=10)
    for unit, control_group in plan.units:
        properties = _user_unit_properties(unit)
        if properties is not None:
            validate_user_unit_state(plan.root, plan.target, os.getuid(), unit, properties)
            subprocess.run(["systemctl", "--user", "stop", unit], check=True, timeout=15)
            if Path("/sys/fs/cgroup" + control_group).exists():
                raise SafetyError(f"owned user unit stopped but cgroup remains: {control_group}")
            subprocess.run(["systemctl", "--user", "reset-failed", unit], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    for path in plan.temps:
        if path.exists():
            shutil.rmtree(path) if path.is_dir() else path.unlink()
    shutil.rmtree(plan.runtime_dir)
    return plan.actions


def cleanup_target(root: Path, target: str, dry_run: bool = False) -> list[str]:
    return execute_cleanup(plan_cleanup(root, target), dry_run)
