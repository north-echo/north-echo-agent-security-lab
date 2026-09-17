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
