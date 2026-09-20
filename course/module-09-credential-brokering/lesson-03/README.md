# 09.03 - Deny replay and confused-deputy substitution

## Outcomes and prerequisites

Complete 09.01 and 09.02. You will trace a request across client, broker, and synthetic upstream; observe single-process replay prevention; and repair a request that does not match its capability. Use Module 07's registered lifecycle and Module 08's socket/JSON vocabulary.

## Concepts before commands

There are three different authorities here:

- The **issuer** holds an HMAC key and can mint operation capabilities.
- The **broker** holds that key for verification and a separate fake service credential. It checks a capability before using its broader upstream authority.
- The **client** submits a bearer token and an operation request. Its normal interface receives neither key nor credential.

The upstream is a fourth role: it accepts the fake service credential and performs one synthetic read. It is separate from the broker so a test can observe whether a rejected request nevertheless caused contact.

These are **teaching roles**, not yet independently isolated operating-system identities. All commands run as your VM account and files remain in its workspace. Mode 0600 does not stop that same account reading its own key files. This lesson proves request validation and the absence of a credential in the demonstrated client exchange; it does not prove that a malicious same-account workload cannot reach any secret file. Combine mediation with the filesystem, process, and resource controls already studied.

A nonce replay cache is also scoped. This implementation remembers consumption only while this broker process lives. Restart loses that memory. Do not reuse the same still-valid token/key/run after restart and call the result durable one-use enforcement. A production design would need coordinated durable consumption or a fresh authorization epoch; that design is outside this exercise.

## Prepare and read the system

From the course root in the disposable VM:

```bash
./lab-start 09.03
cd .student/09.03
pwd
ls -l capability_broker.py synthetic_upstream.py mint_token.py broker_client.py
cat capability_broker.py
cat synthetic_upstream.py
cat mint_token.py
cat broker_client.py
```

You may navigate each with `nano` and its exact filename. There is no source edit in this exercise: the deliberate mistake will be an incorrectly bound request. Read before creating short-lived tokens.

### The broker

