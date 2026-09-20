#!/usr/bin/env python3
"""One-shot synthetic operation broker for the composition lesson."""

import hashlib
import json
import os
from pathlib import Path
import socket
import signal
import sys


def stop(_signum, _frame):
    raise SystemExit(0)


def main() -> int:
    if len(sys.argv) != 5:
        return 2
    socket_path, token_path, credential_path, event_path = map(Path, sys.argv[1:])
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    token = token_path.read_text(encoding="utf-8").strip()
    credential = credential_path.read_text(encoding="utf-8").strip()
    if socket_path.exists() or socket_path.is_symlink():
        raise SystemExit("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        listener.listen(1)
        listener.settimeout(300)
        peer, _ = listener.accept()
        with peer:
            peer.settimeout(2)
            with peer.makefile("rb") as incoming:
                line = incoming.readline(16385)
            if len(line) > 16384 or not line.endswith(b"\n"):
                raise ValueError("request must be one bounded line")
            request = json.loads(line)
            expected = {"operation": "read", "resource": "synthetic:record", "token": token}
            if request != expected:
                response = {"ok": False, "error": "capability denied"}
            else:
                proof = hashlib.sha256((credential + ":read:synthetic:record").encode()).hexdigest()
                event_path.write_text(json.dumps({"credential_used": True, "proof": proof}) + "\n",
                                      encoding="utf-8")
                response = {"ok": True, "result": {"value": "synthetic-result"}}
            peer.sendall(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
