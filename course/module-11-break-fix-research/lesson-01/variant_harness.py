#!/usr/bin/env python3
"""Reproduce runtime-plan effects without an autonomous agent or external target."""

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
    evidence_path, work = Path(sys.argv[2]), Path(sys.argv[3])
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    allowed = work / "allowed"
    allowed.mkdir()
    (allowed / "data.txt").write_text("allowed\n", encoding="utf-8")
    protected = work / "protected.txt"
    protected.write_text("SYNTHETIC-PROTECTED\n", encoding="utf-8")
    (allowed / "link.txt").symlink_to(protected.resolve())
    marker = work / "shell-marker"
    literal = plan["workload"]["literal"].replace("shell-marker", str(marker))
    controls = plan["controls"]

    if controls["execution"] == "shell":
        subprocess.run("/usr/bin/printf '%s\\n' " + literal, shell=True, cwd=work,
                       text=True, capture_output=True, check=False)
    else:
        subprocess.run(["/usr/bin/printf", "%s\n", literal], cwd=work,
                       text=True, capture_output=True, check=False)

    child_env = dict(os.environ) if controls["environment"] == "inherit" else {
        "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"
    }
    environment = subprocess.run(["/usr/bin/env"], text=True, capture_output=True,
                                 check=False, env=child_env).stdout
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
        "allowed_operation": plan["workload"]["operation"] == "read",
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
