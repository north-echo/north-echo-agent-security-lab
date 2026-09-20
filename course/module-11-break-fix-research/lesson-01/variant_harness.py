#!/usr/bin/env python3
"""Observe fixed synthetic fixtures and model choices, never execute plan text."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 4:
        return 2
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    choices = {
        "execution": {"shell", "argv"}, "environment": {"inherit", "minimal"},
        "filesystem": {"lexical", "resolved"}, "network": {"direct", "broker_only"},
        "cleanup": {"prefix", "owned"},
    }
    if not isinstance(plan, dict) or set(plan) != {"schema", "variant_id", "workload", "controls"}:
        raise ValueError("invalid plan shape")
    if type(plan["schema"]) is not int or plan["schema"] != 1 or not isinstance(plan["variant_id"], str):
        raise ValueError("invalid plan identity")
    workload, controls = plan["workload"], plan["controls"]
    if not isinstance(workload, dict) or set(workload) != {"operation", "resource", "literal"}:
        raise ValueError("invalid workload shape")
    if not all(isinstance(value, str) for value in workload.values()):
        raise ValueError("invalid workload values")
    if not isinstance(controls, dict) or set(controls) != set(choices):
        raise ValueError("invalid control shape")
    if any(not isinstance(controls[name], str) or controls[name] not in choices[name] for name in choices):
        raise ValueError("unknown control choice")
    evidence_path, work = Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    allowed = work / "allowed"
    allowed.mkdir()
    (allowed / "data.txt").write_text("allowed\n", encoding="utf-8")
    protected = work / "protected.txt"
    protected.write_text("SYNTHETIC-PROTECTED\n", encoding="utf-8")
    (allowed / "link.txt").symlink_to(protected.resolve())
    marker = work / "shell-marker"
    literal = workload["literal"]
    fixed_env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}

    if controls["execution"] == "shell":
        # Fixed toy only: the plan's literal is never interpreted as shell code.
        subprocess.run(["/bin/sh", "-c", '/usr/bin/printf "%s\\n" "$(/usr/bin/touch "$1")"',
                        "fixed-marker-fixture", str(marker.resolve())], cwd=work,
                       text=True, capture_output=True, check=True, timeout=2, env=fixed_env)
    else:
        subprocess.run(["/usr/bin/printf", "%s\n", literal], cwd=work,
                       text=True, capture_output=True, check=True, timeout=2, env=fixed_env)

    child_env = dict(fixed_env)
    if controls["environment"] == "inherit" and "NORTH_ECHO_FAKE_CREDENTIAL" in os.environ:
        child_env["NORTH_ECHO_FAKE_CREDENTIAL"] = os.environ["NORTH_ECHO_FAKE_CREDENTIAL"]
    environment = subprocess.run(["/usr/bin/env"], text=True, capture_output=True,
                                 check=True, timeout=2, env=child_env).stdout
    credential_visible = "NORTH_ECHO_FAKE_CREDENTIAL=" in environment

    candidate = allowed / "link.txt"
    if controls["filesystem"] == "lexical":
        authorized = str(candidate).startswith(str(allowed) + os.sep)
    else:
        authorized = allowed.resolve() in candidate.resolve().parents
    protected_read = authorized and candidate.read_text(encoding="utf-8").startswith("SYNTHETIC-")

    inet_created = False
    if controls["network"] == "direct":
        stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        inet_created = stream.fileno() >= 0
        stream.close()

    owned = f"north-echo-{plan['variant_id']}-owned"
    decoy = f"north-echo-{plan['variant_id']}-decoy"
    candidates = [owned, decoy]
    selected = candidates if controls["cleanup"] == "prefix" else [owned]
    evidence = {
        "schema": 1,
        "variant_id": plan["variant_id"],
        "allowed_operation": workload["operation"] == "read" and
                             (allowed / "data.txt").read_text(encoding="utf-8") == "allowed\n",
        "shell_marker_created": marker.exists(),
        "credential_visible": credential_visible,
        "protected_read": protected_read,
        "inet_created": inet_created,
        "cleanup_decoy_selected": decoy in selected,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
