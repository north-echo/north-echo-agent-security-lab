<!-- source: course/module-09-credential-brokering/README.md format=markdown -->
# Module 09 - Broker credentials with operation capabilities

Remove fake credentials from workload environments, then place their use behind a local operation broker. HMAC-authenticated, short-lived capabilities bind the exact operation, resource, arguments, audience, run, and nonce without containing the underlying credential. Nonce consumption is remembered for one broker-process lifetime.

Play in order: `09.01`, `09.02`, `09.03`, then `module-09`.

Outcomes:

- observe that an environment credential is ambient authority inherited across `exec`;
- remove that authority with an explicit minimal environment;
- distinguish a signed capability from an encrypted secret;
- bind operation, resource, canonical input, audience, run identity, issue time, expiry, and nonce;
- deny tampering, expiry, excessive lifetime, replay, and confused-deputy substitutions before upstream contact;
- prove a broker used a fake credential upstream without returning it to the client.

Every credential, signing key, capability, resource, and upstream service is synthetic and lesson-local. Communication uses filesystem Unix sockets only; no DNS, LAN, public, cloud, employer, or production service is involved. Prerequisites are Modules 01, 04, and 08.

## Learning route and limits

First observe what an inherited environment makes available. Next authenticate
readable claims and compare them with a requested operation. Finally add policy
checks, an upstream service, and remembered consumption. Distinguish each step:
encoding is not encryption, HMAC is not an asymmetric signature, a valid token
is not permission for a different request, and a nonce alone does not stop replay.

The issuer, broker, client, and upstream are teaching roles running under one
VM account. A private file mode does not separate same-account processes. The
lessons demonstrate the intended request interface, not a complete secret-storage
boundary. Earlier filesystem/process controls are still required for confinement.

The replay cache is in memory and is lost on restart; consumption before contact
also means an upstream failure can spend a token. There is no exactly-once or
durable replay guarantee. All tests and observations use fake material only.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lesson-01/README.md format=markdown -->
# 09.01 - Remove ambient credential authority

## Outcomes and prerequisites

Complete Modules 01, 04, and 08. You will observe a visibly fake credential crossing a process launch, remove it with an explicit environment, and explain what this does not isolate. This revisits B1 with an operation-broker design in mind.

## Concepts before commands

A **credential** is a value a service accepts as evidence of authority. Putting one in a process environment makes it available to that process's code. A child normally inherits the parent's environment unless the launcher supplies a replacement.

An **ambient** credential is available without making a new, operation-specific authorization decision. Its short lifetime may reduce exposure, but does not stop a process reading or copying it while present.

This exercise uses only a string beginning with `FAKE-`. Never substitute an API key, cloud token, password, employer credential, or personal secret. The deliberate disclosure prints only that synthetic value. It demonstrates authority inheritance, not an attack against another process.

## Prepare and read both files

From the course root in the disposable VM:

```bash
./lab-start 09.01
cd .student/09.01
pwd
ls -l credential_probe.py clean_launch.py
cat credential_probe.py
cat clean_launch.py
```

The scripts are already in your prepared workspace. You can inspect them with `nano credential_probe.py` or `nano clean_launch.py`. Reading a source is not executing it; the next exercises run it.

### The synthetic observer

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

### Source, line by line

- `json` formats the observation; `os` exposes this process's environment; `sys` exposes its arguments.
- `name` selects one explicitly fake variable. `os.environ.get` returns its string value or `None` if absent.
- `value is not None` distinguishes an absent variable from a present empty string. A present empty string still has length zero.
- The dictionary reports presence and length without displaying the value by default.
- Only the exact extra argument `leak`, with a present value, adds `leaked_value` to the result. This is intentionally unsafe display behavior for synthetic evidence.
- `json.dumps(..., sort_keys=True)` serializes the observation. Sorting gives stable output; it is not redaction.

### The minimal-environment launcher

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

### Source, line by line

- `subprocess` starts the child. The `os` import is retained for the later deliberate comparison with inherited environment.
- The argument guard refuses a missing command before launch.
- `clean` is a new dictionary containing only the selected PATH and locale. It is not a copy with one known secret removed.
- `sys.argv[1:]` preserves separate command arguments. `shell=False` prevents this launcher from treating them as a shell program.
- `env=clean` replaces the child's inherited environment; `check=False` returns a result object instead of raising on an ordinary nonzero child exit.
- `SystemExit(run.returncode)` forwards ordinary child exit codes. This small example is not a complete signal-status or timeout supervisor.

