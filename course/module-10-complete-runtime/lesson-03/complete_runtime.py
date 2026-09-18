#!/usr/bin/env python3
"""Launch one workload through the complete North Echo containment stack."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys


def integer(spec: dict, name: str, minimum: int, maximum: int) -> int:
    value = spec.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def validated(spec: dict) -> tuple[Path, Path, list[str], int, int, int]:
    if not isinstance(spec, dict):
        raise ValueError("spec must be an object")
    guard = Path(spec.get("guard", ""))
    root = Path(spec.get("allowed_root", ""))
    command = spec.get("command")
    if not guard.is_absolute() or not guard.is_file() or guard.is_symlink():
        raise ValueError("guard must be an absolute regular non-symlink path")
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("allowed_root must be an absolute directory without a symlink leaf")
    if not isinstance(command, list) or not command or any(not isinstance(item, str) or "\x00" in item for item in command):
        raise ValueError("command must be a nonempty argv string array")
    root = root.resolve(strict=True)
    executable = Path(command[0]).resolve(strict=True)
    if os.path.commonpath((root, executable)) != str(root) or not executable.is_file():
        raise ValueError("command executable must resolve beneath allowed_root")
    command = [str(executable), *command[1:]]
    return (
        guard.resolve(strict=True), root, command,
        integer(spec, "memory_max", 16 * 1024 * 1024, 1024 * 1024 * 1024),
        integer(spec, "tasks_max", 4, 256),
        integer(spec, "cpu_percent", 10, 100),
    )


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    result_path = Path(sys.argv[2])
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        guard, root, command, memory, tasks, cpu = validated(spec)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"runtime specification denied: {error}", file=sys.stderr)
        return 1

    unit = f"north-echo-{os.getuid()}-10-lab-{secrets.token_hex(6)}.service"
    argv = [
        "systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
        f"--unit={unit}", "--property=KillMode=control-group", "--property=TimeoutStopSec=5s",
        f"--property=CPUQuota={cpu}%", f"--property=MemoryMax={memory}",
        "--property=MemorySwapMax=0", f"--property=TasksMax={tasks}",
        "--property=UnsetEnvironment=NORTH_ECHO_FAKE_CREDENTIAL",
        "--setenv=PATH=/usr/bin:/bin", "--setenv=LANG=C.UTF-8", "--setenv=LC_ALL=C.UTF-8",
        "--", "unshare", "--user", "--map-root-user", "--net", "--",
        "setpriv", "--bounding-set=-all", "--inh-caps=-all", "--ambient-caps=-all",
        "--no-new-privs", "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
        "LANG=C.UTF-8", "LC_ALL=C.UTF-8", str(guard), str(root), *command,
    ]
    client_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if name in os.environ:
            client_env[name] = os.environ[name]
    try:
        run = subprocess.run(argv, text=True, capture_output=True, check=False,
                             timeout=20, env=client_env)
    except subprocess.TimeoutExpired:
        subprocess.run(["systemctl", "--user", "stop", unit], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=client_env)
        print("runtime timed out and its exact unit was stopped", file=sys.stderr)
        return 1
    attestation = None
    try:
        attestation = json.loads(run.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        pass
    result_path.write_text(json.dumps({
        "schema": 1, "status": run.returncode, "unit": unit,
        "stdout": run.stdout, "stderr": run.stderr, "attestation": attestation,
    }, sort_keys=True) + "\n", encoding="utf-8")
    return run.returncode != 0


if __name__ == "__main__":
    raise SystemExit(main())
