# 09.03 - Deny replay and confused-deputy substitution

## Goal

Put a fake credential behind a Unix-socket operation broker, consume each capability once, and recheck every binding before contacting a separate synthetic upstream.

## Exercise 1 - Read the complete local system

```bash
sed -n '1,360p' capability_broker.py
sed -n '1,220p' synthetic_upstream.py
sed -n '1,180p' mint_token.py
sed -n '1,160p' broker_client.py
```

### Components, block by block

- `mint_token.py` creates the same canonical signed claims as Lesson 09.02. The client receives the token file, not the signing key or service credential.
- `broker_client.py` sends exactly token, operation, resource, audience, run, and parsed input over a filesystem Unix socket.
- `capability_broker.py` validates policy and mode-`0600` secret files before listening. It strictly decodes base64, verifies HMAC, validates the complete claim set and lifetime, and compares request fields to claims and policy.
- The broker hashes canonical request input, checks its digest, and rejects a previously consumed nonce. It consumes the nonce before calling upstream, caps the in-memory replay set, and fails closed at capacity, so a failed operation cannot make the same bearer capability reusable.
- Only after those checks does `call_upstream` read the broker-held fake credential into a request for a separate Unix socket. An upstream response that reflects the credential is rejected.
- `synthetic_upstream.py` accepts one exact fake credential, `read`, resource, and empty input. It never listens on IP and returns only a synthetic value.
- Both services use bounded lines, timeouts, mode-`0600` sockets, signal-driven exit, and exact-path unlinking.

## Exercise 2 - Launch the brokered operation

Create only fake secret material and a local policy:

```bash
umask 077
printf '%s' 'FAKE-SIGNING-KEY-09.03-ONLY-000000000000' > signing.key
printf '%s' 'FAKE-UPSTREAM-CREDENTIAL-09.03' > credential.txt
RUN_ID="run-$$"
AUDIENCE="records.lesson"
RESOURCE="record:alpha"
UPSTREAM="$PWD/upstream.sock"
BROKER="$PWD/broker.sock"
cat > policy.json <<EOF
{"version":1,"audience":"$AUDIENCE","run_id":"$RUN_ID","max_ttl":120,"upstream_socket":"$UPSTREAM","permissions":{"record:alpha":["read"],"record:beta":["read"]}}
EOF
python3 -m json.tool policy.json
```

### Line by line

- `umask 077` is verified by the broker; group- or world-accessible secret files fail setup.
- The signing key and credential are different synthetic authorities. A token signature never contains the credential.
- Policy names one audience and run, a maximum lifetime, one exact upstream socket, and an operation allowlist.
- `record:beta` exists in policy specifically so the confused-deputy test isolates token binding from broad policy denial.

Start both exact owned services and wait for their socket types:

```bash
python3 synthetic_upstream.py credential.txt "$RESOURCE" synthetic-record-value "$UPSTREAM" & upstream_pid=$!
python3 capability_broker.py policy.json signing.key credential.txt "$BROKER" & broker_pid=$!
trap 'kill "$broker_pid" "$upstream_pid" 2>/dev/null || true; wait "$broker_pid" "$upstream_pid" 2>/dev/null || true; rm -f "$BROKER" "$UPSTREAM"' EXIT
for attempt in 1 2 3 4 5; do test -S "$BROKER" && test -S "$UPSTREAM" && break; sleep 0.1; done
test "$(stat -c '%a' "$BROKER")" = 600
test "$(stat -c '%a' "$UPSTREAM")" = 600
```

The readiness and mode checks observe effective socket state. No name-prefix cleanup or unrelated process signaling is used.

Mint and spend one capability:

```bash
python3 mint_token.py signing.key token.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" 60 '{}'
python3 broker_client.py "$BROKER" token.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" '{}'
```

Expected JSON is `ok: true` with `synthetic-record-value`. Neither response nor client environment contains `FAKE-UPSTREAM-CREDENTIAL-09.03`.

## Exercise 3 - Replay and substitute

Replay the same token, then attempt to make the deputy use it for another policy-allowed resource:

```bash
python3 broker_client.py "$BROKER" token.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" '{}'
python3 mint_token.py signing.key deputy.txt read "$RESOURCE" "$AUDIENCE" "$RUN_ID" 60 '{}'
python3 broker_client.py "$BROKER" deputy.txt read record:beta "$AUDIENCE" "$RUN_ID" '{}'
```

### Line by line

- The replay returns `ok: false` because the first successful request consumed the nonce.
- `deputy.txt` is valid for `record:alpha`. The request names `record:beta`, which policy generally allows, but the token-to-request comparison denies the substitution before upstream contact.
- This is the confused-deputy repair: possession of broad broker authority does not let the caller reinterpret a narrower capability.

Intentional mistake: temporarily remove the operation/resource/request comparisons in `verify_token`. The second request advances to upstream instead of failing at the broker. Restore all comparisons and require `request does not match capability`.

Stop exact processes and verify socket cleanup:

```bash
kill "$broker_pid" "$upstream_pid"
wait "$broker_pid" "$upstream_pid"
trap - EXIT
test ! -e "$BROKER"
test ! -e "$UPSTREAM"
rm -f signing.key credential.txt policy.json token.txt deputy.txt
```

## Checkpoint and troubleshooting

```bash
test ! -e "$BROKER"
test ! -e "$UPSTREAM"
```

- If setup says secret files must be mode `0600`, inspect with `stat -c '%a'` and recreate synthetic files under `umask 077`; never broaden permissions.
- If a fresh token reports invalid time, confirm the VM clock is sane and the requested TTL does not exceed policy.
- If upstream denies an exact request, compare its resource and empty input with the policy and token; do not expose the credential for debugging.
- Checkpoint: explain why the replay set must be broker state and why signature verification alone cannot prevent replay.
