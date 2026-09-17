#!/usr/bin/env python3
"""Send one JSON request to the lesson broker."""

import json
import socket
import sys

if len(sys.argv) != 6:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT PATH")
request = {"run_id": sys.argv[2], "host": sys.argv[3], "port": int(sys.argv[4]), "path": sys.argv[5]}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    print(stream.makefile("r", encoding="utf-8").readline(), end="")
