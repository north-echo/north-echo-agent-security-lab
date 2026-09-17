# 08.01 - Remove the inherited IP network

## Goal

Prove that a new network namespace has different kernel network state and cannot reach a synthetic service bound to the parent namespace's loopback address.

## Exercise 1 - Inspect the boundary

Read both complete programs before running them:

```bash
sed -n '1,240p' local_http.py
sed -n '1,240p' connect_probe.py
```

### Source, line by line

- `local_http.py` refuses a pre-existing readiness path, creates one `HTTPServer` on `127.0.0.1`, then writes `ready`. It exits after one request and removes the readiness file in `finally`. Its fixed response is synthetic and its disabled request log avoids host-identifying noise.
- `connect_probe.py` calls `readlink` on `/proc/self/ns/net`, so the namespace identity comes from the process being tested.
- `socket.create_connection` makes exactly one bounded attempt to `127.0.0.1:PORT`; its one-second timeout prevents a failed path from hanging.
- The probe records either `connected: true` or the exception type and returns nonzero on denial. It does not treat an error message alone as proof.

Choose a lesson-local high port, start the one-request service, and connect from the current namespace:

```bash
PORT=$((42000 + $$ % 10000))
READY="$PWD/server.ready"
python3 local_http.py "$PORT" "$READY" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -f "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -f "$READY" && break; sleep 0.1; done
test -f "$READY"
python3 connect_probe.py "$PORT"
wait "$server_pid"
trap - EXIT
```

### Line by line

- The arithmetic selects a high synthetic port without privileged binding. A collision is harmless and visible; choose another value if needed.
- `&` launches only the local service; `$!` captures its exact PID for bounded cleanup.
- `trap` names that exact PID and lesson-local readiness path. It does not use a process-name pattern.
- The bounded loop waits for the server-created readiness evidence before connecting.
- The probe should print its network-namespace link, `connected: true`, and exit zero. `wait` proves the one-request server exited.

## Exercise 2 - Enter an empty network namespace

Start another one-request service, then run the probe after `unshare` creates user and network namespaces:

```bash
python3 local_http.py "$PORT" "$READY" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -f "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -f "$READY" && break; sleep 0.1; done
test -f "$READY"
set +e
unshare --user --map-root-user --net python3 connect_probe.py "$PORT"
isolated_status=$?
set -e
printf 'isolated_status=%s\n' "$isolated_status"
kill "$server_pid"
wait "$server_pid" 2>/dev/null || true
trap - EXIT
```

### Line by line

- `--user --map-root-user` gives the calling user namespace-local capability to create and configure its new network namespace; it does not grant host root.
- `--net` creates a new network namespace. Its loopback device starts down and it has no inherited host interfaces or routes.
- `set +e` permits the expected failed connection to be observed. The saved status must be nonzero.
- Killing the exact still-waiting server proves the isolated request never reached it.

Expected output includes a different `net:[NUMBER]`, `connected: false`, and usually `Network is unreachable`. Error text varies; the stable facts are the distinct namespace and failed connection.

## Exercise 3 - Repair loopback, not host reachability

Intentional mistake: assume that enabling loopback reconnects the namespace to the parent's `127.0.0.1`.

```bash
python3 local_http.py "$PORT" "$READY" &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -f "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -f "$READY" && break; sleep 0.1; done
test -f "$READY"
set +e
unshare --user --map-root-user --net sh -c 'ip link set lo up; ip -brief address show lo; python3 connect_probe.py "$1"' sh "$PORT"
loopback_status=$?
set -e
printf 'private_loopback_status=%s\n' "$loopback_status"
kill "$server_pid"
wait "$server_pid" 2>/dev/null || true
trap - EXIT
```

### Line by line

- `ip link set lo up` changes only the new namespace's loopback device.
- The quoted script receives the port as `$1`; no lesson value is interpolated as shell code.
- `127.0.0.1` now refers to the new namespace itself, not the parent's loopback service, so the connection remains denied (commonly `Connection refused`).
- The repair is conceptual: use a non-IP mediation channel in Lesson 08.02 instead of adding a veth path that broadens connectivity.

## Checkpoint and troubleshooting

```bash
test "$isolated_status" -ne 0
test "$loopback_status" -ne 0
```

- If `unshare` reports `Operation not permitted`, use the documented disposable VM and its narrow user-namespace setup; do not weaken a work host.
- If the first connection fails, select another high port and ensure no stale lesson process remains.
- Checkpoint: explain why both namespaces can have an interface named `lo` while their `127.0.0.1` services remain disjoint.
