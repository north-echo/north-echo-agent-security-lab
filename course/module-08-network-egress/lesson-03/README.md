# 08.03 - Reauthorize names, ports, redirects, and runs

## Goal

Replace one exact request with a reusable fail-closed broker that validates policy once, authorizes every hop, and never performs live DNS.

## Exercise 1 - Read the complete policy engine

```bash
sed -n '1,260p' egress_broker.py
sed -n '1,240p' redirect_services.py
sed -n '1,200p' broker_client.py
```

### Broker, block by block

- `load_policy` accepts exactly `run_id` and `destinations`. Every synthetic hostname maps to one literal IPv4 loopback address and a nonempty set of ports. Non-loopback policy is rejected before listening.
- `authorize` compares the run ID, parses only credential-free `http` URLs, rejects fragments and malformed authorities, then checks the hostname and port against the policy map. It builds an origin-form path and a controlled `Host` header.
- `fetch` accepts exactly four request fields. It authorizes the initial URL and repeats `authorize` after every redirect. It limits redirects, connection time, and response bytes.
- `receive_line` permits one bounded newline-terminated JSON document. This prevents an unbounded stream from becoming broker memory authority.
- `serve` refuses a pre-existing path, creates a mode-`0600` Unix socket, handles each request independently, converts expected failures into `ok: false`, and unlinks its socket in `finally`.
- Signal handlers request a clean loop exit. Setup or policy failure returns nonzero and never falls through to a permissive mode.

`redirect_services.py` creates an allowed service and a protected service, both on loopback, then writes a readiness file. `/same` redirects within the allowed origin; `/escape` redirects to the protected synthetic hostname. The services contain no public endpoint or real secret.

## Exercise 2 - Build a synthetic resolution policy

Choose two ports and write the only allowed name-to-address decision:

```bash
ALLOWED_PORT=$((44000 + $$ % 4000))
PROTECTED_PORT=$((48000 + $$ % 4000))
RUN_ID="redirect-$$"
SOCKET="$PWD/policy-broker.sock"
READY="$PWD/services.ready"
cat > policy.json <<EOF
{
  "run_id": "$RUN_ID",
  "destinations": {
    "allowed.test": {"address": "127.0.0.1", "ports": [$ALLOWED_PORT]}
  }
}
EOF
python3 -m json.tool policy.json
```

### Line by line

- The two ports are distinct high, synthetic endpoints.
- The here-document expands only lesson-controlled shell variables into local JSON.
- `allowed.test` is not sent to DNS. The policy's literal loopback address is the resolver decision the broker will authorize.
- `json.tool` checks syntax before the broker consumes the file.

Launch the services and broker with exact cleanup ownership:

```bash
python3 redirect_services.py "$ALLOWED_PORT" "$PROTECTED_PORT" "$READY" & service_pid=$!
python3 egress_broker.py policy.json "$SOCKET" & broker_pid=$!
trap 'kill "$broker_pid" "$service_pid" 2>/dev/null || true; wait "$broker_pid" "$service_pid" 2>/dev/null || true; rm -f "$SOCKET" "$READY"' EXIT
for attempt in 1 2 3 4 5; do test -S "$SOCKET" && test -f "$READY" && break; sleep 0.1; done
test "$(stat -c '%a' "$SOCKET")" = 600
test -f "$READY"
```

The mode check verifies an effective filesystem property rather than trusting the `chmod` call.

## Exercise 3 - Follow one redirect and deny an escape

```bash
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" "$RUN_ID" allowed.test "$ALLOWED_PORT" /same
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" "$RUN_ID" allowed.test "$ALLOWED_PORT" /escape
unshare --user --map-root-user --net python3 broker_client.py "$SOCKET" wrong-run allowed.test "$ALLOWED_PORT" /ok
```

### Line by line

- `/same` produces one relative redirect. `urljoin` keeps the allowed origin, the next loop reauthorizes it, and the result contains `allowed-final` plus `redirects: 1`.
- `/escape` is the intentional attack. The first origin is allowed, but the absolute redirect names `blocked.test` on the protected port. Reauthorization denies it before connection; the protected body is absent.
- The wrong-run request uses an otherwise valid destination but fails before network access.

Intentional mistake: temporarily add `blocked.test` and `$PROTECTED_PORT` to policy. The escape succeeds, proving that a redirect-safe algorithm cannot repair an overbroad policy. Restore the one-destination policy and require `ok: false`.

Stop and verify cleanup:

```bash
kill "$broker_pid" "$service_pid"
wait "$broker_pid" "$service_pid" 2>/dev/null || true
trap - EXIT
test ! -e "$SOCKET"
```

## Checkpoint and troubleshooting

```bash
python3 egress_broker.py policy.json "$PWD/check.sock" & check_pid=$!
for attempt in 1 2 3 4 5; do test -S "$PWD/check.sock" && break; sleep 0.1; done
kill "$check_pid"
wait "$check_pid"
test ! -e "$PWD/check.sock"
```

- If a policy hostname contains uppercase characters, normalize the policy authoring process; the broker intentionally rejects ambiguous casing.
- If a redirect reports `destination is not authorized`, inspect the new hostname and effective port. Do not allow it merely to silence the failure.
- If termination leaves a path, confirm you signaled the exact broker PID and that the process exited normally.
- Checkpoint: identify the authorization decision made before the first connection and the same decision made again before a redirect connection.
