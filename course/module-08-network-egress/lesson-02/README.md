# 08.02 - Reach one service through a Unix-socket broker

## Outcomes and prerequisites

Complete 08.01 first. You will keep a workload's IP network isolated, send one structured request over a different channel, and distinguish possession of a socket pathname from permission to perform an operation. Reuse Module 07's owned service lifecycle.

## Concepts before commands

A **broker** is a separate process that holds authority the caller does not hold. Here the broker can contact one VM-loopback HTTP service. The caller can ask for one operation; it cannot choose an arbitrary destination or supply a shell command.

`AF_UNIX` means local interprocess communication rather than IP networking. This lesson uses a **pathname socket** in the shared student workspace. A new network namespace does not hide that pathname. Linux's **abstract** Unix-socket namespace is different and is isolated by network namespaces; do not generalize this result to every Unix socket.

Mode `0600` limits access to the owning account on Linux. It does not separate two processes running as that same account. The run ID is a context-binding field, not a secret credential or proof of who sent the request. These limits matter: this is a small mediation demonstration, not a complete multi-user authentication system.

Predict: should an isolated caller reach the HTTP service directly? Should it reach the pathname socket? Which process makes the eventual TCP connection?

## Prepare and read all three programs

From the course root in the VM:

```bash
./lab-start 08.02
cd .student/08.02
pwd
ls -l synthetic_http.py one_host_broker.py broker_client.py
cat synthetic_http.py
cat one_host_broker.py
cat broker_client.py
```

These commands create the working copy, enter it, and display each source. Use `nano one_host_broker.py` if you want to inspect it interactively; no source edit is required.

### The synthetic upstream service

<!-- source: course/module-08-network-egress/lesson-02/synthetic_http.py format=code -->
```python
#!/usr/bin/env python3
"""Serve synthetic content on host loopback until interrupted."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"approved-through-broker\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


def stop(_signum, _frame):
    raise SystemExit(0)


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
ready = Path(sys.argv[2])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")
server = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
ready.write_text("ready\n", encoding="utf-8")
try:
    server.serve_forever()
finally:
    server.server_close()
    ready.unlink(missing_ok=True)
```
<!-- /source -->

### Source, line by line

- The HTTP imports, handler class, response headers, byte body, and quiet logging repeat 08.01.
- `ThreadingHTTPServer` can handle separate requests in separate threads. The small fixed body is synthetic, not a credential.
- The argument guard requires a port and readiness filename. Existing files or dangling symlinks cause refusal before bind.
- The literal address confines the listener to parent-namespace loopback.
- Readiness is written only after the server binds. A failed bind cannot masquerade as a ready fixture.
- `serve_forever` continues until stopped. SIGTERM/SIGINT raise `SystemExit`, allowing `finally` to close the server and remove readiness.
- That cleanup is cooperative: SIGKILL or a crash can leave evidence behind. We verify cleanup rather than assuming it.

### The one-request broker

<!-- source: course/module-08-network-egress/lesson-02/one_host_broker.py format=code -->
```python
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
```
<!-- /source -->

### Source, line by line

- `socket_path, allowed_run, allowed_host, port_text` unpack four arguments. Converting the port makes the policy value an integer.
- Refusing an existing path avoids overwriting another socket or stale lesson evidence.
- `AF_UNIX, SOCK_STREAM` creates a local byte-stream listener. `bind` creates its pathname; `chmod` restricts account access; `listen(1)` enables accepting a connection.
- `accept` returns a new connected socket, `peer`. The listener and the connected peer are distinct descriptors.
- The listener's 300-second idle timeout is a teaching convenience. The peer's two-second timeout bounds an individual blocking operation, not an absolute whole-session deadline.
- `makefile("rb")` exposes a binary reader over the peer. `readline(8193)` permits detecting a request exceeding the 8192-byte limit. Requiring a newline supplies the JSON framing practiced in Module 04.
- `json.loads` turns the line into Python data. Equality against the fixed dictionary requires the same fields and values; an extra field is not silently accepted.
- The rejected branch constructs a denial and never calls `HTTPConnection`. Only the accepted branch contacts literal loopback.
- The synthetic hostname is an HTTP Host header, not a DNS lookup. The caller cannot change the actual connection address.
- `read(65537)` detects a body larger than 65536 bytes. Decoding with replacement handles non-UTF-8 bytes for display, not as a policy decision.
- `sendall` returns one newline-terminated JSON response. The outer `finally` closes the listener and removes its exact socket.
- There is only **one** `accept`, not a loop. Both a successful request and a denied request consume this broker instance. Invalid JSON can terminate it without a structured response; 08.03 adds reusable request handling.

### The isolated client

<!-- source: course/module-08-network-egress/lesson-02/broker_client.py format=code -->
```python
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
```
<!-- /source -->

### Source, line by line