<!-- source: course/module-09-credential-brokering/lesson-03/capability_broker.py format=code -->
```python
#!/usr/bin/env python3
"""Use fake credentials only after a capability passes every binding check."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import signal
import socket
import stat
import sys
import time

MAX_LINE = 16384
MAX_UPSTREAM = 65536
MAX_USED_NONCES = 4096
stopping = False


class Denied(Exception):
    pass


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError) as error:
        raise Denied("input is not canonical JSON") from error


def encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def decode(segment: str) -> bytes:
    if not isinstance(segment, str) or not segment or "=" in segment or len(segment) > 8192:
        raise Denied("invalid token encoding")
    try:
        raw = base64.b64decode(segment + "=" * (-len(segment) % 4), altchars=b"-_", validate=True)
    except (ValueError, binascii.Error) as error:
        raise Denied("invalid token encoding") from error
    if encode(raw) != segment:
        raise Denied("noncanonical token encoding")
    return raw


def load_policy(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    expected = {"version", "audience", "run_id", "max_ttl", "upstream_socket", "permissions"}
    if not isinstance(raw, dict) or set(raw) != expected or type(raw["version"]) is not int or raw["version"] != 1:
        raise Denied("invalid policy shape")
    if not all(isinstance(raw[name], str) and 1 <= len(raw[name]) <= 128 for name in ("audience", "run_id")):
        raise Denied("invalid policy identity")
    if type(raw["max_ttl"]) is not int or not 1 <= raw["max_ttl"] <= 300:
        raise Denied("invalid maximum lifetime")
    if not isinstance(raw["upstream_socket"], str):
        raise Denied("upstream socket must be a path string")
    upstream = Path(raw["upstream_socket"])
    if not upstream.is_absolute():
        raise Denied("upstream socket must be absolute")
    permissions = raw["permissions"]
    if not isinstance(permissions, dict) or not permissions:
        raise Denied("policy has no permissions")
    for resource, operations in permissions.items():
        if not isinstance(resource, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,127}", resource):
            raise Denied("invalid policy resource")
        if not isinstance(operations, list) or not operations or any(not isinstance(op, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", op) for op in operations):
            raise Denied("invalid policy operation")
    return raw


def receive_line(peer: socket.socket, limit: int) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= limit:
        chunk = peer.recv(min(1024, limit + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if len(data) > limit or not data.endswith(b"\n") or data.count(b"\n") != 1:
        raise Denied("request must be one bounded line")
    return bytes(data)


def verify_token(policy: dict, key: bytes, request: dict) -> str:
    required = {"token", "operation", "resource", "audience", "run_id", "input"}
    if not isinstance(request, dict) or set(request) != required:
        raise Denied("invalid request shape")
    if not all(isinstance(request[name], str) for name in ("token", "operation", "resource", "audience", "run_id")):
        raise Denied("invalid request values")
    try:
        payload_text, signature_text = request["token"].split(".")
    except ValueError as error:
        raise Denied("invalid token shape") from error
    supplied = decode(signature_text)
    expected = hmac.new(key, payload_text.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(supplied, expected):
        raise Denied("invalid token signature")
    try:
        claims = json.loads(decode(payload_text))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise Denied("invalid token payload") from error
    claim_names = {"version", "operation", "resource", "audience", "run_id", "issued_at", "expires_at", "nonce", "input_sha256"}
    if not isinstance(claims, dict) or set(claims) != claim_names or type(claims["version"]) is not int or claims["version"] != 1:
        raise Denied("invalid token claims")
    for name in ("operation", "resource", "audience", "run_id", "nonce", "input_sha256"):
        if not isinstance(claims[name], str):
            raise Denied("invalid token claim type")
    if type(claims["issued_at"]) is not int or type(claims["expires_at"]) is not int:
        raise Denied("invalid token time type")
    now = int(time.time())
    if claims["issued_at"] > now or claims["expires_at"] <= now:
        raise Denied("capability is not currently valid")
    if claims["expires_at"] <= claims["issued_at"] or claims["expires_at"] - claims["issued_at"] > policy["max_ttl"]:
        raise Denied("capability lifetime exceeds policy")
    if not re.fullmatch(r"[0-9a-f]{32}", claims["nonce"]):
        raise Denied("invalid capability nonce")
    if not re.fullmatch(r"[0-9a-f]{64}", claims["input_sha256"]):
        raise Denied("invalid input digest")
    bindings = ("operation", "resource", "audience", "run_id")
    if any(claims[name] != request[name] for name in bindings):
        raise Denied("request does not match capability")
    if request["audience"] != policy["audience"] or request["run_id"] != policy["run_id"]:
        raise Denied("request identity is not authorized")
    if request["operation"] not in policy["permissions"].get(request["resource"], []):
        raise Denied("operation is not permitted")
    digest = hashlib.sha256(canonical(request["input"])).hexdigest()
    if not hmac.compare_digest(digest, claims["input_sha256"]):
        raise Denied("request input does not match capability")
    return claims["nonce"]


def call_upstream(policy: dict, credential: str, request: dict) -> object:
    message = {"credential": credential, "operation": request["operation"], "resource": request["resource"], "input": request["input"]}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
        stream.settimeout(2)
        stream.connect(policy["upstream_socket"])
        stream.sendall(canonical(message) + b"\n")
        stream.shutdown(socket.SHUT_WR)
        raw = receive_line(stream, MAX_UPSTREAM)
    if credential.encode() in raw:
        raise Denied("upstream attempted credential disclosure")
    response = json.loads(raw)
    if not isinstance(response, dict) or set(response) != {"ok", "result"} or response["ok"] is not True:
        raise Denied("upstream denied operation")
    return response["result"]


def serve(policy: dict, key: bytes, credential: str, socket_path: Path) -> None:
    if socket_path.exists() or socket_path.is_symlink():
        raise Denied("broker socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.2)
    used_nonces: set[str] = set()
    try:
        while not stopping:
            try:
                peer, _ = listener.accept()
            except TimeoutError:
                continue
            with peer:
                peer.settimeout(2)
                try:
                    request = json.loads(receive_line(peer, MAX_LINE))
                    nonce = verify_token(policy, key, request)
                    if nonce in used_nonces:
                        raise Denied("capability replay denied")
                    if len(used_nonces) >= MAX_USED_NONCES:
                        raise Denied("replay cache capacity reached")
                    used_nonces.add(nonce)
                    result = call_upstream(policy, credential, request)
                    response = {"ok": True, "result": result}
                except (Denied, json.JSONDecodeError, UnicodeError, OSError) as error:
                    response = {"ok": False, "error": str(error)}
                try:
                    peer.sendall(canonical(response) + b"\n")
                except OSError:
                    pass
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)


def stop(_signum, _frame):
    global stopping
    stopping = True


def main() -> int:
    if len(sys.argv) != 5:
        print(f"usage: {sys.argv[0]} POLICY SIGNING_KEY CREDENTIAL SOCKET", file=sys.stderr)
        return 2
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        policy = load_policy(Path(sys.argv[1]))
        key_path, credential_path = Path(sys.argv[2]), Path(sys.argv[3])
        if key_path.is_symlink() or credential_path.is_symlink():
            raise Denied("broker secret files cannot be symlinks")
        if not stat.S_ISREG(key_path.stat().st_mode) or not stat.S_ISREG(credential_path.stat().st_mode):
            raise Denied("broker secret paths must be regular files")
        key = key_path.read_bytes()
        credential = credential_path.read_text(encoding="utf-8").strip()
        if not 32 <= len(key) <= 128 or not 8 <= len(credential) <= 256:
            raise Denied("invalid broker secret material")
        if stat.S_IMODE(key_path.stat().st_mode) != 0o600 or stat.S_IMODE(credential_path.stat().st_mode) != 0o600:
            raise Denied("broker secret files must be mode 0600")
        serve(policy, key, credential, Path(sys.argv[4]))
    except (Denied, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"broker setup denied: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- /source -->

### Source, block by block

- The constants bound client input, upstream response, and remembered nonce count. `Denied` identifies an application-policy failure.
- `canonical` uses the same sorted compact Python JSON convention as 09.02. It rejects non-finite numeric values and converts serialization failures into policy denials.
- `encode` creates the unpadded URL-safe representation. `decode` bounds a segment, rejects supplied padding, asks the decoder to validate its alphabet, and re-encodes to require the exact canonical text.
- `load_policy` requires the complete versioned field set. Audience and run are bounded strings; maximum lifetime is an integer from 1 through 300; the upstream pathname must be absolute.
- The resource and operation patterns accept only the small identifiers used by the course. Every resource maps to a nonempty operation list.
- `receive_line` reads at most one bounded newline-terminated message. A size bound limits memory; the caller must also set a socket timeout to bound idle operations.
- `verify_token` requires exactly token, operation, resource, audience, run, and input. Required textual fields must actually be strings.
- The token must split into two segments. HMAC is recomputed over the payload text and compared to the decoded authenticator before claims are trusted.
- The decoded claim object must have the expected keys and version. Identity/digest/nonce fields are strings; timestamps must be real integers, not Booleans.
- Time checks reject future issue times, expired tokens, nonpositive intervals, and intervals exceeding policy. A token with a valid HMAC can still have an invalid lifetime.
- Regular expressions check nonce and input-digest shape; shape is not a replacement for the HMAC or the input comparison.
- The first binding comparison matches token claims to the caller's requested operation, resource, audience, and run.
- A separate comparison matches audience/run to **broker policy**. A self-consistent token/request pair for some other broker is not sufficient.
- The resource allowlist checks whether policy permits the requested operation. The input hash then binds the exact parsed input according to the course serialization convention.
- Verification returns the nonce only after all these checks. It does not contact upstream.
- `call_upstream` builds a new request with the broker-held credential and the authorized operation fields. It connects only to the policy's Unix socket, not a caller-selected destination.
- The upstream exchange has a timeout and response-size limit. A literal credential reflected in raw response bytes is rejected. This is a check for the known synthetic value, not general data-loss prevention against every encoding or derived secret.
- `serve` creates a private listener and a fresh `used_nonces` set. After verification it rejects repeats and refuses new consumption once the bounded set is full.
- `used_nonces.add` occurs **before** upstream contact. A failed operation can consume a capability; automatically retrying it would undermine that ordering. There is no exactly-once transaction across broker and upstream.
- Accepted peers have timeouts. Expected errors return `ok: false`; a failed response delivery does not terminate the listener.
- SIGTERM/SIGINT set the stop flag. The short accept timeout allows normal loop exit and exact socket removal in `finally`.
- `main` validates policy and reads the fake key/credential during trusted startup. It checks regular files, rejects symlinks, validates lengths, and requires mode 0600 before listening.
- The credential therefore exists in broker memory before requests arrive. The guarantee is that it is **used in an upstream request only after authorization**, not that it is first read after authorization.

The separate pathname checks and reads assume operator-controlled setup files in this lesson. They are not a race-free secret loader against a malicious process that can modify the same directory. Nor does a mode check establish a separate security domain for same-account clients. Keep this boundary narrower than the claim you make.

### The synthetic upstream

<!-- source: course/module-09-credential-brokering/lesson-03/synthetic_upstream.py format=code -->
```python
#!/usr/bin/env python3
"""Synthetic credential-protected operation service over a Unix socket."""

