# North Echo field manual - Module 08

This chapter is self-contained for the guided networking exercises and independent lab. Every service is synthetic and loopback-only; no public or LAN endpoint is used.

<!-- PAGEBREAK -->

## Module overview

# Module 08 - Isolate the network and mediate egress

Remove the workload's inherited IP network, then expose only a narrow HTTP capability through a filesystem Unix socket. The broker uses an explicit synthetic name-to-loopback map, binds requests to a run identity, and authorizes every redirect again.

Play in order: `08.01`, `08.02`, `08.03`, then `module-08`.

Outcomes:

- prove a new network namespace starts with loopback down and cannot reach a service on host loopback;
- distinguish removing direct IP connectivity from authorizing one mediated operation;
- carry a structured request over `AF_UNIX` without restoring an IP route;
- authorize a synthetic hostname, resolved address, port, path shape, and run identity;
- reauthorize redirects before contacting their destinations;
- bound request and response sizes and cleanly remove the broker socket.

All services are synthetic and bind only to `127.0.0.1`. The exercises do not create veth devices, routes, firewall rules, DNS traffic, or public requests. Prerequisites are Modules 01-07 and Linux support for unprivileged user plus network namespaces.

<!-- PAGEBREAK -->

## Lesson 08.01

# 08.01 - Remove the inherited IP network

## Goal

Prove that a new network namespace has different kernel network state and cannot reach a synthetic service bound to the parent namespace's loopback address.

## Exercise 1 - Inspect the boundary

Read both complete programs before running them:

```bash
sed -n '1,240p' local_http.py
sed -n '1,240p' connect_probe.py
```

### Source, line by line

- `local_http.py` refuses a pre-existing readiness path, creates one `HTTPServer` on `127.0.0.1`, then writes `ready`. It exits after one request and removes the readiness file in `finally`. Its fixed response is synthetic and its disabled request log avoids host-identifying noise.
- `connect_probe.py` calls `readlink` on `/proc/self/ns/net`, so the namespace identity comes from the process being tested.
- `socket.create_connection` makes exactly one bounded attempt to `127.0.0.1:PORT`; its one-second timeout prevents a failed path from hanging.
- The probe records either `connected: true` or the exception type and returns nonzero on denial. It does not treat an error message alone as proof.

Choose a lesson-local high port, start the one-request service, and connect from the current namespace:

```bash
PORT=$((42000 + $$ % 10000))
READY="$PWD/server.ready"
python3 local_http.py "$PORT" "$READY" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -f "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -f "$READY" && break; sleep 0.1; done
test -f "$READY"
python3 connect_probe.py "$PORT"
wait "$server_pid"
trap - EXIT
```

### Line by line

- The arithmetic selects a high synthetic port without privileged binding. A collision is harmless and visible; choose another value if needed.
- `&` launches only the local service; `$!` captures its exact PID for bounded cleanup.
- `trap` names that exact PID and lesson-local readiness path. It does not use a process-name pattern.
- The bounded loop waits for the server-created readiness evidence before connecting.
- The probe should print its network-namespace link, `connected: true`, and exit zero. `wait` proves the one-request server exited.

## Exercise 2 - Enter an empty network namespace

Start another one-request service, then run the probe after `unshare` creates user and network namespaces:

```bash
python3 local_http.py "$PORT" "$READY" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -f "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -f "$READY" && break; sleep 0.1; done
test -f "$READY"
set +e
unshare --user --map-root-user --net python3 connect_probe.py "$PORT"
isolated_status=$?
set -e
printf 'isolated_status=%s\n' "$isolated_status"
kill "$server_pid"
wait "$server_pid" 2>/dev/null || true
trap - EXIT
```

### Line by line

- `--user --map-root-user` gives the calling user namespace-local capability to create and configure its new network namespace; it does not grant host root.
- `--net` creates a new network namespace. Its loopback device starts down and it has no inherited host interfaces or routes.
- `set +e` permits the expected failed connection to be observed. The saved status must be nonzero.
- Killing the exact still-waiting server proves the isolated request never reached it.

Expected output includes a different `net:[NUMBER]`, `connected: false`, and usually `Network is unreachable`. Error text varies; the stable facts are the distinct namespace and failed connection.

