#!/usr/bin/env python3
"""Policy-bound loopback HTTP broker over a Unix-domain socket."""

from __future__ import annotations

import http.client
import ipaddress
import json
import os
from pathlib import Path
import signal
import socket
import sys
from urllib.parse import urljoin, urlsplit

MAX_LINE = 8192
MAX_BODY = 65536
MAX_REDIRECTS = 4
stopping = False


class Denied(Exception):
    pass


def load_policy(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if set(raw) != {"run_id", "destinations"} or not isinstance(raw["run_id"], str):
        raise Denied("invalid policy shape")
    if not raw["run_id"] or len(raw["run_id"]) > 128 or not isinstance(raw["destinations"], dict):
        raise Denied("invalid policy values")
    destinations = {}
    for host, rule in raw["destinations"].items():
        if not isinstance(host, str) or host != host.lower() or not host or len(host) > 253:
            raise Denied("invalid policy hostname")
        if not isinstance(rule, dict) or set(rule) != {"address", "ports"}:
            raise Denied("invalid destination rule")
        address = ipaddress.ip_address(rule["address"])
        if address.version != 4 or not address.is_loopback:
            raise Denied("only IPv4 loopback destinations are permitted")
        ports = rule["ports"]
        if not isinstance(ports, list) or not ports or any(type(p) is not int or not 1 <= p <= 65535 for p in ports):
            raise Denied("invalid destination ports")
        destinations[host] = {"address": str(address), "ports": frozenset(ports)}
    if not destinations:
        raise Denied("policy has no destinations")
    return {"run_id": raw["run_id"], "destinations": destinations}


def authorize(policy: dict, run_id: object, url: str) -> tuple[str, str, int, str]:
    if run_id != policy["run_id"]:
        raise Denied("run identity is not authorized")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.username is not None or parsed.password is not None:
        raise Denied("only credential-free HTTP URLs are permitted")
    if parsed.fragment or not parsed.hostname or parsed.hostname != parsed.hostname.lower():
        raise Denied("invalid destination URL")
    try:
        port = parsed.port or 80
    except ValueError as error:
        raise Denied("invalid destination port") from error
    rule = policy["destinations"].get(parsed.hostname)
    if rule is None or port not in rule["ports"]:
        raise Denied("destination is not authorized")
    request_path = parsed.path or "/"
    if not request_path.startswith("/") or request_path.startswith("//"):
        raise Denied("invalid request path")
    if parsed.query:
        request_path += "?" + parsed.query
    authority = parsed.hostname if port == 80 else f"{parsed.hostname}:{port}"
    return rule["address"], authority, port, request_path


def fetch(policy: dict, request: dict) -> dict:
    if not isinstance(request, dict) or set(request) != {"run_id", "host", "port", "path"}:
        raise Denied("invalid request shape")
    host, port, path = request["host"], request["port"], request["path"]
    if not isinstance(host, str) or type(port) is not int or not isinstance(path, str):
        raise Denied("invalid request values")
    url = f"http://{host}:{port}{path}"
    for redirects in range(MAX_REDIRECTS + 1):
        address, authority, port, request_path = authorize(policy, request["run_id"], url)
        connection = http.client.HTTPConnection(address, port, timeout=2)
        try:
            connection.request("GET", request_path, headers={"Host": authority, "Connection": "close"})
            response = connection.getresponse()
            body = response.read(MAX_BODY + 1)
            if len(body) > MAX_BODY:
                raise Denied("response body exceeds limit")
            location = response.getheader("Location")
            status = response.status
        finally:
            connection.close()
        if status not in {301, 302, 303, 307, 308}:
            return {"ok": True, "status": status, "body": body.decode("utf-8", "replace"), "redirects": redirects}
        if not location:
            raise Denied("redirect has no location")
        url = urljoin(url, location)
    raise Denied("redirect limit exceeded")


def receive_line(peer: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_LINE:
        chunk = peer.recv(min(1024, MAX_LINE + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if len(data) > MAX_LINE or not data.endswith(b"\n"):
        raise Denied("request must be one bounded line")
    return bytes(data)


def serve(policy: dict, socket_path: Path) -> None:
    if socket_path.exists() or socket_path.is_symlink():
        raise Denied("socket path already exists")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socket_path))
    os.chmod(socket_path, 0o600)
    listener.listen(8)
    listener.settimeout(0.2)
    try:
        while not stopping:
            try:
                peer, _ = listener.accept()
            except TimeoutError:
                continue
            with peer:
                try:
                    request = json.loads(receive_line(peer))
                    response = fetch(policy, request)
                except (Denied, json.JSONDecodeError, UnicodeError, OSError, http.client.HTTPException) as error:
                    response = {"ok": False, "error": str(error)}
                peer.sendall(json.dumps(response, sort_keys=True).encode() + b"\n")
    finally:
        listener.close()
        socket_path.unlink(missing_ok=True)


def stop(_signum, _frame):
    global stopping
    stopping = True


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} POLICY.json SOCKET", file=sys.stderr)
        return 2
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        serve(load_policy(Path(sys.argv[1])), Path(sys.argv[2]))
    except (OSError, ValueError, json.JSONDecodeError, Denied) as error:
        print(f"broker setup denied: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