import json
import os
from pathlib import Path
import signal
import socket
import sys

stopping = False


def stop(_signum, _frame):
    global stopping
    stopping = True


if len(sys.argv) != 5:
    raise SystemExit(f"usage: {sys.argv[0]} CREDENTIAL RESOURCE VALUE SOCKET")
credential = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
resource, value, socket_text = sys.argv[2:]
socket_path = Path(socket_text)
if socket_path.exists() or socket_path.is_symlink():
    raise SystemExit("upstream socket path already exists")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
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
                with peer.makefile("rb") as incoming:
                    line = incoming.readline(16385)
                if len(line) > 16384 or not line.endswith(b"\n"):
                    raise ValueError("request must be one bounded line")
                request = json.loads(line)
                allowed = request == {"credential": credential, "operation": "read", "resource": resource, "input": {}}
                response = {"ok": True, "result": {"value": value}} if allowed else {"ok": False, "error": "upstream denied"}
            except (ValueError, UnicodeError, OSError):
                response = {"ok": False, "error": "invalid upstream request"}
            try:
                peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
            except OSError:
                pass
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
```
<!-- /source -->

### Source, line by line

- The arguments identify a fake credential file, one resource, one harmless return value, and a socket pathname.
- The credential is read at startup. Its value is not passed in argv; only its filename is.
- Existing socket paths are refused. The listener uses `AF_UNIX`, mode 0600, and an accept timeout.
- Each peer has its own timeout and bounded newline read. Invalid data becomes a denial rather than an unrestricted operation.
- Dictionary equality requires the fake credential, operation `read`, configured resource, and empty-object input.
- Success returns a `result` object containing the synthetic value, not the credential. The program is intentionally not a general database.
- Normal stop closes the listener and removes its exact pathname. SIGKILL cannot execute that cleanup.

### The issuer

<!-- source: course/module-09-credential-brokering/lesson-03/mint_token.py format=code -->
```python
#!/usr/bin/env python3
"""Mint a lesson capability; signing material stays outside the client."""