## Exercise 3 - Repair loopback, not host reachability

Intentional mistake: assume that enabling loopback reconnects the namespace to the parent's `127.0.0.1`.

```bash
python3 local_http.py "$PORT" "$READY" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -f "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -f "$READY" && break; sleep 0.1; done
test -f "$READY"
set +e
unshare --user --map-root-user --net sh -c 'ip link set lo up; ip -brief address show lo; python3 connect_probe.py "$1"' sh "$PORT"
loopback_status=$?
set -e
printf 'private_loopback_status=%s\n' "$loopback_status"
kill "$server_pid"
wait "$server_pid" 2>/dev/null || true
trap - EXIT
```

### Line by line

- `ip link set lo up` changes only the new namespace's loopback device.
- The quoted script receives the port as `$1`; no lesson value is interpolated as shell code.
- `127.0.0.1` now refers to the new namespace itself, not the parent's loopback service, so the connection remains denied (commonly `Connection refused`).
- The repair is conceptual: use a non-IP mediation channel in Lesson 08.02 instead of adding a veth path that broadens connectivity.

## Checkpoint and troubleshooting

```bash
test "$isolated_status" -ne 0
test "$loopback_status" -ne 0
```

- If `unshare` reports `Operation not permitted`, use the documented disposable VM and its narrow user-namespace setup; do not weaken a work host.
- If the first connection fails, select another high port and ensure no stale lesson process remains.
- Checkpoint: explain why both namespaces can have an interface named `lo` while their `127.0.0.1` services remain disjoint.

### Complete guided source listings

#### `local_http.py`

```python
#!/usr/bin/env python3
"""One bounded synthetic HTTP response on loopback."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"synthetic-loopback-service\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
ready = Path(sys.argv[2])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")
server = HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
ready.write_text("ready\n", encoding="utf-8")
try:
    server.handle_request()
finally:
    server.server_close()
    ready.unlink(missing_ok=True)
```

<!-- PAGEBREAK -->

#### `connect_probe.py`

```python
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
        result["connected"] = b"synthetic-loopback-service" in stream.recv(4096)
except OSError as error:
    result["error"] = f"{type(error).__name__}: {error}"
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["connected"] else 1)
```

<!-- PAGEBREAK -->

## Lesson 08.02

# 08.02 - Reach one service through a Unix-socket broker

## Goal

Keep the workload's IP network empty while giving it one structured operation through a filesystem `AF_UNIX` socket.

## Exercise 1 - Read the three complete components

```bash
sed -n '1,240p' synthetic_http.py
sed -n '1,280p' one_host_broker.py
sed -n '1,240p' broker_client.py
```

### Source, line by line

- `synthetic_http.py` serves a fixed response on host loopback and writes a lesson-local readiness file after binding. It is the only IP service.
- `one_host_broker.py` refuses an existing socket path, binds `AF_UNIX`, sets mode `0600`, and accepts one client.
- The broker requires an exact JSON object containing the allowed run, host, port, and `/ok` path. Extra fields fail because dictionary equality is exact.
- Only after authorization does the broker connect to literal `127.0.0.1`. The requested synthetic name becomes the HTTP `Host` header, not a DNS lookup.
- The broker bounds its input line and upstream body, returns one JSON line, closes descriptors, and unlinks its socket in `finally`.
- `broker_client.py` preserves typed fields in JSON, uses `AF_UNIX`, half-closes its write side, and reads one response line.

## Exercise 2 - Compare direct and mediated paths

Launch exact owned processes with a cleanup trap:

```bash
PORT=$((43000 + $$ % 9000))
RUN_ID="lesson-$$"
SOCKET="$PWD/broker.sock"
READY="$PWD/service.ready"
python3 synthetic_http.py "$PORT" "$READY" & service_pid=$!
python3 one_host_broker.py "$SOCKET" "$RUN_ID" allowed.test "$PORT" & broker_pid=$!
trap 'kill "$broker_pid" "$service_pid" 2>/dev/null || true; wait "$broker_pid" "$service_pid" 2>/dev/null || true; rm -f "$SOCKET" "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -S "$SOCKET" && test -f "$READY" && break; sleep 0.1; done
test -S "$SOCKET"
test -f "$READY"
```

