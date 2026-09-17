from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
from pathlib import Path

from .paths import SafetyError, contained


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
    registry = {"pids": [], "mounts": [], "cgroups": [], "temp_paths": []}
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

    uid = os.getuid()
    cgroup_base = Path(f"/sys/fs/cgroup/north-echo-{uid}")
    for raw in registry.get("cgroups", []):
        cgroup = contained(cgroup_base, Path(raw))
        actions.append(f"remove cgroup {cgroup}")
        if not dry_run:
            cgroup.rmdir()

    for raw in registry.get("temp_paths", []):
        path = contained(runtime_dir, Path(raw))
        actions.append(f"remove temp {path}")
        if not dry_run:
            shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)

    actions.append(f"remove runtime registry {runtime_dir}")
    if not dry_run:
        shutil.rmtree(runtime_dir)
    return actions