import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sys
import time


def encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


if len(sys.argv) != 9:
    raise SystemExit(f"usage: {sys.argv[0]} KEY TOKEN OP RESOURCE AUDIENCE RUN TTL INPUT_JSON")
key = Path(sys.argv[1]).read_bytes()
ttl = int(sys.argv[7])
if not 1 <= ttl <= 300:
    raise SystemExit("TTL must be 1..300 seconds")
issued = int(time.time())
input_value = json.loads(sys.argv[8])
claims = {
    "version": 1,
    "operation": sys.argv[3],
    "resource": sys.argv[4],
    "audience": sys.argv[5],
    "run_id": sys.argv[6],
    "issued_at": issued,
    "expires_at": issued + ttl,
    "nonce": secrets.token_hex(16),
    "input_sha256": hashlib.sha256(canonical(input_value)).hexdigest(),
}
payload = encode(canonical(claims))
signature = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
Path(sys.argv[2]).write_text(payload + "." + signature + "\n", encoding="utf-8")
print("capability minted")
```
<!-- /source -->

### Source, line by line

- The encoding and canonicalization functions repeat 09.02's token format.
- The argument guard distinguishes key/token filenames from operation context and input JSON.
- Lifetime is bounded before a token is written. Broker policy can impose a smaller maximum than the issuer's 300-second ceiling.
- Timestamps use current wall-clock seconds; nonce generation supplies a fresh 16-byte value as hexadecimal text.
- The input digest covers parsed, deterministically serialized JSON.
- HMAC authenticates the payload text. The file receives `payload.authenticator` plus a newline; stdout reports only that minting completed.

The issuer is trusted with the shared key. This is not an interface to expose to an untrusted workload with unrestricted signing requests.

### The client

<!-- source: course/module-09-credential-brokering/lesson-03/broker_client.py format=code -->
```python
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
```
<!-- /source -->

### Source, line by line

- The client reads the bearer token from its filename and parses input JSON; it does not read the signing-key or credential files.
- It sends the six exact fields in one newline-terminated request over the broker pathname.
- The write half-close finishes the request direction; the read direction remains open.
- A timeout and size bound limit the response observation. The decoded object must contain a Boolean `ok`.
- Status 0 means an accepted operation; status 1 represents denial or client failure. Inspect the returned JSON, not only the status.

## Exercise 1 - Create synthetic setup material

```bash
(umask 077
 printf '%s' 'FAKE-SIGNING-KEY-09.03-ONLY-000000000000' > signing.key
 printf '%s' 'FAKE-UPSTREAM-CREDENTIAL-09.03' > credential.txt
)
test "$(stat -c '%a' signing.key)" = 600
test "$(stat -c '%a' credential.txt)" = 600
NE_RUN="run-$$"
NE_AUDIENCE="records.lesson"
NE_RESOURCE="record:alpha"
NE_UPSTREAM="$PWD/upstream.sock"
NE_BROKER="$PWD/broker.sock"
python3 - "$NE_RUN" "$NE_AUDIENCE" "$NE_UPSTREAM" <<'PY'
import json
from pathlib import Path
import sys

