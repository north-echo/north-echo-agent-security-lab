# North Echo field manual - Module 09

This chapter is self-contained for the guided credential-brokering exercises and independent lab. Every credential, key, token, service, resource, and value is synthetic and local.

<!-- PAGEBREAK -->

## Module overview

# Module 09 - Broker credentials with operation capabilities

Remove fake credentials from workload environments, then place them behind a local operation broker. Signed, short-lived capabilities bind the exact operation, resource, arguments, audience, run, and one-use nonce without containing the underlying credential.

Play in order: `09.01`, `09.02`, `09.03`, then `module-09`.

Outcomes:

- observe that an environment credential is ambient authority inherited across `exec`;
- remove that authority with an explicit minimal environment;
- distinguish a signed capability from an encrypted secret;
- bind operation, resource, canonical input, audience, run identity, issue time, expiry, and nonce;
- deny tampering, expiry, excessive lifetime, replay, and confused-deputy substitutions before upstream contact;
- prove a broker used a fake credential upstream without returning it to the client.

Every credential, signing key, capability, resource, and upstream service is synthetic and lesson-local. Communication uses filesystem Unix sockets only; no DNS, LAN, public, cloud, employer, or production service is involved. Prerequisites are Modules 01, 04, and 08.

<!-- PAGEBREAK -->

## Lesson 09.01

# 09.01 - Remove ambient credential authority

## Goal

Observe a fake credential crossing `exec` through the environment, trigger a deliberate disclosure, then prove an exact-argv launcher removes it.

## Exercise 1 - Read the complete probes

```bash
sed -n '1,200p' credential_probe.py
sed -n '1,200p' clean_launch.py
```

### Source, line by line

- `credential_probe.py` asks `os.environ` for one explicitly fake variable. It reports presence and length without revealing the value by default.
- Its `leak` mode represents an untrusted tool that can read every inherited variable; it adds the value to JSON only to make the synthetic failure observable.
- `clean_launch.py` requires structured argv, constructs a new environment containing only fixed `PATH` and `LANG`, and calls `subprocess.run` with `shell=False`.
- The child status becomes the launcher status. Failure does not trigger a retry with the inherited environment.

## Exercise 2 - Trigger ambient disclosure

Set a visibly fake lesson value and invoke the probe through a new Python process:

```bash
export NORTH_ECHO_FAKE_CREDENTIAL="FAKE-LESSON-$$-DO-NOT-USE"
python3 credential_probe.py
python3 credential_probe.py leak
```

### Line by line

- `export` places the name in the environment inherited by later `exec` calls. The value is synthetic and must never be replaced with a real credential.
- The first run should report `"present": true` and a nonzero length. This proves inheritance without disclosure.
- The intentional `leak` run prints `leaked_value`. The child needed no separate credential API or user confirmation; possession of the environment was authority.

This does not mean environment variables are always logged. It proves every launched child can read the value and may copy it elsewhere.

## Exercise 3 - Repair inheritance

Run the same exact probe through the clean launcher:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py"
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
unset NORTH_ECHO_FAKE_CREDENTIAL
```

### Line by line

- `/usr/bin/python3` is an exact executable path and the script is a separate argv element.
- Both children should report `"present": false`; `leak` cannot print a value it did not inherit.
- The parent-side `test` proves the fake credential still existed outside the child. The observation is about the launch boundary, not accidental deletion.
- `unset` removes the synthetic value from the lesson shell when the observation is complete.

Intentional mistake: change `env=clean` to `env=os.environ.copy()`. The probe sees the value again. Restore the fixed dictionary and require both modes to report absence.

The repair also removes functionality for a tool that genuinely needs the credential. Lessons 09.02-09.03 restore only an approved operation through a broker; they do not put the credential back into the workload.

## Checkpoint and troubleshooting

```bash
export NORTH_ECHO_FAKE_CREDENTIAL=FAKE-CHECKPOINT
test "$(python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py")" = '{"length": 0, "present": false}'
unset NORTH_ECHO_FAKE_CREDENTIAL
```

- If the child still sees the value, confirm `env=clean` is passed to the exact `subprocess.run` call.
- Do not inspect `/proc` entries belonging to unrelated processes; this exercise needs only its own child environment.
- Checkpoint: explain why a shorter-lived environment credential remains ambient authority during its lifetime.

### Complete guided source listings

#### `credential_probe.py`

```python
#!/usr/bin/env python3
"""Observe whether a synthetic credential crossed exec."""

