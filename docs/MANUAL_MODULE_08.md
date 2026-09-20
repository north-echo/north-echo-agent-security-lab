<!-- source: course/module-08-network-egress/README.md format=markdown -->
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

## Learning route and limits

Begin with a working connection before removing the network view. Otherwise a stopped server could look like successful isolation. Next separate direct connectivity from a permitted broker operation. Finally follow a redirect through a fresh authorization decision and compare correct enforcement with an incorrectly broad policy.

The network namespace, Unix-socket pathname, policy file, and broker process are different parts of the design. Be able to point to the decision each controls. A run ID is a context label, not authentication; mode 0600 does not isolate same-account processes; these small HTTP fixtures are not production services.

Each lesson includes exact preparation commands, complete sources, observations, a deliberate mistake and repair, and registered cleanup. Keep the resource limits and runtime backstops from Module 07. Do not disable SELinux to make a demonstration work.

Readiness for the independent lab means you can explain why a parser is not an authorizer, why an allowed first hop does not authorize a redirect, and why absence of a protected body is weaker evidence than measuring that no protected request occurred.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lesson-01/README.md format=markdown -->
# 08.01 - Remove the inherited IP network

## Outcomes and prerequisites

Complete Modules 01-07 first. You will compare network namespace identities, distinguish parent and private loopback, and observe a synthetic service through a working baseline before testing isolation.

## Concepts before commands

An IP **address** identifies an endpoint in a network context; a **port** identifies a transport service at that address. TCP provides a stream of bytes, not one message per receive call. HTTP gives those bytes a request/response structure. We use a tiny fixed HTTP response only to distinguish the intended service from an unrelated open port.

`127.0.0.1` is **loopback**: it refers to the current network namespace, not universally to your VM or Mac. A new network namespace gets its own interfaces and routes. Its loopback interface initially exists but is down. Enabling that interface does not connect it to the parent's loopback.

In this chapter, the parent environment is the disposable Linux VM. Every service binds only to its loopback address. No public address, LAN target, real credential, DNS query, route, or firewall change is part of the lesson.

## Prepare and read both programs

From the course root in the VM:

```bash
./lab-start 08.01
cd .student/08.01
pwd
ls -l local_http.py connect_probe.py
cat local_http.py
cat connect_probe.py
```

The commands prepare, enter, locate, and display the student sources. You can open either with `nano` and its exact filename, but no edit is required for the baseline. Do not start the server until you have read how it stops.

### The one-response service

```python
#!/usr/bin/env python3
"""One bounded synthetic HTTP response on loopback."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import signal
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


def stop(_signum, _frame):
    raise SystemExit(0)


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} PORT READY_FILE")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
ready = Path(sys.argv[2])
if ready.exists() or ready.is_symlink():
    raise SystemExit("ready path already exists")
server = HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler)
server.timeout = 300
ready.write_text("ready\n", encoding="utf-8")
try:
    server.handle_request()
finally:
    server.server_close()
    ready.unlink(missing_ok=True)
```

### Source, line by line

- `HTTPServer` supplies HTTP connection handling; `BaseHTTPRequestHandler` supplies the request parser and response methods.
- `class Handler(BaseHTTPRequestHandler)` defines a specialized handler. Python calls its `do_GET` method for an HTTP GET request; `self` is that handler instance.
- The `b` prefix creates bytes. Content-Length counts those bytes, not characters in an arbitrary Unicode string.
- `send_response`, `send_header`, and `end_headers` write the response metadata before `wfile.write` writes the body.
- Overriding `log_message` with `pass` suppresses routine request logs; it does not change policy.
- The stop handler raises `SystemExit` for SIGTERM/SIGINT so normal Python cleanup runs. SIGKILL cannot run such cleanup.
- The argv guard requires a port and readiness path. Refusing an existing path avoids silently replacing earlier evidence.
- Binding to `127.0.0.1` keeps the service in the parent namespace's loopback environment. Only after a successful bind does the program write readiness.
- `handle_request` handles at most one request. Its idle timeout and the service runtime limit below keep it bounded.
- `finally` closes the server and removes the readiness file on normal completion or handled termination.

