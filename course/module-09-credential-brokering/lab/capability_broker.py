#!/usr/bin/env python3
"""Fail-closed starter for the Module 09 broker interface."""

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
    raise SystemExit(f"usage: {sys.argv[0]} POLICY SIGNING_KEY CREDENTIAL SOCKET")
socket_path = Path(sys.argv[4])
if socket_path.exists() or socket_path.is_symlink():
    raise SystemExit("socket path already exists")
signal.signal(signal.SIGTERM, stop)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(str(socket_path))
os.chmod(socket_path, 0o600)
listener.listen(4)
listener.settimeout(0.2)
try:
    while not stopping:
        try:
            peer, _ = listener.accept()
        except TimeoutError:
            continue
        with peer:
            peer.recv(16384)
            peer.sendall(json.dumps({"ok": False, "error": "capability policy is not implemented"}).encode() + b"\n")
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