policy = {
    "version": 1, "run_id": sys.argv[1], "audience": sys.argv[2],
    "max_ttl": 120, "upstream_socket": sys.argv[3],
    "permissions": {"record:alpha": ["read"], "record:beta": ["read"]}
}
Path("policy.json").write_text(json.dumps(policy, indent=2) + "\n")
PY
python3 -m json.tool policy.json
```

The creation mask is scoped to a subshell; effective permissions are checked afterward. These exact fake strings have no real-system authority. The policy permits reads of alpha and beta so a later mismatch isolates **token binding**, not merely the absence of beta from policy. The upstream itself serves only alpha.

## Exercise 2 - Launch registered services

```bash
start_capability_service() {
  NE_UNIT="north-echo-$(id -u)-09-03-$(python3 -c 'import secrets; print(secrets.token_hex(4))').service"
  ../../scripts/labctl.py register-unit 09.03 "$NE_UNIT" || return
  systemd-run --user --collect --quiet --expand-environment=no --service-type=exec \
    --unit="$NE_UNIT" --description="North Echo 09.03 workspace=$PWD" \
    --property=RuntimeMaxSec=300s --property=TimeoutStopSec=3s \
    --property=MemoryMax=67108864 --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=CPUQuota=50% -- "$@"
}
start_capability_service /usr/bin/python3 "$PWD/synthetic_upstream.py" \
  "$PWD/credential.txt" "$NE_RESOURCE" synthetic-record-value "$NE_UPSTREAM"
NE_UPSTREAM_UNIT="$NE_UNIT"
start_capability_service /usr/bin/python3 "$PWD/capability_broker.py" \
  "$PWD/policy.json" "$PWD/signing.key" "$PWD/credential.txt" "$NE_BROKER"
