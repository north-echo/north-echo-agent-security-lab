# Module 08 acceptance record

Status: **PASS** on Ubuntu 24.04.4 LTS arm64 with Linux 6.8.0-134-generic.

Source under test: Module 08 feature branch based on `39a9947`; the final commit hash will be the commit containing this record. Date: 2026-09-17.

## Acceptance checklist

- [x] Three substantive guided lessons with exact commands, complete guided source listings, local explanations, expected observations, intentional failures, repairs, checkpoints, and troubleshooting.
- [x] Independent lab specifies the interface and properties without shipping a completed lab implementation.
- [x] `08.01`, `08.02`, `08.03`, and `08.lab` start through the public lifecycle CLI with fresh synthetic fixtures.
- [x] External grader evaluates a read-only copy with fresh randomized hostname, ports, run identity, and response body.
- [x] Starter fails closed; completed implementation passes all 11 properties in practice and exam modes.
- [x] Empty network namespace denies direct IP access.
- [x] Filesystem Unix socket mediates one structured capability without adding an IP path.
- [x] Policy binds run, synthetic hostname, explicit loopback address, port, and path shape.
- [x] Same-origin redirect succeeds; protected-name and literal-address redirect escapes are denied before contact.
- [x] Input, response, timeout, and redirect bounds are enforced; non-loopback policy is rejected.
- [x] Lesson, module dry-run, module reset, and replay lifecycle paths pass with fresh fixture rotation.
- [x] No persistent network object is created. Exact-PID helpers, workspace sockets, readiness files, and process-lifetime namespaces leave no owned resource behind.
- [x] Full field-manual chapter is synchronized with shipped source and lab behavior.
- [x] Full automated suite passes 31/31 on Linux; course attestation and 28-check Linux preflight pass.

## Evidence

- `environment.txt`: distribution, kernel, architecture, and relevant tool versions.
- `tests.txt`: full automated result and focused Module 08 checks.
- `preflight.txt`: required kernel/tool prerequisites.
- `lessons.txt`: all three guided paths and their observations.
- `grading.txt`: starter failure plus completed practice/exam results.
- `lifecycle.txt`: starts, dry-run, reset, and fixture rotation.
- `final.txt`: empty workspaces, sockets, helpers, and temporary state.

## Safety and residual risk

All endpoints were synthetic and bound to `127.0.0.1` inside the disposable VM. No veth device, route, firewall rule, live DNS query, LAN address, cloud metadata endpoint, public service, credential, or production system was used. No feature was skipped.

The broker is an educational HTTP mediator, not a production proxy: it supports bounded plaintext HTTP only, serial request handling, one explicit IPv4 loopback mapping per name, and no TLS. The platform checks honest implementations and is not a hostile multi-user anti-cheat boundary. These limits are deliberate and do not weaken the module's destination, redirect, and run-binding objectives.
