#!/usr/bin/env python3
"""Mint a lesson capability; signing material stays outside the client."""

import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sys
import time


def encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


if len(sys.argv) != 9:
    raise SystemExit(f"usage: {sys.argv[0]} KEY TOKEN OP RESOURCE AUDIENCE RUN TTL INPUT_JSON")
key = Path(sys.argv[1]).read_bytes()
ttl = int(sys.argv[7])
if not 1 <= ttl <= 300:
    raise SystemExit("TTL must be 1..300 seconds")
issued = int(time.time())
input_value = json.loads(sys.argv[8])
claims = {
    "version": 1,
    "operation": sys.argv[3],
    "resource": sys.argv[4],
    "audience": sys.argv[5],
    "run_id": sys.argv[6],
    "issued_at": issued,
    "expires_at": issued + ttl,
    "nonce": secrets.token_hex(16),
    "input_sha256": hashlib.sha256(canonical(input_value)).hexdigest(),
}
payload = encode(canonical(claims))
signature = encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())
Path(sys.argv[2]).write_text(payload + "." + signature + "\n", encoding="utf-8")
print("capability minted")