The launcher does **not** remove filesystem access, existing descriptors, network access, or every possible credential source. Environment reduction is one handoff control, not a complete sandbox.

## Exercise 1 - Predict and observe inherited authority

```bash
export NORTH_ECHO_FAKE_CREDENTIAL="FAKE-LESSON-$$-DO-NOT-USE"
python3 credential_probe.py > inherited.json
python3 credential_probe.py leak > disclosed.json
python3 -m json.tool inherited.json
python3 -m json.tool disclosed.json
```

`export` places the value in later child environments. The shell PID contributes a synthetic run label; it has no security significance. Redirection saves each observation separately.

Expect `present: true` and a positive length in both files. Only `disclosed.json` should include the fake value. The child did not need another authorization API to read it: inheritance already conveyed that access. This does not mean all environment values are automatically logged; it means the receiving code can choose to disclose them.

## Exercise 2 - Repair the launch boundary

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" > cleaned.json
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak > cleaned-leak.json
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
python3 -m json.tool cleaned.json
python3 -m json.tool cleaned-leak.json
```

The absolute executable path and script path are separate arguments. Both children should report absence and length zero; neither should contain `leaked_value`. The parent-side `test` proves you did not merely erase the parent value before observing the child.

## Exercise 3 - Make the incomplete repair visible

Open `nano clean_launch.py`. Change only `env=clean` to `env=os.environ.copy()`, save, and predict the result:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" > regressed.json
python3 -m json.tool regressed.json
```

The inherited variable is present again. Explicit argv and `shell=False` did not repair this separate environment mistake. Restore **only** `env=clean`, save, and rerun:

```bash
python3 clean_launch.py /usr/bin/python3 "$PWD/credential_probe.py" leak > repaired.json
```

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

def result(name):
    return json.loads(Path(name).read_text())

assert result("inherited.json")["present"] is True
assert result("disclosed.json")["leaked_value"].startswith("FAKE-LESSON-")
assert result("regressed.json")["present"] is True
for name in ("cleaned.json", "cleaned-leak.json", "repaired.json"):
    observed = result(name)
    assert observed["present"] is False and observed["length"] == 0
    assert "leaked_value" not in observed