### Line by line

- Both background PIDs come from processes launched in this shell and are saved immediately.
- The socket is placed in the disposable lesson workspace, not a shared system directory.
- The bounded readiness loop checks the actual socket type; it does not sleep indefinitely.
- The trap removes only exact PIDs and the exact lesson path.

First prove direct IP still fails, then use the Unix socket:

```bash
set +e
unshare --user --map-root-user --net python3 -c 'import socket,sys; socket.create_connection(("127.0.0.1",int(sys.argv[1])),1)' "$PORT"
direct_status=$?
set -e
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" "$RUN_ID" allowed.test "$PORT" /ok
wait "$broker_pid"
kill "$service_pid"
wait "$service_pid" 2>/dev/null || true
trap - EXIT
```

### Line by line

- The direct probe runs inside a new empty network namespace and must return nonzero.
- The second `unshare` creates another empty network namespace, but Unix sockets are filesystem objects and remain reachable through the shared workspace mount.
- The broker, outside the network namespace, performs the one authorized loopback request and returns `approved-through-broker`.
- The one-request broker exits and removes its socket. The exact service PID is then stopped and reaped.

The workload did not gain a route, interface, DNS resolver, or general TCP proxy. It gained one operation-shaped capability.

## Exercise 3 - Break and repair request binding

Repeat the launch block, then intentionally send the wrong run ID:

```bash
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" wrong-run allowed.test "$PORT" /ok
```

Expected JSON has `"ok": false` and `request is not authorized`; the upstream service receives nothing. The mistake is treating access to the socket pathname as sufficient authority. Repair it by sending the exact `$RUN_ID` and retain both checks in later policy.

## Checkpoint and troubleshooting

```bash
test "$direct_status" -ne 0
test ! -e "$SOCKET"
```

- If the socket path already exists, remove it only after proving it is the exact lesson path and no owned broker is running.
- If the client gets `Connection refused`, inspect the bounded readiness loop and exact saved PID.
- Checkpoint: explain why an `AF_UNIX` connection crosses this network-namespace boundary without restoring any IP destination authority.

### Complete guided source listings

#### `synthetic_http.py`

```python
#!/usr/bin/env python3
"""Serve synthetic content on host loopback until interrupted."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
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

<!-- PAGEBREAK -->

#### `one_host_broker.py`

```python
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
```

<!-- PAGEBREAK -->

#### `broker_client.py`

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
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request, sort_keys=True).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    print(stream.makefile("r", encoding="utf-8").readline(), end="")
```

<!-- PAGEBREAK -->

## Lesson 08.03

# 08.03 - Reauthorize names, ports, redirects, and runs

## Goal

Replace one exact request with a reusable fail-closed broker that validates policy once, authorizes every hop, and never performs live DNS.

## Exercise 1 - Read the complete policy engine

```bash
sed -n '1,260p' egress_broker.py
sed -n '1,240p' redirect_services.py
sed -n '1,200p' broker_client.py
```

### Broker, block by block

- `load_policy` accepts exactly `run_id` and `destinations`. Every synthetic hostname maps to one literal IPv4 loopback address and a nonempty set of ports. Non-loopback policy is rejected before listening.
- `authorize` compares the run ID, parses only credential-free `http` URLs, rejects fragments and malformed authorities, then checks the hostname and port against the policy map. It builds an origin-form path and a controlled `Host` header.
- `fetch` accepts exactly four request fields. It authorizes the initial URL and repeats `authorize` after every redirect. It limits redirects, connection time, and response bytes.
- `receive_line` permits one bounded newline-terminated JSON document. This prevents an unbounded stream from becoming broker memory authority.
- `serve` refuses a pre-existing path, creates a mode-`0600` Unix socket, handles each request independently, converts expected failures into `ok: false`, and unlinks its socket in `finally`.
- Signal handlers request a clean loop exit. Setup or policy failure returns nonzero and never falls through to a permissive mode.

`redirect_services.py` creates an allowed service and a protected service, both on loopback, then writes a readiness file. `/same` redirects within the allowed origin; `/escape` redirects to the protected synthetic hostname. The services contain no public endpoint or real secret.

## Exercise 2 - Build a synthetic resolution policy

Choose two ports and write the only allowed name-to-address decision:

