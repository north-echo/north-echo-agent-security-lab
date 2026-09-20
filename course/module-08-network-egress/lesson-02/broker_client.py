#!/usr/bin/env python3
"""Send one structured request to a filesystem Unix socket."""

import json
import socket
import sys

if len(sys.argv) != 6:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET RUN_ID HOST PORT PATH")
request = {
    "run_id": sys.argv[2],
    "host": sys.argv[3],
    "port": int(sys.argv[4]),
    "path": sys.argv[5],
}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.settimeout(12)
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request, sort_keys=True).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    with stream.makefile("rb") as incoming:
        line = incoming.readline(524289)
    if len(line) > 524288 or not line.endswith(b"\n"):
        raise SystemExit("response must be one bounded JSON line")
    response = json.loads(line)
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        raise SystemExit("invalid response shape")
    print(json.dumps(response, sort_keys=True))
raise SystemExit(0 if response["ok"] else 1)