print("CREDENTIAL INHERITANCE AND REPAIR: PASS")
PY
test -n "$NORTH_ECHO_FAKE_CREDENTIAL"
unset NORTH_ECHO_FAKE_CREDENTIAL
```

The assertions compare actual JSON fields rather than a suggestive filename. `unset` removes the fake variable from this shell after the experiment. It does not retroactively erase copies in already-running processes or saved JSON.

If the cleaned child sees the value, inspect the actual `env=` argument and confirm you saved the working copy. If the initial observation is absent, repeat the export in the same shell. No inspection of unrelated processes is needed.

A legitimate task may now lack a credential it needs. The next lessons restore a narrow approved **operation**, not the credential itself. Return with `cd ../..`; `./lab-reset 09.01` removes these synthetic output files and restores the working copy.

## Source truth

Python's [subprocess documentation](https://docs.python.org/3.14/library/subprocess.html) defines explicit environment mappings and argument lists. Its [os environment API](https://docs.python.org/3.14/library/os.html#os.environ) describes the process-local mapping. These sources do not claim that an environment-only launcher provides filesystem or network isolation.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lesson-02/README.md format=markdown -->
# 09.02 - Bind an HMAC-authenticated operation capability

## Outcomes and prerequisites

Complete 09.01. You will mint a synthetic operation token, inspect its readable claims, distinguish message authentication from encryption, and observe request-binding and time checks. No listener or external service is involved.

## Concepts before commands

A **bearer capability** conveys authority to whoever presents it. A narrow capability names an operation and resource instead of exposing a general service credential. Possession still matters: a token is not harmless merely because it expires soon.

This example uses HMAC-SHA256, a **shared-key message-authentication code**. The code calls the result a signature for brevity, but it is not an asymmetric public-key signature. Anyone who has the shared key can both verify and mint these tokens. Never give that key to a workload and then expect the token to limit what it can request.

Base64 is a reversible text encoding. A hash is a digest of input bytes. HMAC combines a secret key with a message to check integrity/authenticity relative to that shared key. None of these operations encrypts the claims in this example.

A **binding** ties a claim to its intended context: operation, resource, audience (the intended broker), run, and input. A correct HMAC alone does not authorize a different request. A **nonce** is a fresh random identifier; simply putting it in a token does not make the token one-use. A broker must remember consumption, which 09.03 introduces.

The fixed key below is intentionally public teaching material. It must never protect a real system.

## Prepare and read the program

From the course root:

```bash
./lab-start 09.02
cd .student/09.02
pwd
ls -l capability.py
cat capability.py
```

Open `nano capability.py` to navigate its functions. No source edit is required. Read the whole program before minting short-lived artifacts so reading time does not consume the validity window.

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

### Source, line by line (grouped by function)

- `encode` base64-encodes bytes with the URL-safe alphabet, removes padding, and produces ASCII text. It does not hide the bytes.
- `canonical` sorts object keys, removes optional JSON whitespace, rejects NaN/infinity, and encodes the result as bytes. This is the course's Python serialization convention, not a claim to implement a universal cross-language canonical-JSON standard.
- `input_digest` first parses JSON and then hashes that deterministic representation. Different whitespace or object-key order therefore does not change the digest for the same parsed values.
- `mint` accepts a lifetime from 1 through 300 seconds. `int(time.time())` records wall-clock seconds, not monotonic elapsed time.
- The claims dictionary includes a format version, the operation context, issue/expiry timestamps, a 16-byte random nonce represented by 32 hexadecimal characters, and the input digest.
- The payload is the encoded claims. `hmac.new` authenticates those exact payload characters; the token joins payload and authenticator with one period.
- `verify` splits those two segments, recomputes HMAC, and uses `compare_digest` rather than an ordinary early-exit string comparison.
- It restores base64 padding only for decoding, parses the claims, and constructs matching tuples of expected/request context and actual/token context.
- A different tuple raises a binding error even when HMAC is correct.
- `issued_at <= now < expires_at` defines a half-open validity interval: the token is already invalid at its expiry second.
- `main` distinguishes mint and verify argument counts. Key and token filenames travel in argv; the bearer token itself is read from a file.
- Expected file, parsing, and binding failures print a diagnostic and return nonzero. There is no fallback to an unsigned token.

This compact verifier teaches the mechanism with tokens minted by this tool. It is not yet the stricter schema/encoding/policy validator in 09.03. It also does not retain a replay set. Do not treat a second successful verification as one-use enforcement.

## Exercise 1 - Mint and verify

Create the fake key with a restrictive creation mask in a subshell, leaving your interactive shell's mask unchanged:

```bash
(umask 077; printf '%s' 'FAKE-SIGNING-KEY-09.02-ONLY-000000000000' > signing.key)
test "$(stat -c '%a' signing.key)" = 600
NE_RUN="run-$$"
(umask 077; python3 capability.py mint signing.key token.txt read record:alpha broker.lesson "$NE_RUN" 300 '{}')
test "$(stat -c '%a' token.txt)" = 600
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$NE_RUN" '{}' > verified.json
python3 -m json.tool verified.json
```

`umask` affects newly created files, not existing file modes; the `stat` checks verify the result. If a prior file has the wrong mode, reset this prepared lesson before repeating rather than assuming a mask changed it.

The token binds `read`, `record:alpha`, audience `broker.lesson`, this run, and empty-object input. Timestamps and nonce vary. The fixed fields should match your command. If more than five minutes passes, mint a fresh token and repeat the checks.

## Exercise 2 - Inspect without the key

```bash
python3 - <<'PY'
import base64
import json
from pathlib import Path

payload = Path("token.txt").read_text().strip().split(".")[0]
claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
print(json.dumps(claims, indent=2, sort_keys=True))
assert set(claims) == {
    "version", "operation", "resource", "audience", "run_id",
    "issued_at", "expires_at", "nonce", "input_sha256"
}
assert claims["operation"] == "read" and claims["resource"] == "record:alpha"
print("READABLE CLAIMS: PASS")
PY
```

The program uses only the token file, not the key. The arithmetic adds enough padding to complete a multiple of four encoded characters. The exact key-set assertion checks the visible schema. No service credential belongs in these claims; readable data is not confidential data.

This inspection does **not** authenticate the token. Only verification with the key can check HMAC. Likewise, searching the encoded token for a plaintext secret would not prove that the secret was absent in every encoded form.

## Exercise 3 - Deliberate request mismatch, then repair

```bash
NE_RESOURCE_STATUS=0
python3 capability.py verify signing.key token.txt read record:beta broker.lesson "$NE_RUN" '{}' \
  > wrong-resource.json 2> wrong-resource.err || NE_RESOURCE_STATUS=$?