### The connection observer

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
```

### Source, line by line

- The initial dictionary records the observer's kernel-reported network namespace and starts with no successful observation.
- `socket.create_connection` makes one time-bounded TCP connection to the supplied local port.
- The byte request includes an HTTP method, path, version, Host header, and the blank line ending the headers. The synthetic Host string is not a DNS lookup.
- `sendall` sends the complete small request or raises an error.
- The receive loop collects at most 8 KiB. It stops on end-of-stream and does not assume one TCP receive contains the whole response.
- Splitting at the header/body separator locates the fixed response body. Exact body equality establishes that the expected synthetic service answered, not just that a port accepted a connection.
- `except OSError` records connection/timeout failure. The final exit status is 0 only when the expected body was observed.

This is a bounded observer for the supplied HTTP/1.0 fixture, not a general HTTP client or a proof about every possible network path.

## Exercise 1 - Register and start a working parent service

Reuse Module 07's owned user-unit lifecycle. Define the following helper in this shell:

```bash
start_network_service() {
  NE_UNIT="north-echo-$(id -u)-08-01-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 08.01 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 08.01 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=2s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
NE_PORT=$((42000 + $$ % 10000))
NE_READY="$PWD/server.ready"
```

### Line by line

- The helper creates and registers an exact lesson-owned name before starting anything.
- Unlike 07.01's foreground observation, this service has no `--wait` or `--pipe`: it must remain available while you run a separate client. Its output goes to the user journal.
- `--service-type=exec` makes startup wait until the executable has been invoked; a readiness file still proves the later bind completed.
- Literal argv, exact description, resource limits, and a five-minute runtime backstop are retained.
- `"$@"` forwards the helper's supplied executable and arguments without joining them.
- Shell arithmetic selects a high port. It is a candidate, not a reservation; a collision must be diagnosed.
- The readiness path stays inside this prepared workspace.

Start the service and wait only a bounded time for readiness:

```bash
start_network_service /usr/bin/python3 "$PWD/local_http.py" "$NE_PORT" "$NE_READY"
for attempt in {1..50}; do test -f "$NE_READY" && break; sleep 0.1; done
test -f "$NE_READY"
readlink /proc/self/ns/net
python3 connect_probe.py "$NE_PORT" > parent-result.json
python3 -m json.tool parent-result.json
../../lab-cleanup 08.01
```

The loop allows up to five seconds for the server-created file, not an indefinite sleep. If readiness fails, stop before the client and inspect `journalctl --user -u "$NE_UNIT" --no-pager`; do not interpret a missing server as isolation. The parent result must report `connected: true` and status 0. Cleanup collects/stops only registered, verified units. The one-request server should already have exited.

## Exercise 2 - Test the new network namespace

Predict which namespace handle and connection result should change:

```bash
start_network_service /usr/bin/python3 "$PWD/local_http.py" "$NE_PORT" "$NE_READY"
for attempt in {1..50}; do test -f "$NE_READY" && break; sleep 0.1; done
test -f "$NE_READY"
NE_ISOLATED_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 connect_probe.py "$NE_PORT" \
  > isolated-result.json || NE_ISOLATED_STATUS=$?
python3 -m json.tool isolated-result.json
printf 'isolated status=%s\n' "$NE_ISOLATED_STATUS"
../../lab-cleanup 08.01
```

`--user --map-root-user` supplies namespace-local setup authority; `--net` creates the different network view. The quoted-free executable and arguments are still separate words. The expected failed probe's status is saved without changing interactive shell error options.

Expect a different `net:[NUMBER]`, `connected: false`, and a nonzero status. Error wording may mention an unreachable network; it is not the proof by itself. Parent readiness, a successful previous baseline, changed namespace identity, and the failed bounded connection are the evidence together.

## Exercise 3 - Repair the misconception about loopback

The intentional mistake is assuming that bringing up private loopback restores access to the parent's service. Test it without adding any external network path:

```bash
start_network_service /usr/bin/python3 "$PWD/local_http.py" "$NE_PORT" "$NE_READY"
for attempt in {1..50}; do test -f "$NE_READY" && break; sleep 0.1; done
test -f "$NE_READY"
NE_LOOPBACK_STATUS=0
unshare --user --map-root-user --net sh -c \
  'ip link set lo up && ip -brief address show lo >&2 && exec /usr/bin/python3 connect_probe.py "$1"' \
  namespace-observer "$NE_PORT" > private-loopback-result.json || NE_LOOPBACK_STATUS=$?
python3 -m json.tool private-loopback-result.json
printf 'private loopback status=%s\n' "$NE_LOOPBACK_STATUS"
../../lab-cleanup 08.01
```

The shell program is single-quoted so the outer shell does not consume `$1`. The next word supplies its `$0`; the port becomes `$1`, as practiced in 02.02. `&&` stops if namespace-local interface setup fails. Interface display goes to stderr so stdout remains one JSON document. Only this new namespace's loopback is changed.

The connection still fails, commonly with connection refused. Repair the mental model: private loopback reaches this namespace, not its parent. Lesson 08.02 will introduce a filesystem-mediated channel instead of restoring general IP connectivity.

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

parent = json.loads(Path("parent-result.json").read_text())
for name in ("isolated-result.json", "private-loopback-result.json"):
    child = json.loads(Path(name).read_text())
    assert parent["connected"] is True
    assert child["connected"] is False
    assert child["network_namespace"] != parent["network_namespace"]
print("NETWORK VIEW AND CONNECTION EVIDENCE: PASS")
PY
test ! -e "$NE_READY"
```

The checker compares parsed observations, not a locale-dependent error message. A failed `unshare` produces no valid child observation and cannot pass. After owned cleanup, the readiness path must be absent. If a forced termination leaves stale evidence, use lesson reset after verifying unit cleanup; do not blindly remove arbitrary socket/readiness paths.

If you waited beyond the service's runtime backstop, recreate the service before testing. If the port is already bound, choose another high port and repeat the working baseline. Never change host routes, firewall policy, or SELinux enforcement for this exercise.

Return with `cd ../..`; `./lab-reset 08.01` discards this lesson's work after verified cleanup. Save notes first.

## Source truth

[network_namespaces(7)](https://man7.org/linux/man-pages/man7/network_namespaces.7.html) describes isolated network state. Python's [socket documentation](https://docs.python.org/3.14/library/socket.html) describes stream reads and timeouts; [http.server](https://docs.python.org/3.14/library/http.server.html) describes the synthetic server API, which is not recommended as a production web server.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lesson-02/README.md format=markdown -->
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

### Source, line by line

- The HTTP imports, handler class, response headers, byte body, and quiet logging repeat 08.01.
- `ThreadingHTTPServer` can handle separate requests in separate threads. The small fixed body is synthetic, not a credential.
- The argument guard requires a port and readiness filename. Existing files or dangling symlinks cause refusal before bind.
- The literal address confines the listener to parent-namespace loopback.
- Readiness is written only after the server binds. A failed bind cannot masquerade as a ready fixture.
- `serve_forever` continues until stopped. SIGTERM/SIGINT raise `SystemExit`, allowing `finally` to close the server and remove readiness.
- That cleanup is cooperative: SIGKILL or a crash can leave evidence behind. We verify cleanup rather than assuming it.

### The one-request broker

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
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lesson-03/README.md format=markdown -->
# 08.03 - Reauthorize names, ports, redirects, and runs

## Outcomes and prerequisites

Complete 08.01 and 08.02. You will read a reusable broker, author a small synthetic destination policy, observe an allowed redirect, and verify that a changed destination needs a new authorization decision. You will also repair an overbroad policy by restarting the broker with a narrower one.

## Concepts before commands

An HTTP **redirect** is a response telling the client to try another URL. Status 302 plus a Location header does not grant authority to contact that location. A relative location such as `/ok` keeps the current origin; an absolute location can select a different hostname or port.

A URL contains a scheme, authority, path, and optional query/fragment. For `http://allowed.test:45123/ok?view=small`, the scheme is `http`, host is `allowed.test`, port is 45123, path is `/ok`, and query is `view=small`. A **parser** separates these pieces; it does not decide whether they are permitted.

This lesson's resolution policy maps a synthetic name to a literal IPv4 loopback address. No name is sent to a live DNS resolver. The HTTP Host header preserves the approved logical name while the actual connection uses the approved address. Name, address, and port must not become three unrelated decisions.

Keep the limits visible: the run ID is still a context label; mode 0600 does not distinguish same-account clients; the broker permits GET requests to allowed destinations, not arbitrary public browsing. All services remain inside this disposable VM.

## Prepare and read the programs

From the course root:

```bash
./lab-start 08.03
cd .student/08.03
pwd
ls -l egress_broker.py redirect_services.py broker_client.py
cat egress_broker.py
cat redirect_services.py
cat broker_client.py
```

Use `nano egress_broker.py` to navigate the source if desired. The exercises edit policy data, not the policy engine. Read all components before starting listeners.

### The reusable policy engine

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
    if not isinstance(raw, dict) or set(raw) != {"run_id", "destinations"} or not isinstance(raw["run_id"], str):
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
    if any(ord(character) <= 32 or ord(character) == 127 for character in url):
        raise Denied("whitespace and control characters are not permitted")
    try:
        parsed = urlsplit(url)
    except ValueError as error:
        raise Denied("invalid destination URL") from error
    if parsed.scheme != "http" or parsed.username is not None or parsed.password is not None:
        raise Denied("only credential-free HTTP URLs are permitted")
    if parsed.fragment or not parsed.hostname:
        raise Denied("invalid destination URL")
    try:
        port = 80 if parsed.port is None else parsed.port
    except ValueError as error:
        raise Denied("invalid destination port") from error
    if not 1 <= port <= 65535:
        raise Denied("invalid destination port")
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
    if host not in policy["destinations"]:
        raise Denied("destination is not authorized")
    if not 1 <= port <= 65535 or not path.startswith("/") or path.startswith("//"):
        raise Denied("invalid request port or path")
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
                peer.settimeout(2)
                try:
                    request = json.loads(receive_line(peer))
                    response = fetch(policy, request)
                except (Denied, json.JSONDecodeError, UnicodeError, OSError, http.client.HTTPException) as error:
                    response = {"ok": False, "error": str(error)}
                try:
                    peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
                except OSError:
                    pass  # A disconnected client must not stop the listening service.
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

### Source, block by block

- Imports separate HTTP transport, address classification, JSON, filesystem paths, signals, sockets, and URL parsing. None is a substitute for authorization.
- `MAX_LINE`, `MAX_BODY`, and `MAX_REDIRECTS` are explicit bounds. `Denied` is a distinct exception class so policy failures can become structured denials.
- `load_policy` parses the file before listening. `isinstance(raw, dict)` checks its container type; `set(raw)` compares its keys. Both are needed.
- Run IDs must be nonempty bounded strings. Each destination rule has exactly `address` and `ports`; unknown authority-bearing fields are not silently ignored.
- `ip_address` parses a literal address, not a hostname. Requiring version 4 and `is_loopback` keeps every permitted connection inside VM loopback.
- `type(p) is int` deliberately rejects Boolean values, which Python otherwise treats as integer subclasses. Every port must be within 1 through 65535.
- `frozenset` stores an immutable set for membership checks. The resulting in-memory policy is loaded **once at startup**, not reread on every request.
- `authorize` first checks the run value. It rejects whitespace/control characters before parsing because a URL parser can otherwise normalize some input.
- `urlsplit` separates the URL. Scheme, user information, fragment, hostname, effective port, and path shape are then checked explicitly.
- The parser's `hostname` property normalizes case. Policy keys are lowercase; do not claim that this property rejects uppercase characters in every incoming URL.
- An omitted port means 80; explicit port 0 is rejected, not silently replaced with 80.
- The destination lookup binds the parsed name to its stored loopback address and permitted ports. The returned tuple contains the exact address, controlled Host authority, port, and origin-form request path.
- `fetch` requires exactly the four request fields. It rejects unknown hosts before composing a URL and refuses paths beginning with `//`, which could be confused with an authority-bearing reference.
- Each loop iteration calls `authorize` **before** making a connection. `HTTPConnection` receives the approved literal address rather than resolving the supplied hostname.
- `try/finally` closes the HTTP connection even on errors. Reading one byte beyond the body limit detects oversize responses without unbounded allocation.
- Non-redirect responses return their actual HTTP status and body. Here `ok: true` means the broker completed an authorized exchange, not that every HTTP status is a successful application result.
- For redirect responses, `urljoin` constructs the next URL. It can change the origin; the next loop must authorize the result again. Four redirects may be followed; a further redirect is denied.
- `receive_line` accumulates a bounded byte sequence and requires its newline delimiter. It does not execute received strings.
- `serve` refuses an existing socket path, binds a mode-0600 listener, and repeatedly accepts one request per connection. Its short accept timeout lets the loop notice a stop request.
- Each peer gets a blocking-operation timeout. Expected input, policy, or upstream errors become `ok: false`. A disconnected client cannot terminate the service merely because its response cannot be delivered.
- The signal handler sets `stopping`; normal loop exit reaches `finally` and removes the socket. `main` loads policy before calling `serve`, so invalid policy cannot create a permissive listener.

These are small-message and per-operation limits, not a complete defense against all denial-of-service behavior. The service is sequential, has no general concurrent admission control, and does not enforce one absolute deadline across an entire redirect chain. Module 07's runtime/resource backstop remains important. Do not deploy this teaching server publicly.

### The two synthetic destinations

```python
#!/usr/bin/env python3
"""Synthetic allowed and protected HTTP services for redirect exercises."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import sys
import threading


def stop(_signum, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

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

### Source, line by line

- The argv guard takes two ports and a readiness path. Both servers bind only to `127.0.0.1`.
- `Allowed.do_GET` sends a relative redirect for `/same`, an absolute redirect to `blocked.test` for `/escape`, and otherwise a fixed allowed body.
- `Protected.do_GET` returns a different synthetic body. There is no real secret.
- The protected server runs in a daemon thread while the main thread runs the allowed server. They share a process but listen at distinct ports.
- The ready file is written after both binds succeed. A port collision is a setup failure, not a policy denial.
- SIGTERM/SIGINT request normal process exit. The `finally` block closes both servers, stops the background serving loop, and removes readiness.

### The bounded client

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
    stream.settimeout(12)
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request).encode() + b"\n")
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

### Source, line by line

- This is the same structured Unix-socket exchange practiced in 08.02: separate typed fields, one JSON line, a write half-close, and a bounded response read.
- The socket pathname is the connection target. The `host` field is data submitted for broker authorization, not a client-side DNS lookup.
- The `ok` field must be a Boolean. Status 0 corresponds to an accepted exchange; status 1 requires inspecting the denial or error.
- Because this broker loops over connections, a denied request does not consume the whole server. Each client process still sends exactly one request.

## Exercise 1 - Author and inspect the resolution policy

```bash
NE_ALLOWED_PORT=$((44000 + $$ % 4000))
NE_PROTECTED_PORT=$((48000 + $$ % 4000))
NE_RUN="redirect-$$"
NE_SOCKET="$PWD/policy-broker.sock"
NE_READY="$PWD/services.ready"
python3 - "$NE_RUN" "$NE_ALLOWED_PORT" <<'PY'
import json
from pathlib import Path
import sys

policy = {"run_id": sys.argv[1], "destinations": {
    "allowed.test": {"address": "127.0.0.1", "ports": [int(sys.argv[2])]}
}}
Path("policy.json").write_text(json.dumps(policy, indent=2) + "\n")
PY
python3 -m json.tool policy.json
```

Shell arithmetic selects separate high-port ranges; it does not reserve ports. The single-quoted here-document delimiter preserves Python text; the two shell values arrive through argv. `json.dumps` serializes their types safely. `json.tool` checks syntax and displays the policy, but does not prove its destinations are appropriately narrow.

Predict what each request should do before launching anything: `/same` with the right run, `/escape` with the right run, and `/ok` with the wrong run.

## Exercise 2 - Launch registered services

```bash
start_policy_service() {
  NE_UNIT="north-echo-$(id -u)-08-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 08.03 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 08.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
```

This repeats the registered, literal-argv, bounded lifecycle from 08.02. Define the helper once in this shell. Use this launch block every time the exercise asks for a restart:

```bash
start_policy_service /usr/bin/python3 "$PWD/redirect_services.py" "$NE_ALLOWED_PORT" "$NE_PROTECTED_PORT" "$NE_READY"
NE_HTTP_UNIT="$NE_UNIT"
start_policy_service /usr/bin/python3 "$PWD/egress_broker.py" "$PWD/policy.json" "$NE_SOCKET"
NE_BROKER_UNIT="$NE_UNIT"
for attempt in {1..50}; do test -S "$NE_SOCKET" && test -f "$NE_READY" && break; sleep 0.1; done
test -S "$NE_SOCKET"
test -f "$NE_READY"
test "$(stat -c '%a' "$NE_SOCKET")" = 600
```

The readiness and mode tests check created objects, not just command intent. If they fail, stop before testing the policy. Inspect the saved exact unit names with `journalctl --user -u "$NE_HTTP_UNIT" -u "$NE_BROKER_UNIT" --no-pager`, then use `../../lab-cleanup 08.03`.

## Exercise 3 - Observe per-hop authorization

```bash
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /same > same.json
NE_ESCAPE_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /escape > escape.json || NE_ESCAPE_STATUS=$?
NE_RUN_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" wrong-run allowed.test "$NE_ALLOWED_PORT" /ok > wrong-run.json || NE_RUN_STATUS=$?
python3 -m json.tool same.json
python3 -m json.tool escape.json
python3 -m json.tool wrong-run.json
test "$NE_ESCAPE_STATUS" -eq 1
test "$NE_RUN_STATUS" -eq 1
```

Expect `same.json` to contain status 200, `allowed-final\n`, and `redirects: 1`. The first request is allowed, the relative redirect stays within the allowed destination, and that destination is checked again.

Expect `escape.json` to say the destination is not authorized. The allowed server may suggest another hostname; that suggestion does not change policy. Expect the wrong-run response to fail before an upstream connection.

The source ordering shows why denial occurs before protected contact. These response bodies alone do not independently measure contact counts; the independent lab's grader adds that observation. Never equate “secret body not displayed” with “service was never contacted.”

## Exercise 4 - Deliberately broaden policy, then repair it

First stop the exact owned services. Add only the lesson's second synthetic loopback endpoint:

```bash
../../lab-cleanup 08.03
python3 - "$NE_PROTECTED_PORT" <<'PY'
import json
from pathlib import Path
import sys

path = Path("policy.json")
policy = json.loads(path.read_text())
policy["destinations"]["blocked.test"] = {
    "address": "127.0.0.1", "ports": [int(sys.argv[1])]
}
path.write_text(json.dumps(policy, indent=2) + "\n")
PY
```

This is the intentional mistake: the policy now grants authority the intended workload should not have. A correct enforcement algorithm cannot repair an overbroad authorization decision.

Repeat the **launch block from Exercise 2**, then observe the changed result:

```bash
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /escape > broadened.json
python3 -m json.tool broadened.json
../../lab-cleanup 08.03
```

The synthetic protected body is now returned because the second destination was explicitly allowed. Nothing contacted a public service. Restarting mattered: changing the file while the old broker ran would not change its already-loaded policy.

Remove that grant, inspect the repaired policy, then repeat the launch block:

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("policy.json")
policy = json.loads(path.read_text())
del policy["destinations"]["blocked.test"]
path.write_text(json.dumps(policy, indent=2) + "\n")
PY
python3 -m json.tool policy.json
```

After the fresh launch:

```bash
NE_REPAIRED_STATUS=0
unshare --user --map-root-user --net /usr/bin/python3 broker_client.py \
  "$NE_SOCKET" "$NE_RUN" allowed.test "$NE_ALLOWED_PORT" /escape > repaired.json || NE_REPAIRED_STATUS=$?
test "$NE_REPAIRED_STATUS" -eq 1
../../lab-cleanup 08.03
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

same = result("same.json")
assert same["ok"] is True and same["status"] == 200
assert same["redirects"] == 1 and same["body"] == "allowed-final\n"
for name in ("escape.json", "wrong-run.json", "repaired.json"):
    assert result(name)["ok"] is False
assert result("broadened.json")["body"] == "protected-service-must-not-be-read\n"
assert set(result("policy.json")["destinations"]) == {"allowed.test"}
print("REDIRECT REAUTHORIZATION AND POLICY REPAIR: PASS")
PY
test ! -e "$NE_SOCKET"
test ! -e "$NE_READY"
```

Explain two different failures: an algorithm following redirects without reauthorization, and an algorithm correctly enforcing an excessively broad policy. This lesson repairs the latter by narrowing data and restarting.

If the broker refuses policy, inspect the complete startup error before changing a control. If a denied request unexpectedly succeeds, inspect the loaded policy and confirm you restarted after repair. If a readiness file outlives its service, cleanup/reset the exact lesson; do not interpret it as live readiness. Keep SELinux enabled and do not add routes, DNS, public endpoints, or wildcard teardown.

Return with `cd ../..`; `./lab-reset 08.03` discards the prepared workspace after verified cleanup.

## Source truth

Python's [URL parsing documentation](https://docs.python.org/3.14/library/urllib.parse.html) explicitly separates parsing from validation and describes origin-changing joins. The [HTTP client API](https://docs.python.org/3.14/library/http.client.html) documents request/response handling; [signal](https://docs.python.org/3.14/library/signal.html) explains handler execution. This course's authorization contract is narrower than those general-purpose APIs.
<!-- /source -->

---

<!-- source: course/module-08-network-egress/lab/README.md format=markdown -->
# Module 08 independent lab - Policy-bound egress broker

## Your assignment and readiness check

Build a reusable broker that mediates a small HTTP capability for a network-isolated caller. Do not give the caller a route, general TCP proxy, live DNS resolver, or shell command interface.

Before beginning, explain the successful direct baseline and isolated failure from 08.01, the pathname-socket path from 08.02, and the per-redirect decision plus policy-restart requirement from 08.03. If any is unclear, repeat that guided exercise first. This lab asks you to assemble those skills independently, not discover an undocumented API.

## Prepare and inspect the starter

From the course root in your disposable Linux VM:

```bash
./lab-start module-08
cd .student/08.lab
pwd
ls -l egress_broker.py
cat egress_broker.py
nano egress_broker.py
```

The working copy is yours to edit. Keep canonical files under `course/` unchanged. In nano, use Ctrl+O, Enter to save and Ctrl+X to exit with the course's default key bindings.

```python
#!/usr/bin/env python3
"""Starter: validate arguments, but do not expose an unmediated fallback."""

import sys

if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
    raise SystemExit(2)
print("broker policy is not implemented", file=sys.stderr)
raise SystemExit(1)
```

### Starter, line by line

- The docstring describes a deliberately incomplete program, not a working broker.
- `sys.argv` contains the executable filename plus the policy and socket arguments.
- The length check reports interface misuse with status 2.
- Even correctly supplied arguments reach a nonzero, fail-closed exit. The starter creates no listener and opens no network path.
- Replace the incomplete behavior with your implementation; preserving a helpful argument check is useful.

## Required interface and behavior

The grader invokes:

```text
python3 egress_broker.py POLICY.json SOCKET
```

Validate the complete policy **before** creating a listener. The policy has exactly a nonempty bounded `run_id` and a `destinations` dictionary. Each lowercase synthetic hostname maps to exactly a literal `address` and a nonempty list of integer `ports`. Accept only IPv4 loopback addresses and ports 1 through 65535; reject Boolean ports. Never perform live DNS or contact a non-loopback address.

Create a filesystem Unix socket at the supplied path with mode 0600. Refuse a pre-existing path, including a dangling symlink. The socket is an IPC channel, not proof of a client's identity.

Each connection carries one bounded newline-terminated JSON object:

```json
{"run_id":"example-run","host":"allowed.test","port":45123,"path":"/ok"}
```

Require exactly those fields. Bind the run value to policy, validate types and path shape, and authorize the hostname, mapped literal address, and port before every upstream connection. A caller must not override the mapped address with an extra field.

Support relative and absolute HTTP redirects, but parse and reauthorize every resulting destination **before** contacting it. Reject user information, non-HTTP schemes, fragments, invalid ports, control characters, ambiguous paths, oversized messages/bodies, excessive redirects, and upstream failures. Use the practiced limits of 8192 request bytes, 65536 response-body bytes, and at most four followed redirects. Use bounded blocking operations; do not describe these as one absolute end-to-end deadline.

Success is one JSON line with Boolean `ok: true`, integer HTTP `status`, string `body`, and integer `redirects`. Denial is one line with `ok: false` and an `error`. A denied request must not prevent a later valid request. Clean SIGTERM/SIGINT termination must exit successfully and remove the exact socket. Do not implement permissive fallback behavior.

## Map the work to practiced skills

- Policy dictionaries, JSON types, and exact field sets: Module 04 and 08.03.
- A pathname Unix socket with effective mode checking: 08.02.
- Literal address selection without live DNS: 08.02 and 08.03.
- Checking the destination again after a redirect: 08.03.
- Bounded reads, operation timeouts, and response framing: all three networking lessons.
- Signal-aware cleanup and registered manual service launches: 08.01-08.03 and Module 07.
- Distinguishing namespace setup failure from an observed connection denial: 08.01.

Write a short design note before coding: where is the last authorization decision before a connection? What data reaches that connection? Which cleanup path runs if an upstream request fails? Your note is part of your learning evidence, not an automatically graded answer.

## Validate independently

```bash
python3 -m py_compile egress_broker.py
../../lab-grade module-08
../../lab-grade module-08 --mode exam
```

Compilation checks syntax without starting a listener. Practice grading creates fresh synthetic names, ports, run identity, and bodies, then reports failed properties with lesson references. Exam grading uses the same behavior checks with less repair guidance. A passing practice run is not a substitute for explaining the boundary.

The external grader runs randomized allowed/protected loopback services. It checks approved access, run binding, name and port denial, an allowed relative redirect, denied name and literal-address redirect destinations **before protected contact**, exact request shape, refusal of non-loopback policy, a real isolated network observation, mode 0600, and clean teardown. Protected-service contact counts are stronger evidence than merely not displaying its body.

The grader is a finite set of observations. It does not prove absence of every parser ambiguity, a complete authentication design, resilience to every slow client, or production suitability. Retain your own boundary explanation alongside the result.

## Troubleshooting, cleanup, and reset

If no socket appears, inspect syntax, policy validation, path length, and the startup error; do not remove validation to make a listener appear. If a redirect test fails, follow the parsed next destination and the policy decision rather than matching the grader's canary text. If namespace creation fails, repair the supported disposable-VM setup before interpreting connectivity results.

The grader owns and terminates its test processes. If you manually launch services while debugging, use the same registered unit pattern as the lessons, substituting `module-08` in the target, unit-name component, and exact description. Use `../../lab-cleanup module-08 --dry-run`, then `../../lab-cleanup module-08`; do not use wildcard process kills.

Return with `cd ../..`. `./lab-reset module-08` removes the lab workspace and fixtures after verified cleanup. Save your own notes first. Use only synthetic loopback services; keep SELinux enabled and never add host routes, firewall changes, real credentials, or public targets.
<!-- /source -->

## Security model summary

The network namespace replaces the workload's inherited IP network view. These lessons leave the workspace filesystem shared and deliberately expose a mode-0600 pathname Unix socket through it; they do not prove that no other filesystem channel exists. The broker checks a fixed request schema, run context, synthetic name-to-loopback mapping, port, transport bounds, and each redirect. Run context is not authentication and account permissions do not separate same-account processes. Network isolation does not make broker policy correct, and broker policy does not replace filesystem, syscall, privilege, or resource controls.

## Glossary

- **Network namespace:** per-namespace interfaces, routes, and related network state.
- **Loopback:** an address that refers only to the network namespace containing it.
- **Pathname Unix-domain socket:** a local IPC endpoint addressed through the filesystem rather than IP routing; distinct from Linux abstract Unix sockets.
- **Mediated egress:** a narrower process performs an approved network operation for an isolated caller.
- **Reauthorization:** repeating policy checks after a request changes, including at every redirect.
- **Run binding:** requiring a request to name the exact synthetic execution identity authorized by policy.
