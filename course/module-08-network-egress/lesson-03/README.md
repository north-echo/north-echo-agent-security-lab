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

<!-- source: course/module-08-network-egress/lesson-03/egress_broker.py format=code -->
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
<!-- /source -->

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

<!-- source: course/module-08-network-egress/lesson-03/redirect_services.py format=code -->
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
<!-- /source -->

### Source, line by line

- The argv guard takes two ports and a readiness path. Both servers bind only to `127.0.0.1`.
- `Allowed.do_GET` sends a relative redirect for `/same`, an absolute redirect to `blocked.test` for `/escape`, and otherwise a fixed allowed body.
- `Protected.do_GET` returns a different synthetic body. There is no real secret.
- The protected server runs in a daemon thread while the main thread runs the allowed server. They share a process but listen at distinct ports.
- The ready file is written after both binds succeed. A port collision is a setup failure, not a policy denial.
- SIGTERM/SIGINT request normal process exit. The `finally` block closes both servers, stops the background serving loop, and removes readiness.

### The bounded client

<!-- source: course/module-08-network-egress/lesson-03/broker_client.py format=code -->
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
<!-- /source -->

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
