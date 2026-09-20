#!/usr/bin/env python3
"""A one-request Unix-socket broker for one exact synthetic destination."""

import http.client
import json
import os
from pathlib import Path
import socket
import signal
import sys


def stop(_signum, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT")
socket_path, allowed_run, allowed_host, port_text = sys.argv[1:]
allowed_port = int(port_text)
path = Path(socket_path)
if path.exists() or path.is_symlink():
    raise SystemExit("socket path already exists")

listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(socket_path)
os.chmod(socket_path, 0o600)
listener.listen(1)
listener.settimeout(300)
try:
    peer, _ = listener.accept()
    with peer:
        peer.settimeout(2)
        with peer.makefile("rb") as incoming:
            line = incoming.readline(8193)
        if len(line) > 8192 or not line.endswith(b"\n"):
            raise ValueError("request must be one bounded JSON line")
        request = json.loads(line)
        if request != {"run_id": allowed_run, "host": allowed_host, "port": allowed_port, "path": "/ok"}:
            response = {"ok": False, "error": "request is not authorized"}
        else:
            connection = http.client.HTTPConnection("127.0.0.1", allowed_port, timeout=2)
            connection.request("GET", "/ok", headers={"Host": allowed_host})
            upstream = connection.getresponse()
            raw_body = upstream.read(65537)
            connection.close()
            if len(raw_body) > 65536:
                raise ValueError("response body exceeds limit")
            body = raw_body.decode("utf-8", "replace")
            response = {"ok": True, "status": upstream.status, "body": body}
        peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
finally:
    listener.close()
    path.unlink(missing_ok=True)