- The argument guard requires socket, run ID, host, port, and path. JSON preserves the integer port rather than flattening the request into command text.
- A `with` block closes the Unix socket on exit. Its timeout prevents an indefinitely idle call.
- `connect` uses the socket pathname; `sendall` sends the complete request plus its delimiter.
- `shutdown(SHUT_WR)` declares that no more request bytes will be sent while retaining the read direction.
- The bounded response read limits memory used by this small client. The response must be a dictionary with an actual Boolean `ok`.
- The printed JSON is normalized for inspection. Exit status 0 means `ok: true`; status 1 means denial or another client failure. Inspect the JSON as well as the status.

## Exercise 1 - Start registered, bounded services

Define the helper and lesson-local names:

```bash
start_broker_service() {
  NE_UNIT="north-echo-$(id -u)-08-02-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 08.02 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 08.02 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
NE_PORT=$((43000 + $$ % 9000))
NE_RUN="lesson-$$"
NE_SOCKET="$PWD/broker.sock"
NE_READY="$PWD/service.ready"
```

The helper registers ownership before launch, preserves literal argv, and retains Module 07's runtime and resource backstops. No `--wait` is used because the service must remain available for another command. The run label uses this shell's PID to distinguish this exercise; it is not a cryptographic identity.

Launch both components:

```bash
start_broker_service /usr/bin/python3 "$PWD/synthetic_http.py" "$NE_PORT" "$NE_READY"
NE_HTTP_UNIT="$NE_UNIT"
start_broker_service /usr/bin/python3 "$PWD/one_host_broker.py" "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_PORT"
NE_BROKER_UNIT="$NE_UNIT"
for attempt in {1..50}; do test -S "$NE_SOCKET" && test -f "$NE_READY" && break; sleep 0.1; done
test -S "$NE_SOCKET"
test -f "$NE_READY"
test "$(stat -c '%a' "$NE_SOCKET")" = 600
```

Save each unit name for diagnosis. The bounded readiness loop checks an actual socket and the upstream's ready file. `stat` checks the effective mode. If any test fails, stop here: inspect the exact units with `journalctl --user -u "$NE_HTTP_UNIT" -u "$NE_BROKER_UNIT" --no-pager`, then run owned cleanup.

## Exercise 2 - Compare direct and mediated access

```bash
NE_DIRECT_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 -c \
  'import socket,sys; socket.create_connection(("127.0.0.1",int(sys.argv[1])),1)' \
  "$NE_PORT" || NE_DIRECT_STATUS=$?
test "$NE_DIRECT_STATUS" -ne 0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_PORT" /ok > approved.json
python3 -m json.tool approved.json
../../lab-cleanup 08.02
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

The first command cannot reach the parent namespace's listener. A connection traceback is expected; a failed `unshare` is not evidence of network isolation. The second command uses the same namespace-creation flags but reaches the pathname socket. Its successful JSON demonstrates that namespace creation and the mediated path both work.

The expected body is `approved-through-broker\n`. The broker, not the isolated caller, opens the IP connection. Owned cleanup stops any remaining registered service and checks its identity; it does not kill by a guessed PID or name prefix.

## Exercise 3 - Deliberate wrong-run request, then repair

Repeat **only the launch block** from Exercise 1 to create fresh services. Send an otherwise valid request with a wrong context:

```bash
NE_DENIED_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" wrong-run allowed.test "$NE_PORT" /ok > denied.json || NE_DENIED_STATUS=$?
python3 -m json.tool denied.json
test "$NE_DENIED_STATUS" -eq 1
../../lab-cleanup 08.02
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

Expect `ok: false` and `request is not authorized`. Reading the rejected branch explains why this implementation does not contact the upstream for that request. A missing body alone would not prove absence of contact.

The denied call consumed the one-shot broker. Merely retrying against its removed socket is **not** a repair. Repeat the launch block again, then restore the correct run value:

```bash
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_PORT" /ok > repaired.json
../../lab-cleanup 08.02
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

for name in ("approved.json", "repaired.json"):
    result = json.loads(Path(name).read_text())
    assert result["ok"] is True
    assert result["status"] == 200
    assert result["body"] == "approved-through-broker\n"
denied = json.loads(Path("denied.json").read_text())
assert denied["ok"] is False
assert denied["error"] == "request is not authorized"
print("DIRECT DENIAL AND MEDIATED REPAIR: PASS")
PY
test "$NE_DIRECT_STATUS" -ne 0
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

Explain which process held IP authority and why socket permission alone did not authorize the operation. An absent socket after a request is normal for this one-shot broker. A pre-existing socket before launch requires verified cleanup/reset, not blind removal. A pathname that is too long cannot fit Linux's Unix-socket address; keep the course near your VM home, not deeply nested.

After a five-minute pause, the runtime backstop may have stopped a fixture. Clean up and relaunch instead of treating stale readiness as a successful test. Return with `cd ../..`; `./lab-reset 08.02` discards this workspace after owned cleanup.

## Source truth

Linux [unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html) describes pathname sockets and their permissions; [network_namespaces(7)](https://man7.org/linux/man-pages/man7/network_namespaces.7.html) distinguishes abstract-socket isolation. Python's [socket API](https://docs.python.org/3.14/library/socket.html) supplies stream, shutdown, and timeout behavior. These explain the mechanism, not an authentication guarantee.