```bash
ALLOWED_PORT=$((44000 + $$ % 4000))
PROTECTED_PORT=$((48000 + $$ % 4000))
RUN_ID="redirect-$$"
SOCKET="$PWD/policy-broker.sock"
READY="$PWD/services.ready"
cat > policy.json <<EOF
{
  "run_id": "$RUN_ID",
  "destinations": {
    "allowed.test": {"address": "127.0.0.1", "ports": [$ALLOWED_PORT]}
  }
}
EOF
python3 -m json.tool policy.json
```

### Line by line

- The two ports are distinct high, synthetic endpoints.
- The here-document expands only lesson-controlled shell variables into local JSON.
- `allowed.test` is not sent to DNS. The policy's literal loopback address is the resolver decision the broker will authorize.
- `json.tool` checks syntax before the broker consumes the file.

Launch the services and broker with exact cleanup ownership:

```bash
python3 redirect_services.py "$ALLOWED_PORT" "$PROTECTED_PORT" "$READY" & service_pid=$!
python3 egress_broker.py policy.json "$SOCKET" & broker_pid=$!
trap 'kill "$broker_pid" "$service_pid" 2>/dev/null || true; wait "$broker_pid" "$service_pid" 2>/dev/null || true; rm -f "$SOCKET" "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -S "$SOCKET" && test -f "$READY" && break; sleep 0.1; done
test "$(stat -c '%a' "$SOCKET")" = 600
test -f "$READY"
```

The mode check verifies an effective filesystem property rather than trusting the `chmod` call.

## Exercise 3 - Follow one redirect and deny an escape

```bash
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" "$RUN_ID" allowed.test "$ALLOWED_PORT" /same
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" "$RUN_ID" allowed.test "$ALLOWED_PORT" /escape
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" wrong-run allowed.test "$ALLOWED_PORT" /ok
```

### Line by line

- `/same` produces one relative redirect. `urljoin` keeps the allowed origin, the next loop reauthorizes it, and the result contains `allowed-final` plus `redirects: 1`.
- `/escape` is the intentional attack. The first origin is allowed, but the absolute redirect names `blocked.test` on the protected port. Reauthorization denies it before connection; the protected body is absent.
- The wrong-run request uses an otherwise valid destination but fails before network access.

Intentional mistake: temporarily add `blocked.test` and `$PROTECTED_PORT` to policy. The escape succeeds, proving that a redirect-safe algorithm cannot repair an overbroad policy. Restore the one-destination policy and require `ok: false`.

Stop and verify cleanup:

```bash
kill "$broker_pid" "$service_pid"
wait "$broker_pid" "$service_pid" 2>/dev/null || true
trap - EXIT
test ! -e "$SOCKET"
```

## Checkpoint and troubleshooting

```bash
python3 egress_broker.py policy.json "$PWD/check.sock" & check_pid=$!
for attempt in 1 2 3 4 5; do test -S "$PWD/check.sock" && break; sleep 0.1; done
kill "$check_pid"
wait "$check_pid"
test ! -e "$PWD/check.sock"
```

- If a policy hostname contains uppercase characters, normalize the policy authoring process; the broker intentionally rejects ambiguous casing.
- If a redirect reports `destination is not authorized`, inspect the new hostname and effective port. Do not allow it merely to silence the failure.
- If termination leaves a path, confirm you signaled the exact broker PID and that the process exited normally.
- Checkpoint: identify the authorization decision made before the first connection and the same decision made again before a redirect connection.

### Complete guided source listings

#### `egress_broker.py`

