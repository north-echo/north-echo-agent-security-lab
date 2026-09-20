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

<!-- source: course/module-09-credential-brokering/lesson-02/capability.py format=code -->
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
<!-- /source -->

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
