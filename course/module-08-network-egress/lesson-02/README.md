# 08.02 - Reach one service through a Unix-socket broker

## Goal

Keep the workload's IP network empty while giving it one structured operation through a filesystem `AF_UNIX` socket.

## Exercise 1 - Read the three complete components

```bash
sed -n '1,240p' synthetic_http.py
sed -n '1,280p' one_host_broker.py
sed -n '1,240p' broker_client.py
```

### Source, line by line

- `synthetic_http.py` serves a fixed response on host loopback and writes a lesson-local readiness file after binding. It is the only IP service.
- `one_host_broker.py` refuses an existing socket path, binds `AF_UNIX`, sets mode `0600`, and accepts one client.
- The broker requires an exact JSON object containing the allowed run, host, port, and `/ok` path. Extra fields fail because dictionary equality is exact.
- Only after authorization does the broker connect to literal `127.0.0.1`. The requested synthetic name becomes the HTTP `Host` header, not a DNS lookup.
- The broker bounds its input line and upstream body, returns one JSON line, closes descriptors, and unlinks its socket in `finally`.
- `broker_client.py` preserves typed fields in JSON, uses `AF_UNIX`, half-closes its write side, and reads one response line.

## Exercise 2 - Compare direct and mediated paths

Launch exact owned processes with a cleanup trap:

```bash
PORT=$((43000 + $$ % 9000))
RUN_ID="lesson-$$"
SOCKET="$PWD/broker.sock"
READY="$PWD/service.ready"
python3 synthetic_http.py "$PORT" "$READY" & service_pid=$!
python3 one_host_broker.py "$SOCKET" "$RUN_ID" allowed.test "$PORT" & broker_pid=$!
trap 'kill "$broker_pid" "$service_pid" 2>/dev/null || true; wait "$broker_pid" "$service_pid" 2>/dev/null || true; rm -f "$SOCKET" "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -S "$SOCKET" && test -f "$READY" && break; sleep 0.1; done
test -S "$SOCKET"
test -f "$READY"
```

### Line by line

- Both background PIDs come from processes launched in this shell and are saved immediately.
- The socket is placed in the disposable lesson workspace, not a shared system directory.
- The bounded readiness loop checks the actual socket type; it does not sleep indefinitely.
- The trap removes only exact PIDs and the exact lesson path.

First prove direct IP still fails, then use the Unix socket:

```bash
set +e
unshare --user --map-root-user --net python3 -c 'import socket,sys; socket.create_connection(("127.0.0.1",int(sys.argv[1])),1)' "$PORT"
direct_status=$?
set -e
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" "$RUN_ID" allowed.test "$PORT" /ok
wait "$broker_pid"
kill "$service_pid"
wait "$service_pid" 2>/dev/null || true
trap - EXIT
```

### Line by line

- The direct probe runs inside a new empty network namespace and must return nonzero.
- The second `unshare` creates another empty network namespace, but Unix sockets are filesystem objects and remain reachable through the shared workspace mount.
- The broker, outside the network namespace, performs the one authorized loopback request and returns `approved-through-broker`.
- The one-request broker exits and removes its socket. The exact service PID is then stopped and reaped.

The workload did not gain a route, interface, DNS resolver, or general TCP proxy. It gained one operation-shaped capability.

## Exercise 3 - Break and repair request binding

Repeat the launch block, then intentionally send the wrong run ID:

```bash
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" wrong-run allowed.test "$PORT" /ok
```

Expected JSON has `"ok": false` and `request is not authorized`; the upstream service receives nothing. The mistake is treating access to the socket pathname as sufficient authority. Repair it by sending the exact `$RUN_ID` and retain both checks in later policy.

## Checkpoint and troubleshooting

```bash
test "$direct_status" -ne 0
test ! -e "$SOCKET"
```

- If the socket path already exists, remove it only after proving it is the exact lesson path and no owned broker is running.
- If the client gets `Connection refused`, inspect the bounded readiness loop and exact saved PID.
- Checkpoint: explain why an `AF_UNIX` connection crosses this network-namespace boundary without restoring any IP destination authority.
