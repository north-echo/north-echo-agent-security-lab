#!/usr/bin/env python3
"""Send one capability-bound operation request."""

import json
from pathlib import Path
import socket
import sys

if len(sys.argv) != 8:
    raise SystemExit(f"usage: {sys.argv[0]} SOCKET TOKEN OP RESOURCE AUDIENCE RUN INPUT_JSON")
request = {
    "token": Path(sys.argv[2]).read_text(encoding="utf-8").strip(),
    "operation": sys.argv[3],
    "resource": sys.argv[4],
    "audience": sys.argv[5],
    "run_id": sys.argv[6],
    "input": json.loads(sys.argv[7]),
}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
    stream.settimeout(5)
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