NE_OPERATION_STATUS=0
python3 capability.py verify signing.key token.txt append record:alpha broker.lesson "$NE_RUN" '{}' \
  > wrong-operation.json 2> wrong-operation.err || NE_OPERATION_STATUS=$?
cat wrong-resource.err wrong-operation.err
test "$NE_RESOURCE_STATUS" -ne 0
test "$NE_OPERATION_STATUS" -ne 0
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$NE_RUN" '{}' > repaired.json
```

The token is unchanged. Its HMAC remains valid, but neither changed request matches its narrower grant. Expect `capability binding mismatch`. Returning to the original operation/resource repairs the mismatch without broadening the grant.

This is the central **confused-deputy** concern: a component with broader authority must not let a caller reinterpret a narrower authorization as permission to act on a different resource.

## Exercise 4 - Observe expiry and the replay limitation

```bash
(umask 077; python3 capability.py mint signing.key short.txt read record:alpha broker.lesson "$NE_RUN" 1 '{}')
sleep 2
NE_EXPIRED_STATUS=0
python3 capability.py verify signing.key short.txt read record:alpha broker.lesson "$NE_RUN" '{}' \
  > expired.json 2> expired.err || NE_EXPIRED_STATUS=$?
cat expired.err
test "$NE_EXPIRED_STATUS" -ne 0
python3 capability.py verify signing.key token.txt read record:alpha broker.lesson "$NE_RUN" '{}' > repeated.json
```

The two-second pause crosses the one-second validity window. Expect `capability is not currently valid`, not just any failure. The longer-lived token can still verify again: signature checking and expiry do not remember whether it was used.

A clock error can invalidate this observation. Inspect `date -u` in the disposable VM if timestamps are implausible; do not remove time validation. Expiry invalidates authority under this verifier, but does not delete token files.

## Checkpoint, troubleshooting, and replay

```bash
python3 - <<'PY'
import json
from pathlib import Path

