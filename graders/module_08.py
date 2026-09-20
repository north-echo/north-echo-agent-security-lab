from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from northecho.grading import Check, run_bounded


def _server(handler):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _quiet(_self, _format, *_arguments):
    pass


def _request(socket_path: Path, payload: dict) -> dict | None:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(3)
            stream.connect(str(socket_path))
            stream.sendall(json.dumps(payload).encode() + b"\n")
            stream.shutdown(socket.SHUT_WR)
            raw = stream.makefile("rb").readline(131072)
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError, TimeoutError):
        return None


def _wait_for_socket(path: Path, process: subprocess.Popen) -> bool:
    for _ in range(60):
        if path.exists():
            return stat.S_ISSOCK(path.stat().st_mode)
        if process.poll() is not None:
            return False
        time.sleep(0.05)
    return False


def _stopped(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def _direct_isolated(port: int) -> bool:
    code = """
import json, os, socket, sys
result = {"network_namespace": os.readlink("/proc/self/ns/net"), "connected": False}
try:
    with socket.create_connection(("127.0.0.1", int(sys.argv[1])), .5):
        result["connected"] = True
except OSError:
    pass
print(json.dumps(result))
"""
    run = run_bounded(
        ["unshare", "--user", "--map-root-user", "--net", sys.executable, "-c", code, str(port)],
        text=True, capture_output=True, timeout=3,
    )
    try:
        observed = json.loads(run.stdout)
        return bool(
            run.returncode == 0 and isinstance(observed, dict)
            and observed.get("connected") is False
            and isinstance(observed.get("network_namespace"), str)
            and observed["network_namespace"].startswith("net:[")
            and observed["network_namespace"] != os.readlink("/proc/self/ns/net")
        )
    except (ValueError, TypeError):
        return False


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "egress_broker.py"
    if not source.is_file():
        return [Check("An egress broker is present", False, "Module 08 lab contract")]

    protected_hits = {"count": 0}
    canary = fixture["canary"]

    class Protected(BaseHTTPRequestHandler):
        log_message = _quiet

        def do_GET(self):
            protected_hits["count"] += 1
            body = ("protected:" + canary).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    protected, protected_thread = _server(Protected)
    protected_port = protected.server_address[1]

    class Allowed(BaseHTTPRequestHandler):
        log_message = _quiet

        def do_GET(self):
            if self.path == "/same":
                self.send_response(302)
                self.send_header("Location", "/ok")
                self.end_headers()
                return
            if self.path == "/escape-name":
                self.send_response(302)
                self.send_header("Location", f"http://blocked-{fixture['hostname']}:{protected_port}/secret")
                self.end_headers()
                return
            if self.path == "/escape-address":
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{protected_port}/secret")
                self.end_headers()
                return
            body = ("approved:" + canary).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    allowed, allowed_thread = _server(Allowed)
    allowed_port = allowed.server_address[1]
    allowed_host = f"allowed-{fixture['hostname']}"
    run_id = f"run-{fixture['hostname']}"

    checks: dict[str, bool] = {}
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix="ne08-") as raw:
            work = Path(raw)
            agent = work / "egress_broker.py"
            shutil.copy2(source, agent)
            agent.chmod(0o444)
            policy = work / "policy.json"
            policy.write_text(json.dumps({
                "run_id": run_id,
                "destinations": {allowed_host: {"address": "127.0.0.1", "ports": [allowed_port]}},
            }), encoding="utf-8")
            socket_path = work / "broker.sock"
            process = subprocess.Popen(
                [sys.executable, str(agent), str(policy), str(socket_path)],
                cwd=work,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            ready = _wait_for_socket(socket_path, process)
            checks["ready"] = ready and stat.S_IMODE(socket_path.stat().st_mode) == 0o600

            def ask(host=allowed_host, port=allowed_port, path="/ok", identity=run_id):
                return _request(socket_path, {"run_id": identity, "host": host, "port": port, "path": path}) if ready else None

            approved = ask()
            checks["approved"] = bool(approved and approved.get("ok") is True and approved.get("status") == 200 and approved.get("body") == f"approved:{canary}")
            wrong_run = ask(identity=run_id + "-wrong")
            checks["run"] = bool(wrong_run and wrong_run.get("ok") is False)
            blocked_name = ask(host=f"blocked-{fixture['hostname']}", port=protected_port)
            checks["name"] = bool(blocked_name and blocked_name.get("ok") is False)
            blocked_port = ask(port=protected_port)
            checks["port"] = bool(blocked_port and blocked_port.get("ok") is False)
            same = ask(path="/same")
            checks["same_redirect"] = bool(same and same.get("ok") is True and same.get("redirects") == 1 and same.get("body") == f"approved:{canary}")
            before = protected_hits["count"]
            escaped_name = ask(path="/escape-name")
            escaped_address = ask(path="/escape-address")
            checks["redirect"] = bool(
                escaped_name and escaped_name.get("ok") is False
                and escaped_address and escaped_address.get("ok") is False
                and protected_hits["count"] == before
            )
            malformed = _request(socket_path, {"run_id": run_id, "host": allowed_host, "port": allowed_port, "path": "/ok", "address": "127.0.0.1"}) if ready else None
            checks["shape"] = bool(malformed and malformed.get("ok") is False)
            _stopped(process)
            for _ in range(30):
                if not socket_path.exists():
                    break
                time.sleep(0.05)
            checks["cleanup"] = process.returncode == 0 and not socket_path.exists()

            unsafe_policy = work / "unsafe-policy.json"
            unsafe_policy.write_text(json.dumps({
                "run_id": run_id,
                "destinations": {allowed_host: {"address": "192.0.2.1", "ports": [80]}},
            }), encoding="utf-8")
            unsafe_socket = work / "unsafe.sock"
            unsafe = run_bounded(
                [sys.executable, str(agent), str(unsafe_policy), str(unsafe_socket)],
                cwd=work,
                text=True,
                capture_output=True,
                timeout=3,
            )
            checks["loopback"] = unsafe.returncode != 0 and not unsafe_socket.exists()

            checks["isolated"] = _direct_isolated(allowed_port)
    finally:
        if process is not None:
            _stopped(process)
        allowed.shutdown()
        protected.shutdown()
        allowed.server_close()
        protected.server_close()
        allowed_thread.join(timeout=2)
        protected_thread.join(timeout=2)

    return [
        Check("Broker creates a private Unix socket", checks.get("ready", False), "Module 08 lesson 02"),
        Check("Approved synthetic request succeeds", checks.get("approved", False), "Module 08 lesson 02"),
        Check("Request is bound to the authorized run", checks.get("run", False), "Module 08 lesson 03"),
        Check("Unapproved name is denied", checks.get("name", False), "Module 08 lesson 03"),
        Check("Unapproved port is denied", checks.get("port", False), "Module 08 lesson 03"),
        Check("Approved same-origin redirect succeeds", checks.get("same_redirect", False), "Module 08 lesson 03"),
        Check("Redirect name and address escapes are denied before contact", checks.get("redirect", False), "Module 08 lesson 03"),
        Check("Extra authority-bearing fields fail closed", checks.get("shape", False), "Module 08 lesson 03"),
        Check("Policy cannot authorize a non-loopback address", checks.get("loopback", False), "Module 08 lesson 03"),
        Check("Isolated client has no direct IP path", checks.get("isolated", False), "Module 08 lesson 01"),
        Check("Broker exits cleanly and removes its socket", checks.get("cleanup", False), "Module 08 lesson 02"),
    ]
