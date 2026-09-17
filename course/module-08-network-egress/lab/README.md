# Module 08 independent lab - Policy-bound egress broker

Implement `egress_broker.py`. The grader invokes:

```text
python3 egress_broker.py POLICY.json SOCKET
```

The broker must validate the complete policy before creating a mode-`0600` filesystem Unix socket. Policy contains an exact `run_id` and a map from synthetic lowercase hostnames to a literal `address` plus allowed `ports`. Permit only IPv4 loopback addresses; never perform live DNS or make a non-loopback request.

Each client connection carries one bounded newline-terminated JSON object:

```json
{"run_id":"...","host":"allowed.test","port":45123,"path":"/ok"}
```

Require exactly those fields. Authorize the run, hostname, mapped address, and port before each connection. Support bounded HTTP redirects, but parse and reauthorize every new URL before contacting it. Reject credentials, non-HTTP schemes, malformed ports, ambiguous paths, oversized input or output, excessive redirects, extra authority-bearing fields, and upstream failures. Responses are one JSON line: success includes `ok`, `status`, `body`, and `redirects`; denial includes `ok: false` and an error. Clean termination must remove the exact socket.

The fresh external grader starts randomized allowed and protected loopback services. It checks approved access, run binding, hostname and port denial, an allowed relative redirect, denied name and literal-address redirect escapes before protected contact, strict request shape, non-loopback policy rejection, absence of a direct IP path from a new network namespace, socket mode, and teardown.

The starter fails closed without creating a socket. Build from the interfaces and ordering practiced in the three lessons; the lab deliberately does not include a complete implementation.

```bash
python3 -m py_compile egress_broker.py
../../lab-grade module-08
../../lab-grade module-08 --mode exam
```

### Test commands, line by line

- `py_compile` catches syntax errors without starting a listener or contacting a service.
- Practice mode creates fresh names, ports, run identity, and bodies, then reports failed properties with lesson references.
- Exam mode runs the same behavior checks with reduced repair guidance.

Use only the disposable VM and grader-created synthetic loopback services. Do not add veth devices, routes, firewall rules, DNS requests, public endpoints, or a permissive fallback.
