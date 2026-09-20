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

<!-- source: course/module-09-credential-brokering/lab/capability_broker.py format=code -->
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
<!-- /source -->

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
