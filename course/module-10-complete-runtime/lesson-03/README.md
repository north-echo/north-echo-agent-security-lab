# 10.03 - Launch, attest, and collect the complete runtime

## Goal

Compose the outer cgroup/namespace/privilege launcher with the native guard, make one capability-mediated synthetic operation, emit effective-state telemetry, and prove exact teardown.

## Exercise 1 - Read the complete composition

```bash
sed -n '1,340p' complete_runtime.py
sed -n '1,360p' runtime_probe.c
sed -n '1,220p' demo_broker.py
```

### Line by line

- The first file is the outer orchestrator and result writer.
- The second is the confined workload that obtains kernel-visible evidence from inside every layer.
- The third is a one-shot synthetic host-side broker; it owns the fake credential and exact socket lifecycle.

### `complete_runtime.py`, block by block

- `validated` accepts only a regular trusted guard, an absolute directory, an argv array whose executable resolves beneath that directory, and bounded CPU, memory, and task values. It rejects before creating a result or unit.
- The exact transient unit name contains the ordinary UID and random material. `systemd-run --wait --collect` creates the cgroup before descendants, applies CPU/memory/swap/PID limits, uses control-group kill semantics, and synchronously collects the unit.
- `unshare` creates user and network namespaces. `setpriv` then removes bounding, inheritable, and ambient capabilities and sets `no_new_privs` after user mapping has created namespace-scoped capabilities.
- The native guard receives the allowed root, installs Landlock and seccomp, and executes the structured workload argv. No shell interprets paths or arguments.
- The systemd client receives only its IPC variables plus a fixed locale/path; the transient service explicitly unsets the fake credential, and `/usr/bin/env -i` gives the guard only fixed locale/path values. Timeout handling stops only the exact generated unit.
- The result preserves status, stdout, stderr, unit identity, and the parsed final JSON attestation.

### Probe and broker, block by block

- `runtime_probe.c` performs real allowed/protected reads; compares its network-namespace inode with the host value; reads its own capability, `NoNewPrivs`, and `Seccomp` fields; and reads effective cgroup controller files.
- Its `AF_INET` call must fail, while its `AF_UNIX` call sends one prebuilt capability request to the broker. The response must be successful and must not contain the public fake-credential prefix marker; the full credential is never in workload argv.
- `demo_broker.py` holds the expected synthetic capability and fake credential outside the workload. On one exact request it uses the credential to derive an event proof but returns only a synthetic value. Its `finally` block unlinks the exact socket.

## Exercise 2 - Build a randomized local system

```bash
DEMO=$(mktemp -d /tmp/north-echo-10.03.XXXXXX)
mkdir "$DEMO/allowed"
gcc -O2 -Wall -Wextra -static \
  ../../course/module-10-complete-runtime/lesson-02/runtime_guard.c \
  -o "$DEMO/runtime_guard" -lseccomp
gcc -O2 -Wall -Wextra -static runtime_probe.c -o "$DEMO/allowed/runtime_probe"
python3 - "$DEMO" <<'PY'
import json, secrets, sys
from pathlib import Path
root = Path(sys.argv[1])
token = "CAP-" + secrets.token_hex(16)
credential = "FAKE-CREDENTIAL-" + secrets.token_hex(16)
(root / "allowed" / "allowed.txt").write_text("allowed\n")
(root / "protected.txt").write_text("synthetic-protected\n")
(root / "token.txt").write_text(token + "\n")
(root / "credential.txt").write_text(credential + "\n")
(root / "allowed" / "request.json").write_text(json.dumps({
    "operation": "read", "resource": "synthetic:record", "token": token,
}, sort_keys=True, separators=(",", ":")) + "\n")
PY
chmod 600 "$DEMO/token.txt" "$DEMO/credential.txt"
HOST_NET=$(stat -Lc '%i' /proc/self/ns/net)
HOST_USER=$(stat -Lc '%i' /proc/self/ns/user)
```

Every identifier is synthetic and fresh. The broker's secret files are outside the allowed root; the request file contains only a narrow bearer capability.

## Exercise 3 - Trigger the incomplete composition

Start the one-shot broker and invoke only the inner guard:

```bash
python3 demo_broker.py "$DEMO/allowed/broker.sock" "$DEMO/token.txt" \
  "$DEMO/credential.txt" "$DEMO/direct-event.json" & direct_broker=$!
for attempt in 1 2 3 4 5; do test -S "$DEMO/allowed/broker.sock" && break; sleep 0.1; done
NORTH_ECHO_FAKE_CREDENTIAL="$(sed -n '1p' "$DEMO/credential.txt")" \
  "$DEMO/runtime_guard" "$DEMO/allowed" "$DEMO/allowed/runtime_probe" \
  "$DEMO/allowed/allowed.txt" "$DEMO/protected.txt" "$DEMO/allowed/broker.sock" \
  "$DEMO/allowed/request.json" "$HOST_NET" "$HOST_USER" 'FAKE-CREDENTIAL-' || true
wait "$direct_broker"
```