NE_BROKER_UNIT="$NE_UNIT"
for attempt in {1..50}; do test -S "$NE_BROKER" && test -S "$NE_UPSTREAM" && break; sleep 0.1; done
test -S "$NE_BROKER"
test -S "$NE_UPSTREAM"
test "$(stat -c '%a' "$NE_BROKER")" = 600
test "$(stat -c '%a' "$NE_UPSTREAM")" = 600
```

The helper retains exact ownership registration, literal argv, resource ceilings, and runtime backstop. Absolute source/setup paths avoid depending on the service manager's working directory. Readiness checks effective socket types and permissions.

If startup fails, stop before minting. Inspect `journalctl --user -u "$NE_UPSTREAM_UNIT" -u "$NE_BROKER_UNIT" --no-pager`, then `../../lab-cleanup 09.03`. Do not broaden file modes or disable SELinux.

Mint and spend one capability promptly:

```bash
(umask 077; python3 mint_token.py signing.key token.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" 120 '{}')
python3 broker_client.py "$NE_BROKER" token.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" '{}' > approved.json
python3 -m json.tool approved.json
```

Expect `ok: true` and `result: {"value": "synthetic-record-value"}`. This establishes a working upstream path before testing denials. The client was given a token file, not the credential value. Again, that is an interface observation, not proof of same-account file isolation.

## Exercise 3 - Deny replay and repair a mismatched request

```bash
NE_REPLAY_STATUS=0
python3 broker_client.py "$NE_BROKER" token.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" '{}' \
  > replay.json || NE_REPLAY_STATUS=$?
(umask 077; python3 mint_token.py signing.key deputy.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" 120 '{}')
NE_DEPUTY_STATUS=0
python3 broker_client.py "$NE_BROKER" deputy.txt read record:beta "$NE_AUDIENCE" "$NE_RUN" '{}' \
  > wrong-resource.json || NE_DEPUTY_STATUS=$?
python3 -m json.tool replay.json
python3 -m json.tool wrong-resource.json
test "$NE_REPLAY_STATUS" -eq 1
test "$NE_DEPUTY_STATUS" -eq 1
```

Expect `capability replay denied` for the spent token. Expect `request does not match capability` for the fresh alpha token submitted with beta. Both operations are policy-allowed in general, but this particular token does not grant beta.

Repair the request, not the token verifier:

```bash
python3 broker_client.py "$NE_BROKER" deputy.txt read "$NE_RESOURCE" "$NE_AUDIENCE" "$NE_RUN" '{}' > repaired.json
python3 -m json.tool repaired.json
```

The mismatch failed before nonce consumption, so the still-valid fresh token can now authorize its exact operation. By contrast, the earlier successfully spent token remains consumed. If reading took more than two minutes, mint fresh test tokens and repeat the sequence; do not remove expiry checks.

## Checkpoint, cleanup, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

for name in ("approved.json", "repaired.json"):
    observed = result(name)
    assert observed["ok"] is True
    assert observed["result"] == {"value": "synthetic-record-value"}
assert result("replay.json") == {"ok": False, "error": "capability replay denied"}
assert result("wrong-resource.json") == {"ok": False, "error": "request does not match capability"}
for name in ("approved.json", "repaired.json", "replay.json", "wrong-resource.json"):
    assert "FAKE-UPSTREAM-CREDENTIAL-09.03" not in Path(name).read_text()
print("OPERATION BINDING AND PROCESS-LIFETIME REPLAY: PASS")
PY
../../lab-cleanup 09.03 --dry-run
../../lab-cleanup 09.03
test ! -e "$NE_BROKER"
test ! -e "$NE_UPSTREAM"
```

The checker establishes the expected successful and denied exchanges, with no literal credential in those observations. It does not prove every possible disclosure channel is closed. The lab grader independently counts upstream calls during protected attempts; that adds evidence that rejection occurred before contact.

The cleanup planner verifies registered ownership before stopping services. Both socket paths must disappear on normal termination. A pre-existing path or an ownership mismatch is a reason to inspect/reset this exact lesson, never to kill processes by prefix.

Explain why the fake credential and HMAC key are different authorities, why a valid authenticator is insufficient for a substituted request, why failed upstream operations can consume a nonce, and what is lost on broker restart.

Return with `cd ../..`; `./lab-reset 09.03` discards the local fake setup, tokens, observations, and working copy after owned cleanup. Start a fresh run for replay practice. Do not reuse this public fake key as real security material.

## Source truth

Python's [HMAC documentation](https://docs.python.org/3.14/library/hmac.html) covers shared-key authentication, not encryption or durable replay prevention. Its [socket API](https://docs.python.org/3.14/library/socket.html) describes stream operations and timeouts. Linux [unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html) describes pathname permissions; they must not be mistaken for a separate same-account identity boundary.
