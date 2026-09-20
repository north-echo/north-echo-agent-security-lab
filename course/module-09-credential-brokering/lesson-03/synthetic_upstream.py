#!/usr/bin/env python3
"""Synthetic credential-protected operation service over a Unix socket."""

import json
import os
from pathlib import Path
import signal
import socket
import sys

stopping = False


def stop(_signum, _frame):
    global stopping
    stopping = True


if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} CREDENTIAL RESOURCE VALUE SOCKET")
credential = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
resource, value, socket_text = sys.argv[2:]
socket_path = Path(socket_text)
if socket_path.exists() or socket_path.is_symlink():
    raise SystemExit("upstream socket path already exists")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(str(socket_path))
os.chmod(socket_path, 0o600)
listener.listen(8)
listener.settimeout(0.2)
try:
    while not stopping:
        try:
            peer, _ = listener.accept()
        except TimeoutError:
            continue
        with peer:
            peer.settimeout(2)
            try:
                with peer.makefile("rb") as incoming:
                    line = incoming.readline(16385)
                if len(line) > 16384 or not line.endswith(b"\n"):
                    raise ValueError("request must be one bounded line")
                request = json.loads(line)
                allowed = request == {"credential": credential, "operation": "read", "resource": resource, "input": {}}
                response = {"ok": True, "result": {"value": value}} if allowed else {"ok": False, "error": "upstream denied"}
            except (ValueError, UnicodeError, OSError):
                response = {"ok": False, "error": "invalid upstream request"}
            try:
                peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
            except OSError:
                pass
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
