# Module 09 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic.

Source under test: Module 09 feature branch based on `33f2980`; the final commit hash will be the commit containing this record. Date: 2026-09-17.

## Acceptance checklist

- [x] Three substantive guided lessons with exact commands, complete guided source listings, local explanations, expected observations, intentional failures, repairs, checkpoints, and troubleshooting.
- [x] Independent lab specifies the interface and properties without shipping a completed lab implementation.
- [x] `09.01`, `09.02`, `09.03`, and `09.lab` start through the public lifecycle CLI with fresh synthetic fixtures.
- [x] External grader evaluates a read-only copy with fresh fake signing key, credential, identity, resources, values, times, and nonces.
- [x] Runnable starter fails closed; completed implementation passes all 12 properties in practice and exam modes.
- [x] Ambient fake credential inheritance is reproduced and removed by a minimal environment.
- [x] Capabilities bind operation, resource, canonical input, audience, run, issue/expiry time, and nonce.
- [x] Tampering, future/expired/overlong time, policy excess, malformed shape, and deputy substitutions are denied before upstream contact.
- [x] Successful operation proves fake credential use at the synthetic upstream without client disclosure.
- [x] Replay cache consumes the nonce before upstream use, is bounded, and rejects reuse.
- [x] Lesson, module dry-run, module reset, and replay lifecycle paths pass with fresh fixture rotation.
- [x] No persistent broker object is created. Exact-PID services, workspace sockets, and fake secret files leave no owned resource behind.
- [x] Full field-manual chapter is synchronized with shipped source and lab behavior.
- [x] Full automated suite passes 33/33 on Linux; course attestation and 28-check Linux preflight pass.

## Evidence

- `environment.txt`: distribution, kernel, architecture, transport, and fake-secret constraints.
- `tests.txt`: full automated result and focused Module 09 checks.
- `preflight.txt`: supported-baseline prerequisites.
- `lessons.txt`: all three guided paths and observations.
- `grading.txt`: starter failure plus completed practice/exam results.
- `lifecycle.txt`: starts, dry-run, reset, and fixture rotation.
- `final.txt`: empty workspaces, sockets, helpers, and temporary state.

## Safety and residual risk

Only generated fake secrets and local Unix sockets in the disposable VM were used. No real credential, network request, identity provider, cloud service, LAN host, public endpoint, employer system, or production resource was involved. No feature was skipped.

The broker is an educational single-process capability verifier, not a production authorization service. HMAC uses one symmetric issuer/verifier key, replay state is memory-only and bounded to one broker lifetime, there is no durable audit log or key rotation, and capabilities are bearer values until expiry or consumption. These deliberate limits do not weaken the module's ambient-authority, binding, replay, and confused-deputy objectives.
