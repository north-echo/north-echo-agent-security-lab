#!/usr/bin/env python3
"""Launch one synthetic workload through the North Echo containment stack."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time


def integer(spec: dict, name: str, minimum: int, maximum: int) -> int:
    value = spec.get(name)
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


def validated(spec: dict) -> tuple[Path, Path, list[str], int, int, int]:
    fields = {"guard", "allowed_root", "command", "memory_max", "tasks_max", "cpu_percent"}
    if not isinstance(spec, dict) or set(spec) != fields:
        raise ValueError("spec must be an object with exactly the documented fields")
    if not all(isinstance(spec[name], str) for name in ("guard", "allowed_root")):
        raise ValueError("guard and allowed_root must be path strings")
    guard, root = Path(spec["guard"]), Path(spec["allowed_root"])
    command = spec["command"]
    if not guard.is_absolute() or not guard.is_file() or guard.is_symlink():
        raise ValueError("guard must be an absolute regular non-symlink path")
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        raise ValueError("allowed_root must be an absolute directory without a symlink leaf")
    if not isinstance(command, list) or not command or any(
            not isinstance(item, str) or "\x00" in item for item in command):
        raise ValueError("command must be a nonempty argv string array")
    if not Path(command[0]).is_absolute():
        raise ValueError("command executable must be absolute")
    root = root.resolve(strict=True)
    if root == Path("/"):
        raise ValueError("the whole filesystem cannot be the workload root")
    executable = Path(command[0]).resolve(strict=True)
    if os.path.commonpath((root, executable)) != str(root) or not executable.is_file():
        raise ValueError("command executable must resolve beneath allowed_root")
    return (
        guard.resolve(strict=True), root, [str(executable), *command[1:]],
        integer(spec, "memory_max", 16 * 1024 * 1024, 1024 * 1024 * 1024),
        integer(spec, "tasks_max", 4, 256),
        integer(spec, "cpu_percent", 10, 100),
    )


def register_owner(client_env: dict) -> dict:
    workspace = Path(__file__).resolve().parent
    prepared = workspace.parent.name == ".student"
    target = workspace.name if prepared else "10.lab"
    if target not in {"10.03", "10.lab"}:
        raise ValueError("unsupported prepared runtime workspace")
    unit = f"north-echo-{os.getuid()}-{target.replace('.', '-')}-{secrets.token_hex(6)}.service"
    owner = {"unit": unit, "uid": os.getuid(),
             "description": f"North Echo {target} workspace={workspace}", "record": None}
    if prepared:
        control = workspace.parent.parent / "scripts/labctl.py"
        subprocess.run([sys.executable, str(control), "register-unit", target, unit],
                       check=True, capture_output=True, text=True, timeout=5, env=client_env)
    else:
        # The external grader copies this file into a separate owned directory.
        runtime = workspace / ".runtime"
        if runtime.is_symlink():
            raise ValueError("refusing a symlinked ownership directory")
        runtime.mkdir(mode=0o700, exist_ok=True)
        record = runtime / (unit + ".json")
        with record.open("x", encoding="utf-8") as stream:
            json.dump(owner, stream, sort_keys=True)
        owner["record"] = record
    return owner


def inspect_unit(owner: dict, client_env: dict) -> dict | None:
    run = subprocess.run(
        ["systemctl", "--user", "show", owner["unit"], "--property=LoadState",
         "--property=Description", "--property=ControlGroup"],
        text=True, capture_output=True, timeout=5, env=client_env,
    )
    properties = dict(line.split("=", 1) for line in run.stdout.splitlines() if "=" in line)
    if properties.get("LoadState") == "not-found":
        return None
    if run.returncode or not properties.get("LoadState"):
        raise RuntimeError("unit state could not be established; ownership record retained")
    return properties


def collect_owned(owner: dict, client_env: dict) -> None:
    properties = inspect_unit(owner, client_env)
    if properties is not None:
        group = properties.get("ControlGroup", "")
        prefix = f"/user.slice/user-{owner['uid']}.slice/user@{owner['uid']}.service/"
        if (properties.get("Description") != owner["description"]
                or not group.startswith(prefix) or not group.endswith("/" + owner["unit"])):
            raise RuntimeError("unit ownership mismatch; refusing stop and retaining record")
        subprocess.run(["systemctl", "--user", "stop", owner["unit"]],
                       check=True, capture_output=True, timeout=5, env=client_env)
        for _ in range(20):
            if inspect_unit(owner, client_env) is None:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("unit remains after stop; ownership record retained")
        if Path("/sys/fs/cgroup" + group).exists():
            raise RuntimeError("owned cgroup remains; ownership record retained")
    if owner["record"] is not None:
        owner["record"].unlink()


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} SPEC.json RESULT.json", file=sys.stderr)
        return 2
    result_path = Path(sys.argv[2])
    try:
        spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        guard, root, command, memory, tasks, cpu = validated(spec)
    except (OSError, ValueError, TypeError) as error:
        print(f"runtime specification denied: {error}", file=sys.stderr)
        return 1

    client_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if name in os.environ:
            client_env[name] = os.environ[name]
    try:
        owner = register_owner(client_env)
        unit = owner["unit"]
        argv = [
            "systemd-run", "--user", "--wait", "--pipe", "--collect", "--quiet",
            "--expand-environment=no", f"--unit={unit}", f"--description={owner['description']}",
            "--property=KillMode=control-group", "--property=TimeoutStopSec=2s",
            "--property=RuntimeMaxSec=15s", "--property=CPUQuotaPeriodSec=100ms",
            f"--property=CPUQuota={cpu}%", f"--property=MemoryMax={memory}",
            "--property=MemorySwapMax=0", f"--property=TasksMax={tasks}",
            "--property=UnsetEnvironment=NORTH_ECHO_FAKE_CREDENTIAL",
            "--setenv=PATH=/usr/bin:/bin", "--setenv=LANG=C.UTF-8", "--setenv=LC_ALL=C.UTF-8",
            "--", "/usr/bin/unshare", "--user", "--map-root-user", "--net", "--",
            "/usr/bin/setpriv", "--bounding-set=-all", "--inh-caps=-all", "--ambient-caps=-all",
            "--no-new-privs", "--", "/usr/bin/env", "-i", "PATH=/usr/bin:/bin",
            "LANG=C.UTF-8", "LC_ALL=C.UTF-8", str(guard), str(root), *command,
        ]
        try:
            run = subprocess.run(argv, text=True, capture_output=True, check=False,
                                 timeout=20, env=client_env)
        finally:
            collect_owned(owner, client_env)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"runtime launch or collection failed: {error}", file=sys.stderr)
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
    return int(run.returncode != 0)


if __name__ == "__main__":
    raise SystemExit(main())
