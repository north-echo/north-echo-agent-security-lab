# Module 08 independent lab - Policy-bound egress broker

## Your assignment and readiness check

Build a reusable broker that mediates a small HTTP capability for a network-isolated caller. Do not give the caller a route, general TCP proxy, live DNS resolver, or shell command interface.

Before beginning, explain the successful direct baseline and isolated failure from 08.01, the pathname-socket path from 08.02, and the per-redirect decision plus policy-restart requirement from 08.03. If any is unclear, repeat that guided exercise first. This lab asks you to assemble those skills independently, not discover an undocumented API.

## Prepare and inspect the starter

From the course root in your disposable Linux VM:

```bash
./lab-start module-08
cd .student/08.lab
pwd
ls -l egress_broker.py
cat egress_broker.py
nano egress_broker.py
```

The working copy is yours to edit. Keep canonical files under `course/` unchanged. In nano, use Ctrl+O, Enter to save and Ctrl+X to exit with the course's default key bindings.

<!-- source: course/module-08-network-egress/lab/egress_broker.py format=code -->
```python
#!/usr/bin/env python3
"""Starter: validate arguments, but do not expose an unmediated fallback."""

import sys

if len(sys.argv) != 3:
    print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
    raise SystemExit(2)
print("broker policy is not implemented", file=sys.stderr)
raise SystemExit(1)
```
<!-- /source -->

### Starter, line by line

- The docstring describes a deliberately incomplete program, not a working broker.
- `sys.argv` contains the executable filename plus the policy and socket arguments.
- The length check reports interface misuse with status 2.
- Even correctly supplied arguments reach a nonzero, fail-closed exit. The starter creates no listener and opens no network path.
- Replace the incomplete behavior with your implementation; preserving a helpful argument check is useful.

## Required interface and behavior

The grader invokes:

```text
python3 egress_broker.py POLICY.json SOCKET
```

Validate the complete policy **before** creating a listener. The policy has exactly a nonempty bounded `run_id` and a `destinations` dictionary. Each lowercase synthetic hostname maps to exactly a literal `address` and a nonempty list of integer `ports`. Accept only IPv4 loopback addresses and ports 1 through 65535; reject Boolean ports. Never perform live DNS or contact a non-loopback address.

Create a filesystem Unix socket at the supplied path with mode 0600. Refuse a pre-existing path, including a dangling symlink. The socket is an IPC channel, not proof of a client's identity.

Each connection carries one bounded newline-terminated JSON object:

```json
{"run_id":"example-run","host":"allowed.test","port":45123,"path":"/ok"}
```

Require exactly those fields. Bind the run value to policy, validate types and path shape, and authorize the hostname, mapped literal address, and port before every upstream connection. A caller must not override the mapped address with an extra field.

Support relative and absolute HTTP redirects, but parse and reauthorize every resulting destination **before** contacting it. Reject user information, non-HTTP schemes, fragments, invalid ports, control characters, ambiguous paths, oversized messages/bodies, excessive redirects, and upstream failures. Use the practiced limits of 8192 request bytes, 65536 response-body bytes, and at most four followed redirects. Use bounded blocking operations; do not describe these as one absolute end-to-end deadline.

Success is one JSON line with Boolean `ok: true`, integer HTTP `status`, string `body`, and integer `redirects`. Denial is one line with `ok: false` and an `error`. A denied request must not prevent a later valid request. Clean SIGTERM/SIGINT termination must exit successfully and remove the exact socket. Do not implement permissive fallback behavior.

## Map the work to practiced skills

- Policy dictionaries, JSON types, and exact field sets: Module 04 and 08.03.
- A pathname Unix socket with effective mode checking: 08.02.
- Literal address selection without live DNS: 08.02 and 08.03.
- Checking the destination again after a redirect: 08.03.
- Bounded reads, operation timeouts, and response framing: all three networking lessons.
- Signal-aware cleanup and registered manual service launches: 08.01-08.03 and Module 07.
- Distinguishing namespace setup failure from an observed connection denial: 08.01.

Write a short design note before coding: where is the last authorization decision before a connection? What data reaches that connection? Which cleanup path runs if an upstream request fails? Your note is part of your learning evidence, not an automatically graded answer.

## Validate independently

```bash
python3 -m py_compile egress_broker.py
../../lab-grade module-08
../../lab-grade module-08 --mode exam
```

Compilation checks syntax without starting a listener. Practice grading creates fresh synthetic names, ports, run identity, and bodies, then reports failed properties with lesson references. Exam grading uses the same behavior checks with less repair guidance. A passing practice run is not a substitute for explaining the boundary.

The external grader runs randomized allowed/protected loopback services. It checks approved access, run binding, name and port denial, an allowed relative redirect, denied name and literal-address redirect destinations **before protected contact**, exact request shape, refusal of non-loopback policy, a real isolated network observation, mode 0600, and clean teardown. Protected-service contact counts are stronger evidence than merely not displaying its body.

The grader is a finite set of observations. It does not prove absence of every parser ambiguity, a complete authentication design, resilience to every slow client, or production suitability. Retain your own boundary explanation alongside the result.

## Troubleshooting, cleanup, and reset

If no socket appears, inspect syntax, policy validation, path length, and the startup error; do not remove validation to make a listener appear. If a redirect test fails, follow the parsed next destination and the policy decision rather than matching the grader's canary text. If namespace creation fails, repair the supported disposable-VM setup before interpreting connectivity results.

The grader owns and terminates its test processes. If you manually launch services while debugging, use the same registered unit pattern as the lessons, substituting `module-08` in the target, unit-name component, and exact description. Use `../../lab-cleanup module-08 --dry-run`, then `../../lab-cleanup module-08`; do not use wildcard process kills.

Return with `cd ../..`. `./lab-reset module-08` removes the lab workspace and fixtures after verified cleanup. Save your own notes first. Use only synthetic loopback services; keep SELinux enabled and never add host routes, firewall changes, real credentials, or public targets.