The deliberate incomplete launch already has Landlock, seccomp, and broker access, but its attestation reports `private_net:false`, host cgroup values, and `credential_absent:false`. Composition is conjunctive: several successful layers do not compensate for missing outer controls.

## Exercise 4 - Repair, attest, and collect

Start a fresh one-shot broker, generate the structured spec without shell-built JSON, and run the complete launcher:

```bash
rm "$DEMO/direct-event.json"
python3 demo_broker.py "$DEMO/allowed/broker.sock" "$DEMO/token.txt" \
  "$DEMO/credential.txt" "$DEMO/event.json" & broker_pid=$!
trap 'kill "$broker_pid" 2>/dev/null || true; wait "$broker_pid" 2>/dev/null || true' EXIT
for attempt in 1 2 3 4 5; do test -S "$DEMO/allowed/broker.sock" && break; sleep 0.1; done
python3 - "$DEMO" "$HOST_NET" "$HOST_USER" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = {
    "guard": str(root / "runtime_guard"),
    "allowed_root": str(root / "allowed"),
    "command": [str(root / "allowed" / "runtime_probe"),
                str(root / "allowed" / "allowed.txt"), str(root / "protected.txt"),
                str(root / "allowed" / "broker.sock"), str(root / "allowed" / "request.json"),
                sys.argv[2], sys.argv[3], "FAKE-CREDENTIAL-"],
    "memory_max": 50331648, "tasks_max": 16, "cpu_percent": 50,
}
(root / "spec.json").write_text(json.dumps(spec) + "\n")
PY
NORTH_ECHO_FAKE_CREDENTIAL="$(sed -n '1p' "$DEMO/credential.txt")" \
  python3 complete_runtime.py "$DEMO/spec.json" "$DEMO/result.json"
wait "$broker_pid"
trap - EXIT
python3 -m json.tool "$DEMO/result.json"
python3 -m json.tool "$DEMO/event.json"
```

The attestation must report allowed-read and protected-denial true, direct-IP denial and private user/network namespaces true, zero capability sets, `NoNewPrivs` 1, `Seccomp` 2, CPU `50000 100000`, memory `50331648`, swap `0`, PIDs `16`, broker success, and credential absence. The separate event proves the outside broker used its credential; neither result contains it.

Prove non-disclosure and teardown before removing exact paths:

```bash
! grep -F "$(sed -n '1p' "$DEMO/credential.txt")" "$DEMO/result.json"
test ! -e "$DEMO/allowed/broker.sock"
! systemctl --user list-units --all --plain --no-legend 'north-echo-*-10-lab-*.service' | grep .
rm "$DEMO/allowed/runtime_probe" "$DEMO/allowed/allowed.txt" "$DEMO/allowed/request.json"
rm "$DEMO/runtime_guard" "$DEMO/protected.txt" "$DEMO/token.txt" "$DEMO/credential.txt"
rm "$DEMO/spec.json" "$DEMO/result.json" "$DEMO/event.json"
rmdir "$DEMO/allowed" "$DEMO"
```

## Faded practice - From one job to a batch

Before the cold capstone, practice orchestration without changing the controls.
In this disposable lesson workspace, use the JSON-list validation and ordered
trace skills from Module 04 to plan three copies of an already validated runtime
spec. Give them distinct IDs and predict what should happen for workload exit
statuses 0, 7, and 0. Write the prediction in `batch-notes.md`.

Your independent exercise is to invoke the single-job interface sequentially,
preserve IDs and statuses in input order, and inspect exact unit collection after
each invocation. Use simple local static workers, not a broker that only accepts
one connection. Change one resource budget and verify its effective cgroup value
rather than merely inspecting the input JSON.

Deliberate mistake: validate and launch the first job before looking at the
second. Make the second job's task limit zero. Explain in `batch-notes.md` why
partial execution is inappropriate for malformed input. Repair the sequence by
validating all specs and unique identities before any launch. An ordinary worker
exit of 7 is different: its spec was valid, so later jobs should still run.

Checkpoint: show ordered 0/7/0 outcomes, no remaining owned units, and rejection
of a malformed later spec before any workload runs. No batch implementation is
provided; the capstone applies these practiced operations under fresh profiles.

## Checkpoint and troubleshooting

- If the broker socket is not ready, inspect only the owned broker PID and its exact synthetic paths; do not search for or kill name-matched host processes.
- If cgroup values differ, verify the delegated user manager and controllers with `./scripts/linux-preflight`.
- If the probe exits at `execv`, confirm the static workload executable resolves beneath `allowed_root`.
- If broker access fails while `AF_INET` is denied, confirm the socket path is below the allowed root and shorter than the Unix-socket path limit.
- Checkpoint: point to one attested field for each of privilege, filesystem, syscalls, resources, network, and credential mediation, then explain which separate evidence proves teardown.