original = json.loads(Path("verified.json").read_text())
assert json.loads(Path("repaired.json").read_text()) == original
assert json.loads(Path("repeated.json").read_text()) == original
assert original["expires_at"] - original["issued_at"] == 300
assert len(original["nonce"]) == 32
assert "binding mismatch" in Path("wrong-resource.err").read_text()
assert "binding mismatch" in Path("wrong-operation.err").read_text()
assert "not currently valid" in Path("expired.err").read_text()
print("BINDING, EXPIRY, AND REPLAY LIMIT: PASS")
PY
```

Explain why anyone can read claims, why a key holder can mint tokens, and why a nonce needs consumption state. If every verification fails HMAC, check that the key and token belong to the same exercise. If JSON parsing fails, preserve `'{}'` as one argument.

These are synthetic artifacts, but treat the files as authority-bearing during the exercise. Return with `cd ../..`; `./lab-reset 09.02` removes only this prepared workspace and its fake artifacts. No background service needs stopping.

## Source truth

Python's [HMAC API](https://docs.python.org/3.14/library/hmac.html) documents keyed authentication and digest comparison; [base64](https://docs.python.org/3.14/library/base64.html) documents reversible encodings; [secrets](https://docs.python.org/3.14/library/secrets.html) supplies the random nonce. Authorization bindings and replay consumption are application policy, not features supplied automatically by those primitives.
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lesson-03/README.md format=markdown -->
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

### Source, line by line

- The arguments identify a fake credential file, one resource, one harmless return value, and a socket pathname.
- The credential is read at startup. Its value is not passed in argv; only its filename is.
- Existing socket paths are refused. The listener uses `AF_UNIX`, mode 0600, and an accept timeout.
- Each peer has its own timeout and bounded newline read. Invalid data becomes a denial rather than an unrestricted operation.
- Dictionary equality requires the fake credential, operation `read`, configured resource, and empty-object input.
- Success returns a `result` object containing the synthetic value, not the credential. The program is intentionally not a general database.
- Normal stop closes the listener and removes its exact pathname. SIGKILL cannot execute that cleanup.

### The issuer

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

### Source, line by line

- The encoding and canonicalization functions repeat 09.02's token format.
- The argument guard distinguishes key/token filenames from operation context and input JSON.
- Lifetime is bounded before a token is written. Broker policy can impose a smaller maximum than the issuer's 300-second ceiling.
- Timestamps use current wall-clock seconds; nonce generation supplies a fresh 16-byte value as hexadecimal text.
- The input digest covers parsed, deterministically serialized JSON.
- HMAC authenticates the payload text. The file receives `payload.authenticator` plus a newline; stdout reports only that minting completed.

The issuer is trusted with the shared key. This is not an interface to expose to an untrusted workload with unrestricted signing requests.

### The client

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
<!-- /source -->

---

<!-- source: course/module-09-credential-brokering/lab/README.md format=markdown -->
# Module 09 independent lab - Capability-bound credential broker

## Assignment and readiness check

Implement the operation-broker contract practiced in 09.01-09.03. The client submits a narrow capability; the broker holds the broader fake credential. Reject unauthorized requests before upstream contact while preserving the approved operation.

Before coding, explain the difference between HMAC and encryption, token-to-request binding and request-to-policy authorization, expiry and nonce consumption, and API separation versus same-account filesystem isolation. Repeat the relevant guided lesson if one is unclear.

## Prepare and inspect the starter

From the course root:

```bash
./lab-start module-09
cd .student/09.lab
pwd
ls -l capability_broker.py
cat capability_broker.py
nano capability_broker.py
```

Edit this working copy, not canonical course content. With the default nano bindings, Ctrl+O then Enter saves and Ctrl+X exits.

```python
#!/usr/bin/env python3
"""Fail-closed starter for the Module 09 broker interface."""

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
    raise SystemExit(f"usage: {sys.argv[0]} POLICY SIGNING_KEY CREDENTIAL SOCKET")
socket_path = Path(sys.argv[4])
if socket_path.exists() or socket_path.is_symlink():
    raise SystemExit("socket path already exists")
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(str(socket_path))
os.chmod(socket_path, 0o600)
listener.listen(4)
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
                peer.recv(16384)
                peer.sendall(json.dumps({"ok": False, "error": "capability policy is not implemented"}).encode() + b"\n")
            except OSError:
                pass
finally:
    listener.close()
    socket_path.unlink(missing_ok=True)
