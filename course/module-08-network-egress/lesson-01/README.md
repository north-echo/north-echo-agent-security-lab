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

<!-- source: course/module-08-network-egress/lesson-01/local_http.py format=code -->
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
<!-- /source -->

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

<!-- source: course/module-08-network-egress/lesson-01/connect_probe.py format=code -->
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
<!-- /source -->

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