import json
import os
import sys

name = "NORTH_ECHO_FAKE_CREDENTIAL"
value = os.environ.get(name)
result = {"present": value is not None, "length": len(value) if value else 0}
if len(sys.argv) == 2 and sys.argv[1] == "leak" and value is not None:
    result["leaked_value"] = value
print(json.dumps(result, sort_keys=True))
```

#### `clean_launch.py`

```python
#!/usr/bin/env python3
"""Launch exact argv with a small, credential-free environment."""

import os
import subprocess
import sys

if len(sys.argv) < 2:
    raise SystemExit(f"usage: {sys.argv[0]} COMMAND [ARG...]")
clean = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
run = subprocess.run(sys.argv[1:], shell=False, env=clean, check=False)
raise SystemExit(run.returncode)
```

<!-- PAGEBREAK -->

## Lesson 09.02

# 09.02 - Bind a signed operation capability

## Goal

Mint a short-lived token whose signature covers the exact operation context, then deny tampering, substitution, and expiry.

## Exercise 1 - Read the complete capability tool

```bash
sed -n '1,300p' capability.py
```

### Source, block by block

- `encode` produces unpadded URL-safe base64. It is an encoding, not encryption.
- `canonical` gives JSON one deterministic byte representation; `input_digest` hashes parsed input rather than caller whitespace.
- `mint` bounds lifetime to 1-300 seconds and creates claims for version, operation, resource, audience, run, issue/expiry time, random nonce, and input digest.
- HMAC-SHA256 signs the encoded payload with a lesson-local fake key. The token contains payload plus signature, never a service credential.
- `verify` recomputes the signature with `compare_digest`, compares every request binding, then checks current time inside the validity interval.
- The CLI writes a token file rather than passing a bearer token through process arguments. Every parse or verification failure returns nonzero.

## Exercise 2 - Mint, inspect, and verify

Create a fake signing key with restrictive permissions and mint one read capability:

```bash
umask 077
printf '%s' 'FAKE-SIGNING-KEY-09.02-ONLY-000000000000' > signing.key
RUN_ID="run-$$"
python3 capability.py mint signing.key token.txt read record:alpha broker.lesson "$RUN_ID" 60 '{}'
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$RUN_ID" '{}'
```

### Line by line

- `umask 077` makes newly created key and token files private to the current user.
- The signing material is synthetic. It authenticates lesson tokens but grants access to no real system.
- `RUN_ID` prevents a capability from another run being accepted merely because its other fields match.
- Mint binds empty canonical input `{}`. Verification must provide the same operation, resource, audience, run, and input.
- Expected verification output is JSON containing those claims, a 32-hex-character nonce, and nearby integer timestamps.

Inspect the readable payload without the key:

```bash
python3 -c 'import base64,json,pathlib; p=pathlib.Path("token.txt").read_text().split(".")[0]; print(json.dumps(json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4))),indent=2,sort_keys=True))'
! grep -q 'FAKE-SIGNING' token.txt
```

- Anyone holding the capability can decode its claims; signing provides integrity and issuer authenticity, not confidentiality.
- The grep checkpoint proves the signing key itself is not embedded. A service credential must likewise never be placed in claims.

## Exercise 3 - Break bindings, then expire the token

```bash
set +e
python3 capability.py verify signing.key token.txt read record:beta broker.lesson "$RUN_ID" '{}'
resource_status=$?
python3 capability.py verify signing.key token.txt append record:alpha broker.lesson "$RUN_ID" '{}'
operation_status=$?
set -e
test "$resource_status" -ne 0
test "$operation_status" -ne 0
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$RUN_ID" '{}'
```

### Line by line

- The first two calls are intentional confused-deputy attempts: reuse a valid token while asking for a different resource or operation.
- Both signatures remain valid, but request-to-claim comparison fails. A valid signature alone is not authorization.
- The final exact request repairs the mismatch and succeeds.

Now observe expiry with a separate one-second capability:

```bash
python3 capability.py mint signing.key short.txt read record:alpha broker.lesson "$RUN_ID" 1 '{}'
sleep 2
! python3 capability.py verify signing.key short.txt read record:alpha broker.lesson "$RUN_ID" '{}'
rm -f signing.key token.txt short.txt
```

- `sleep 2` crosses the one-second validity window; verification must return nonzero.
- Removing the lesson-local fake artifacts limits accidental reuse. Expiry does not erase bearer tokens by itself.

## Checkpoint and troubleshooting

```bash
test "$resource_status" -ne 0
test "$operation_status" -ne 0
```

- If every verification reports signature mismatch, use the same unmodified key file for mint and verify.
- If JSON input fails, quote it as one argv element; the tool hashes parsed canonical JSON.
- Checkpoint: identify which properties are visible in the payload and which property depends on possession of the signing key.

### Complete guided source listings

#### `capability.py`

```python
#!/usr/bin/env python3
"""Mint and verify one short-lived, operation-bound synthetic capability."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sys
import time


def encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def input_digest(raw: str) -> str:
    return hashlib.sha256(canonical(json.loads(raw))).hexdigest()


def mint(key: bytes, operation: str, resource: str, audience: str, run_id: str, ttl: int, input_json: str) -> str:
    if not 1 <= ttl <= 300:
        raise ValueError("TTL must be 1..300 seconds")
    issued = int(time.time())
    claims = {
        "version": 1,
        "operation": operation,
        "resource": resource,
        "audience": audience,
        "run_id": run_id,
        "issued_at": issued,
        "expires_at": issued + ttl,
        "nonce": secrets.token_hex(16),
        "input_sha256": input_digest(input_json),
    }
    payload = encode(canonical(claims))
    signature = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
    return payload + "." + signature


def verify(key: bytes, token: str, operation: str, resource: str, audience: str, run_id: str, input_json: str) -> dict:
    payload, supplied = token.strip().split(".")
    expected = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(supplied, expected):
        raise ValueError("signature mismatch")
    padded = payload + "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded))
    now = int(time.time())
    expected_binding = (operation, resource, audience, run_id, input_digest(input_json))
    actual_binding = tuple(claims[name] for name in ("operation", "resource", "audience", "run_id", "input_sha256"))
    if actual_binding != expected_binding:
        raise ValueError("capability binding mismatch")
    if not claims["issued_at"] <= now < claims["expires_at"]:
        raise ValueError("capability is not currently valid")
    return claims


def main() -> int:
    if len(sys.argv) < 2:
        return 2
    if sys.argv[1] == "mint" and len(sys.argv) == 10:
        key = Path(sys.argv[2]).read_bytes()
        token = mint(key, sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], int(sys.argv[8]), sys.argv[9])
        Path(sys.argv[3]).write_text(token + "\n", encoding="utf-8")
        print("capability minted")
        return 0
    if sys.argv[1] == "verify" and len(sys.argv) == 9:
        key = Path(sys.argv[2]).read_bytes()
        token = Path(sys.argv[3]).read_text(encoding="utf-8")
        claims = verify(key, token, sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])
        print(json.dumps(claims, sort_keys=True))
        return 0
    print("usage: capability.py mint KEY TOKEN OP RESOURCE AUDIENCE RUN TTL INPUT_JSON", file=sys.stderr)
    print("   or: capability.py verify KEY TOKEN OP RESOURCE AUDIENCE RUN INPUT_JSON", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"capability denied: {error}", file=sys.stderr)
        raise SystemExit(1)
```

<!-- PAGEBREAK -->

## Lesson 09.03

# 09.03 - Deny replay and confused-deputy substitution

## Goal

Put a fake credential behind a Unix-socket operation broker, consume each capability once, and recheck every binding before contacting a separate synthetic upstream.

## Exercise 1 - Read the complete local system

```bash
sed -n '1,360p' capability_broker.py
sed -n '1,220p' synthetic_upstream.py
sed -n '1,180p' mint_token.py
sed -n '1,160p' broker_client.py
```

### Components, block by block

- `mint_token.py` creates the same canonical signed claims as Lesson 09.02. The client receives the token file, not the signing key or service credential.
- `broker_client.py` sends exactly token, operation, resource, audience, run, and parsed input over a filesystem Unix socket.
- `capability_broker.py` validates policy and mode-`0600` secret files before listening. It strictly decodes base64, verifies HMAC, validates the complete claim set and lifetime, and compares request fields to claims and policy.
- The broker hashes canonical request input, checks its digest, and rejects a previously consumed nonce. It consumes the nonce before calling upstream, caps the in-memory replay set, and fails closed at capacity, so a failed operation cannot make the same bearer capability reusable.
- Only after those checks does `call_upstream` read the broker-held fake credential into a request for a separate Unix socket. An upstream response that reflects the credential is rejected.
- `synthetic_upstream.py` accepts one exact fake credential, `read`, resource, and empty input. It never listens on IP and returns only a synthetic value.
- Both services use bounded lines, timeouts, mode-`0600` sockets, signal-driven exit, and exact-path unlinking.

## Exercise 2 - Launch the brokered operation

Create only fake secret material and a local policy:

```bash
umask 077
printf '%s' 'FAKE-SIGNING-KEY-09.03-ONLY-000000000000' > signing.key
printf '%s' 'FAKE-UPSTREAM-CREDENTIAL-09.03' > credential.txt
RUN_ID="run-$$"
AUDIENCE="records.lesson"
RESOURCE="record:alpha"
UPSTREAM="$PWD/upstream.sock"
BROKER="$PWD/broker.sock"
cat > policy.json <<EOF
{"version":1,"audience":"$AUDIENCE","run_id":"$RUN_ID","max_ttl":120,"upstream_socket":"$UPSTREAM","permissions":{"record:alpha":["read"],"record:beta":["read"]}}
EOF
python3 -m json.tool policy.json
```

### Line by line

- `umask 077` is verified by the broker; group- or world-accessible secret files fail setup.
- The signing key and credential are different synthetic authorities. A token signature never contains the credential.
- Policy names one audience and run, a maximum lifetime, one exact upstream socket, and an operation allowlist.
- `record:beta` exists in policy specifically so the confused-deputy test isolates token binding from broad policy denial.

Start both exact owned services and wait for their socket types:

```bash
python3 synthetic_upstream.py credential.txt "$RESOURCE" synthetic-record-value "$UPSTREAM" & upstream_pid=$!
python3 capability_broker.py policy.json signing.key credential.txt "$BROKER" & broker_pid=$!
trap 'kill "$broker_pid" "$upstream_pid" 2>/dev/null || true; wait "$broker_pid" "$upstream_pid" 2>/dev/null || true; rm -f "$BROKER" "$UPSTREAM"' EXIT
for attempt in 1 2 3 4 5; do test -S "$BROKER" && test -S "$UPSTREAM" && break; sleep 0.1; done
test "$(stat -c '%a' "$BROKER")" = 600
test "$(stat -c '%a' "$UPSTREAM")" = 600
```

The readiness and mode checks observe effective socket state. No name-prefix cleanup or unrelated process signaling is used.

Mint and spend one capability:

```bash
python3 mint_token.py signing.key token.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" 60 '{}'
python3 broker_client.py "$BROKER" token.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" '{}'
```

Expected JSON is `ok: true` with `synthetic-record-value`. Neither response nor client environment contains `FAKE-UPSTREAM-CREDENTIAL-09.03`.

## Exercise 3 - Replay and substitute

Replay the same token, then attempt to make the deputy use it for another policy-allowed resource:

```bash
python3 broker_client.py "$BROKER" token.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" '{}'
python3 mint_token.py signing.key deputy.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" 60 '{}'
python3 broker_client.py "$BROKER" deputy.txt read record:beta "$AUDIENCE" "$RUN_ID" '{}'
```

### Line by line

- The replay returns `ok: false` because the first successful request consumed the nonce.
- `deputy.txt` is valid for `record:alpha`. The request names `record:beta`, which policy generally allows, but the token-to-request comparison denies the substitution before upstream contact.
- This is the confused-deputy repair: possession of broad broker authority does not let the caller reinterpret a narrower capability.

Intentional mistake: temporarily remove the operation/resource/request comparisons in `verify_token`. The second request advances to upstream instead of failing at the broker. Restore all comparisons and require `request does not match capability`.

Stop exact processes and verify socket cleanup:

```bash
kill "$broker_pid" "$upstream_pid"
wait "$broker_pid" "$upstream_pid"
trap - EXIT
test ! -e "$BROKER"
test ! -e "$UPSTREAM"
rm -f signing.key credential.txt policy.json token.txt deputy.txt
```

## Checkpoint and troubleshooting

```bash
test ! -e "$BROKER"
test ! -e "$UPSTREAM"
```

- If setup says secret files must be mode `0600`, inspect with `stat -c '%a'` and recreate synthetic files under `umask 077`; never broaden permissions.
- If a fresh token reports invalid time, confirm the VM clock is sane and the requested TTL does not exceed policy.
- If upstream denies an exact request, compare its resource and empty input with the policy and token; do not expose the credential for debugging.
- Checkpoint: explain why the replay set must be broker state and why signature verification alone cannot prevent replay.

### Complete guided source listings

#### `capability_broker.py`

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
    if not isinstance(raw, dict) or set(raw) != expected or raw["version"] != 1:
        raise Denied("invalid policy shape")
    if not all(isinstance(raw[name], str) and 1 <= len(raw[name]) <= 128 for name in ("audience", "run_id")):
        raise Denied("invalid policy identity")
    if type(raw["max_ttl"]) is not int or not 1 <= raw["max_ttl"] <= 300:
        raise Denied("invalid maximum lifetime")
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
    if not isinstance(claims, dict) or set(claims) != claim_names or claims["version"] != 1:
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
                peer.sendall(canonical(response) + b"\n")
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
        if stat.S_IMODE(key_path.stat().st_mode) & 0o077 or stat.S_IMODE(credential_path.stat().st_mode) & 0o077:
            raise Denied("broker secret files must be mode 0600")
        serve(policy, key, credential, Path(sys.argv[4]))
    except (Denied, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"broker setup denied: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### `synthetic_upstream.py`

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
                request = json.loads(peer.makefile("rb").readline(16384))
                allowed = request == {"credential": credential, "operation": "read", "resource": resource, "input": {}}
                response = {"ok": True, "result": {"value": value}} if allowed else {"ok": False, "error": "upstream denied"}
            except (json.JSONDecodeError, OSError):
                response = {"ok": False, "error": "invalid upstream request"}
            peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
```

#### `mint_token.py`

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
issued = int(time.time())
input_value = json.loads(sys.argv[8])
claims = {
    "version": 1,
    "operation": sys.argv[3],
    "resource": sys.argv[4],
    "audience": sys.argv[5],
    "run_id": sys.argv[6],
    "issued_at": issued,
    "expires_at": issued + int(sys.argv[7]),
    "nonce": secrets.token_hex(16),
    "input_sha256": hashlib.sha256(canonical(input_value)).hexdigest(),
}
payload = encode(canonical(claims))
signature = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
Path(sys.argv[2]).write_text(payload + "." + signature + "\n", encoding="utf-8")
print("capability minted")
```

#### `broker_client.py`

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
    stream.connect(sys.argv[1])
    stream.sendall(json.dumps(request, sort_keys=True).encode() + b"\n")
    stream.shutdown(socket.SHUT_WR)
    print(stream.makefile("r", encoding="utf-8").readline(), end="")
```

<!-- PAGEBREAK -->

## Independent lab

# Module 09 independent lab - Capability-bound credential broker

Implement `capability_broker.py`. The grader invokes:

```text
python3 capability_broker.py POLICY.json SIGNING_KEY CREDENTIAL SOCKET
```

The policy contains version 1, exact audience and run identity, a maximum lifetime, an absolute synthetic-upstream Unix socket, and a resource-to-operation allowlist. Signing-key and fake-credential files are mode `0600`. The broker must validate all setup before creating its own mode-`0600` Unix socket.

Clients send one bounded JSON line containing exactly:

```json
{"token":"PAYLOAD.SIGNATURE","operation":"read","resource":"record:example","audience":"records.example","run_id":"run-example","input":{}}
```

Verify canonical URL-safe base64 and HMAC-SHA256 with constant-time comparison. Require the exact version and claim set: operation, resource, audience, run, issue time, expiry, nonce, and canonical-input SHA-256. Deny future, expired, nonpositive, or policy-overlong lifetimes. Match request fields and input to claims, then match audience/run and permission to policy. Consume a valid 32-hex nonce before upstream contact and deny reuse.

Only after every check may the broker read the fake credential and send it with the authorized operation to the exact upstream Unix socket. Bound the in-memory replay set and fail closed at capacity. Never place the credential or signing key in tokens, client responses, errors, logs, argv values, or environment variables. Reject an upstream response that reflects the credential. Clean termination must remove the exact broker socket.

The external grader uses fresh fake secrets, identities, resources, values, times, nonces, and a separate synthetic upstream. It checks success and credential use, non-disclosure, replay, signature tampering, audience/run binding, time bounds, operation/resource/input substitution, policy denial, strict request shape, private socket mode, insecure secret-file rejection before listen, and cleanup. Protected attempts must be denied before upstream contact.

The starter is a runnable, private, fail-closed Unix server that denies every operation. It intentionally does not implement capabilities or contact upstream. The lab withholds a complete solution; use only interfaces practiced in Lessons 09.01-09.03.

```bash
python3 -m py_compile capability_broker.py
../../lab-grade module-09
../../lab-grade module-09 --mode exam
```

### Test commands, line by line

- `py_compile` checks syntax without opening a socket or reading secret material.
- Practice mode runs fresh behavior checks and names relevant lessons for failed properties.
- Exam mode repeats the same properties while withholding lesson references.

Use only the generated fake credential and synthetic Unix-socket upstream. Never substitute a real key, token, credential, network service, or production resource.

## Security model summary

The workload receives neither the fake service credential nor the signing key. It receives a bearer capability whose readable claims are integrity-protected and narrowly bind an operation. The broker independently rechecks signature, claim shape, time, audience, run, policy, operation, resource, canonical input, and nonce before using its broader credential. The upstream proves credential use, while response filtering and external grading prove non-disclosure. A capability remains authority until expiry or consumption, so storage and replay state still matter.

## Glossary

- **Ambient authority:** authority available to code without an explicit operation-specific grant.
- **Capability:** an unforgeable or integrity-protected value that conveys specific authority to its holder.
- **Audience:** the broker or service for which a capability is intended.
- **Nonce:** a unique identifier consumed to make a bearer capability one-use.
- **Replay:** reuse of a previously accepted authorization value.
- **Confused deputy:** a more-privileged component induced to use its authority for a caller-selected target outside the caller's grant.
- **HMAC:** a keyed message-authentication code that provides integrity and issuer authentication, not confidentiality.
