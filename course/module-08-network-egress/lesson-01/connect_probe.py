#!/usr/bin/env python3
"""Attempt one TCP connection and report the network namespace identity."""

import json
import os
import socket
import sys

if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} PORT")

result = {
    "network_namespace": os.readlink("/proc/self/ns/net"),
    "connected": False,
}
try:
    with socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=1) as stream:
        stream.sendall(b"GET / HTTP/1.0\r\nHost: synthetic.test\r\n\r\n")
        response = bytearray()
        while len(response) < 8192:
            chunk = stream.recv(min(1024, 8192 - len(response)))
            if not chunk:
                break
            response.extend(chunk)
        body = bytes(response).split(b"\r\n\r\n", 1)[-1]
        result["connected"] = body == b"synthetic-loopback-service\n"
except OSError as error:
    result["error"] = f"{type(error).__name__}: {error}"
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["connected"] else 1)
