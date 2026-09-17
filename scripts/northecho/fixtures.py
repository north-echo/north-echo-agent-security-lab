from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

ADJECTIVES = ("amber", "quiet", "polar", "silver", "lunar", "cedar")
NOUNS = ("otter", "heron", "relay", "quartz", "harbor", "signal")


def generate(directory: Path, target: str, attempt: int) -> dict:
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    token = secrets.token_hex(16)
    fixture_id = secrets.token_hex(4)
    synthetic_user = f"{secrets.choice(ADJECTIVES)}-{secrets.choice(NOUNS)}-{secrets.randbelow(900)+100}"
    manifest = {
        "schema": 1,
        "target": target,
        "attempt": attempt,
        "fixture_id": fixture_id,
        "canary": f"NECHO-{token}",
        "synthetic_user": synthetic_user,
        "port": secrets.randbelow(10000) + 41000,
        "hostname": f"ne-{fixture_id}",
    }
    manifest_path = directory / "manifest.json"
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    os.chmod(manifest_path, 0o600)
    protected = directory / f"protected-{fixture_id}.txt"
    protected.write_text(manifest["canary"] + "\n", encoding="utf-8")
    os.chmod(protected, 0o600)
    return manifest
