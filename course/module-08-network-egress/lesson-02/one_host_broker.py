#!/usr/bin/env python3
"""A one-request Unix-socket broker for one exact synthetic destination."""

import http.client
import json
import os
from pathlib import Path
import socket
import sys

if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT")
socket_path, allowed_run, allowed_host, port_text = sys.argv[1:]
allowed_port = int(port_text)
path = Path(socket_path)
if path.exists():
    raise SystemExit("socket path already exists")

listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(socket_path)
os.chmod(socket_path, 0o600)
listener.listen(1)
try:
    peer, _ = listener.accept()
    with peer:
        request = json.loads(peer.makefile("rb").readline(8192))
        if request != {"run_id": allowed_run, "host": allowed_host, "port": allowed_port, "path": "/ok"}:
            response = {"ok": False, "error": "request is not authorized"}
        else:
            connection = http.client.HTTPConnection("127.0.0.1", allowed_port, timeout=2)
            connection.request("GET", "/ok", headers={"Host": allowed_host})
            upstream = connection.getresponse()
            body = upstream.read(65536).decode("utf-8", "replace")
            connection.close()
            response = {"ok": True, "status": upstream.status, "body": body}
        peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
finally:
    listener.close()
    path.unlink(missing_ok=True)