```python
#!/usr/bin/env python3
"""Policy-bound loopback HTTP broker over a Unix-domain socket."""

from __future__ import annotations

import http.client
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import sys
from urllib.parse import urljoin, urlsplit

MAX_LINE = 8192
MAX_BODY = 65536
MAX_REDIRECTS = 4
stopping = False


class Denied(Exception):
    pass


def load_policy(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if set(raw) != {"run_id", "destinations"} or not isinstance(raw["run_id"], str):
        raise Denied("invalid policy shape")
    if not raw["run_id"] or len(raw["run_id"]) > 128 or not isinstance(raw["destinations"], dict):
        raise Denied("invalid policy values")
    destinations = {}
    for host, rule in raw["destinations"].items():
        if not isinstance(host, str) or host != host.lower() or not host or len(host) > 253:
            raise Denied("invalid policy hostname")
        if not isinstance(rule, dict) or set(rule) != {"address", "ports"}:
            raise Denied("invalid destination rule")
        address = ipaddress.ip_address(rule["address"])
        if address.version != 4 or not address.is_loopback:
            raise Denied("only IPv4 loopback destinations are permitted")
        ports = rule["ports"]
        if not isinstance(ports, list) or not ports or any(type(p) is not int or not 1 <= p <= 65535 for p in ports):
            raise Denied("invalid destination ports")
        destinations[host] = {"address": str(address), "ports": frozenset(ports)}
    if not destinations:
        raise Denied("policy has no destinations")
    return {"run_id": raw["run_id"], "destinations": destinations}


def authorize(policy: dict, run_id: object, url: str) -> tuple[str, str, int, str]:
    if run_id != policy["run_id"]:
        raise Denied("run identity is not authorized")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.username is not None or parsed.password is not None:
        raise Denied("only credential-free HTTP URLs are permitted")
    if parsed.fragment or not parsed.hostname or parsed.hostname != parsed.hostname.lower():
        raise Denied("invalid destination URL")
    try:
        port = parsed.port or 80
    except ValueError as error:
        raise Denied("invalid destination port") from error
    rule = policy["destinations"].get(parsed.hostname)
    if rule is None or port not in rule["ports"]:
        raise Denied("destination is not authorized")
    request_path = parsed.path or "/"
    if not request_path.startswith("/") or request_path.startswith("//"):
        raise Denied("invalid request path")
    if parsed.query:
        request_path += "?" + parsed.query
    authority = parsed.hostname if port == 80 else f"{parsed.hostname}:{port}"
    return rule["address"], authority, port, request_path


def fetch(policy: dict, request: dict) -> dict:
    if not isinstance(request, dict) or set(request) != {"run_id", "host", "port", "path"}:
        raise Denied("invalid request shape")
    host, port, path = request["host"], request["port"], request["path"]
    if not isinstance(host, str) or type(port) is not int or not isinstance(path, str):
        raise Denied("invalid request values")
    url = f"http://{host}:{port}{path}"
    for redirects in range(MAX_REDIRECTS + 1):
        address, authority, port, request_path = authorize(policy, request["run_id"], url)
        connection = http.client.HTTPConnection(address, port, timeout=2)
        try:
            connection.request("GET", request_path, headers={"Host": authority, "Connection": "close"})
            response = connection.getresponse()
            body = response.read(MAX_BODY + 1)
            if len(body) > MAX_BODY:
                raise Denied("response body exceeds limit")
            location = response.getheader("Location")
            status = response.status
        finally:
            connection.close()
        if status not in {301, 302, 303, 307, 308}:
            return {"ok": True, "status": status, "body": body.decode("utf-8", "replace"), "redirects": redirects}
        if not location:
            raise Denied("redirect has no location")
        url = urljoin(url, location)
    raise Denied("redirect limit exceeded")


def receive_line(peer: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_LINE:
        chunk = peer.recv(min(1024, MAX_LINE + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if len(data) > MAX_LINE or not data.endswith(b"\n"):
        raise Denied("request must be one bounded line")
    return bytes(data)


def serve(policy: dict, socket_path: Path) -> None:
    if socket_path.exists() or socket_path.is_symlink():
        raise Denied("socket path already exists")
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
                try:
                    request = json.loads(receive_line(peer))
                    response = fetch(policy, request)
                except (Denied, json.JSONDecodeError, UnicodeError, OSError, http.client.HTTPException) as error:
                    response = {"ok": False, "error": str(error)}
                peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)


def stop(_signum, _frame):
    global stopping
    stopping = True


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
        return 2
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        serve(load_policy(Path(sys.argv[1])), Path(sys.argv[2]))
    except (OSError, ValueError, json.JSONDecodeError, Denied) as error:
        print(f"broker setup denied: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

<!-- PAGEBREAK -->

#### `redirect_services.py`

```python
#!/usr/bin/env python3
"""Synthetic allowed and protected HTTP services for redirect exercises."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading

if len(sys.argv) != 4:
    raise SystemExit(f"usage: {sys.argv[0]} ALLOWED_PORT PROTECTED_PORT READY_FILE")
allowed_port, protected_port = map(int, sys.argv[1:3])
ready = Path(sys.argv[3])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")


class Allowed(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/same":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        elif self.path == "/escape":
            self.send_response(302)
            self.send_header("Location", f"http://blocked.test:{protected_port}/secret")
            self.end_headers()
        else:
            body = b"allowed-final\n"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


class Protected(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"protected-service-must-not-be-read\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_arguments):
        pass


protected = ThreadingHTTPServer(("127.0.0.1", protected_port), Protected)
threading.Thread(target=protected.serve_forever, daemon=True).start()
allowed = ThreadingHTTPServer(("127.0.0.1", allowed_port), Allowed)
ready.write_text("ready\n", encoding="utf-8")
try:
    allowed.serve_forever()
finally:
    allowed.server_close()
    protected.shutdown()
    protected.server_close()
    ready.unlink(missing_ok=True)
```

<!-- PAGEBREAK -->

#### `broker_client.py`

```python
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
```

<!-- PAGEBREAK -->

## Independent lab

# Module 08 independent lab - Policy-bound egress broker

Implement `egress_broker.py`. The grader invokes:

```text
python3 egress_broker.py POLICY.json SOCKET
```

The broker must validate the complete policy before creating a mode-`0600` filesystem Unix socket. Policy contains an exact `run_id` and a map from synthetic lowercase hostnames to a literal `address` plus allowed `ports`. Permit only IPv4 loopback addresses; never perform live DNS or make a non-loopback request.

Each client connection carries one bounded newline-terminated JSON object:

```json
{"run_id":"...","host":"allowed.test","port":45123,"path":"/ok"}
```

Require exactly those fields. Authorize the run, hostname, mapped address, and port before each connection. Support bounded HTTP redirects, but parse and reauthorize every new URL before contacting it. Reject credentials, non-HTTP schemes, malformed ports, ambiguous paths, oversized input or output, excessive redirects, extra authority-bearing fields, and upstream failures. Responses are one JSON line: success includes `ok`, `status`, `body`, and `redirects`; denial includes `ok: false` and an error. Clean termination must remove the exact socket.

The fresh external grader starts randomized allowed and protected loopback services. It checks approved access, run binding, hostname and port denial, an allowed relative redirect, denied name and literal-address redirect escapes before protected contact, strict request shape, non-loopback policy rejection, absence of a direct IP path from a new network namespace, socket mode, and teardown.

The starter fails closed without creating a socket. Build from the interfaces and ordering practiced in the three lessons; the lab deliberately does not include a complete implementation.

```bash
python3 -m py_compile egress_broker.py
../../lab-grade module-08
../../lab-grade module-08 --mode exam
```

### Test commands, line by line

- `py_compile` catches syntax errors without starting a listener or contacting a service.
- Practice mode creates fresh names, ports, run identity, and bodies, then reports failed properties with lesson references.
- Exam mode runs the same behavior checks with reduced repair guidance.

Use only the disposable VM and grader-created synthetic loopback services. Do not add veth devices, routes, firewall rules, DNS requests, public endpoints, or a permissive fallback.

## Security model summary

The network namespace removes the workload's inherited IP interfaces and routes. The shared filesystem exposes only a mode-0600 Unix socket. The broker is a separate authority boundary: it accepts a fixed request schema, binds it to a run ID, maps only synthetic names to IPv4 loopback, checks the port, bounds transport data, and repeats authorization after redirects. Network isolation does not make broker policy correct, and broker policy does not replace the filesystem, syscall, privilege, or resource controls from earlier modules.

## Glossary

- **Network namespace:** per-namespace interfaces, routes, and related network state.
- **Loopback:** an address that refers only to the network namespace containing it.
- **Unix-domain socket:** a local IPC endpoint addressed through the filesystem rather than IP routing.
- **Mediated egress:** a narrower process performs an approved network operation for an isolated caller.
- **Reauthorization:** repeating policy checks after a request changes, including at every redirect.
- **Run binding:** requiring a request to name the exact synthetic execution identity authorized by policy.