```

### Starter, line by line

- The imports support a minimal Unix-socket server, not a completed authorization system.
- The stop flag and signal handler permit cooperative loop exit.
- The argument guard expects policy, signing-key, credential, and socket filenames. Only the socket argument is used by this incomplete starter.
- Existing socket paths are refused; the listener uses mode 0600 and a short accept timeout.
- Each accepted connection has an operation timeout. The starter reads bounded bytes and always returns a denial.
- The outer `finally` closes and unlinks the exact listener on normal termination.

The starter is runnable and does not contact upstream, but it deliberately does **not** validate policy/secret setup before listening. Keeping its deny-all response would fail the approved-operation requirement. You must implement validation before listener creation, not merely add a success branch after startup.

## Interface and required behavior

The grader invokes:

```text
python3 capability_broker.py POLICY.json SIGNING_KEY CREDENTIAL SOCKET
```

Policy contains version 1, exact audience and run, maximum lifetime, an absolute synthetic-upstream Unix pathname, and a resource-to-operation allowlist. Signing key and fake credential must be regular non-symlink files with mode 0600 and the bounded lengths practiced in 09.03. Validate trusted setup before creating a mode-0600 broker socket. Refuse a pre-existing socket path.

Each connection carries one bounded JSON line with exactly:

```json
{"token":"PAYLOAD.AUTHENTICATOR","operation":"read","resource":"record:example","audience":"records.example","run_id":"run-example","input":{}}
```

Require canonical URL-safe unpadded base64 and HMAC-SHA256 with digest comparison appropriate for authenticators. Require the complete claim set: version, operation, resource, audience, run, issue time, expiry, nonce, and input SHA-256. The issuer/verifier share a key; this is not a public-key signature scheme.

Reject future, expired, nonpositive, or policy-overlong validity intervals. Timestamps and limits must be integers rather than Booleans. Match request context to claims, then audience/run and operation permission to policy. Bind input using the practiced sorted compact JSON convention with non-finite values rejected.

After all checks, require an unused 32-hex-character nonce. Consume it **before** the upstream operation. Bound remembered nonces to 4096 and fail closed at capacity; do not silently evict a still-live consumed token merely to admit another. This lab's replay state is process-local. Durable cross-restart or multi-broker consumption is not implemented or claimed.

The broker may read the fake credential at trusted startup, but must not send it upstream until authorization succeeds. Send it only with the authorized operation to the configured upstream Unix socket. Bound client input to 16384 bytes and upstream responses to 65536 bytes, require line framing, and use blocking-operation timeouts.

Return one structured response: `ok: true` with `result` for an approved exchange, or `ok: false` with `error` for denial. Reject literal reflection of the fake credential in the upstream response. Never intentionally place the key/credential in capabilities, client responses, logs, argv **values**, or environment variables. Passing their filenames is part of this interface.

Clean SIGTERM/SIGINT termination must remove the exact socket. A denied request or disconnected client must not turn the listener into a permissive fallback.

## Build from practiced skills

- Environment authority and its limits: 09.01 and B1.
- Deterministic input hashing, HMAC, encoding, and time intervals: 09.02.
- Strict token/schema checks, audience/run/policy binding, and nonce consumption: 09.03.
- Unix-socket framing, bounds, actual mode checks, and signal cleanup: Modules 08-09.
- Registered manual service lifecycle and effective resource limits: Module 07.

Before implementation, write down the order of your checks and identify the first line permitted to contact upstream. Also record what restart does to replay state. This explanation is learning evidence, not an automatic test answer.

## Validate your implementation

```bash
python3 -m py_compile capability_broker.py
../../lab-grade module-09
../../lab-grade module-09 --mode exam
```

Compilation checks syntax without starting the server. Practice grading creates fresh synthetic keys, credentials, identities, resources, values, and tokens. It reports failed properties with lesson references. Exam mode reduces repair hints, not the required behavior.

The grader checks approved credential use, absence of the known fake secret in observed responses, replay, tampering, audience/run, lifetime bounds, operation/resource/input substitution, policy denial, exact request shape, private socket mode, insecure-file rejection before listen, and cleanup. It independently observes upstream contacts during rejected attempts.

These finite observations are not a proof of all-channel non-disclosure, race-free same-account secret loading, persistent replay protection, production authentication, or exactly-once execution. State those limits in your notes.

## Troubleshooting and reset

If every request fails, first distinguish setup refusal from token denial and upstream failure. A correct deny-all server is not a functioning authorized service. If only a substituted request succeeds, inspect the binding order; do not special-case fixture names. If a fresh token is expired, check VM time and the chosen lifetime.

The grader owns its processes. For manual debugging, adapt the registered unit helper from 09.03 with target `module-09`, matching exact description and unit-name component. Preview `../../lab-cleanup module-09 --dry-run`, then run `../../lab-cleanup module-09`. Never use wildcard teardown or real credentials.

Return with `cd ../..`; `./lab-reset module-09` discards the working copy and fake fixtures after verified cleanup. Save your own design notes first.
<!-- /source -->

## Security model summary

The client interface receives an authenticated, readable capability rather than the broker's fake service credential. The broker checks claims, policy, context, time, input, and process-local nonce consumption before upstream use. These examples do not isolate same-account access to setup files, persist replay state across restart, guarantee exactly-once execution, or prove all-channel non-disclosure. The external grader adds independent upstream-contact observations for its finite synthetic cases.

## Glossary

- **Ambient authority:** authority available to code without an explicit operation-specific grant.
- **Capability:** an unforgeable or integrity-protected value that conveys specific authority to its holder.
- **Audience:** the broker or service for which a capability is intended.
- **Nonce:** a random identifier whose remembered consumption enables replay checks for a defined lifetime.
- **Replay:** reuse of a previously accepted authorization value.
- **Confused deputy:** a more-privileged component induced to use its authority for a caller-selected target outside the caller's grant.
- **HMAC:** a shared-key message-authentication code; every holder of the key can mint or verify, and claims are not encrypted.
