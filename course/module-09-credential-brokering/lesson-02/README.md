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
