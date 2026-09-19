from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from contextlib import ExitStack
import threading
import time
from pathlib import Path

from northecho.grading import Check, stop_process


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _mint(key: bytes, operation: str, resource: str, audience: str, run_id: str, input_value: object, *, issued: int | None = None, expires: int | None = None, nonce: str | None = None) -> str:
    now = int(time.time()) if issued is None else issued
    claims = {
        "version": 1,
        "operation": operation,
        "resource": resource,
        "audience": audience,
        "run_id": run_id,
        "issued_at": now,
        "expires_at": now + 60 if expires is None else expires,
        "nonce": nonce or secrets.token_hex(16),
        "input_sha256": hashlib.sha256(_canonical(input_value)).hexdigest(),
    }
    payload = _encode(_canonical(claims))
    return payload + "." + _encode(hmac.new(key, payload.encode(), hashlib.sha256).digest())


class Upstream:
    def __init__(self, path: Path, credential: str, values: dict[str, str]):
        self.path = path
        self.credential = credential
        self.values = values
        self.events: list[dict] = []
        self.stop_event = threading.Event()
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.listener.bind(str(path))
        except OSError:
            self.listener.close()
            raise
        self.listener.listen(8)
        self.listener.settimeout(0.1)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop_event.is_set():
            try:
                peer, _ = self.listener.accept()
            except TimeoutError:
                continue
            with peer:
                peer.settimeout(2)
                try:
                    raw = peer.makefile("rb").readline(65536)
                    request = json.loads(raw)
                    self.events.append(request)
                    if set(request) != {"credential", "operation", "resource", "input"}:
                        response = {"ok": False, "error": "bad shape"}
                    elif request["credential"] != self.credential or request["operation"] != "read" or request["input"] != {}:
                        response = {"ok": False, "error": "denied"}
                    elif request["resource"] not in self.values:
                        response = {"ok": False, "error": "missing"}
                    else:
                        response = {"ok": True, "result": {"value": self.values[request["resource"]]}}
                except (OSError, json.JSONDecodeError):
                    response = {"ok": False, "error": "invalid"}
                try:
                    peer.sendall(_canonical(response) + b"\n")
                except OSError:
                    pass

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=2)
        self.listener.close()
        self.path.unlink(missing_ok=True)


def _wait_socket(path: Path, process: subprocess.Popen) -> bool:
    for _ in range(60):
        if path.exists():
            return stat.S_ISSOCK(path.stat().st_mode)
        if process.poll() is not None:
            return False
        time.sleep(0.05)
    return False


def _ask(path: Path, request: dict) -> dict | None:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(3)
            stream.connect(str(path))
            stream.sendall(_canonical(request) + b"\n")
            stream.shutdown(socket.SHUT_WR)
            value = json.loads(stream.makefile("rb").readline(65536))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError, TimeoutError):
        return None


def _request(token: str, operation: str, resource: str, audience: str, run_id: str, input_value: object) -> dict:
    return {"token": token, "operation": operation, "resource": resource, "audience": audience, "run_id": run_id, "input": input_value}


def _stop_process(process: subprocess.Popen) -> tuple[str, str]:
    if process.poll() is None:
        process.terminate()
    try:
        stdout, stderr = process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=3)
    return stdout, stderr


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "capability_broker.py"
    if not source.is_file():
        return [Check("A capability broker is present", False, "Module 09 lab contract")]

    results: dict[str, bool] = {}
    response_texts: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ne09-") as raw, ExitStack() as owned:
        work = Path(raw)
        agent = work / "capability_broker.py"
        shutil.copy2(source, agent)
        agent.chmod(0o444)
        key = secrets.token_bytes(32)
        credential = "FAKE-CREDENTIAL-" + fixture["canary"]
        audience = "broker-" + fixture["hostname"]
        run_id = "run-" + secrets.token_hex(6)
        resource_a = "record:" + secrets.token_hex(4)
        resource_b = "record:" + secrets.token_hex(4)
        value_a = "value-" + secrets.token_hex(12)
        value_b = "value-" + secrets.token_hex(12)
        key_path = work / "signing.key"
        credential_path = work / "credential.txt"
        key_path.write_bytes(key)
        credential_path.write_text(credential + "\n", encoding="utf-8")
        key_path.chmod(0o600)
        credential_path.chmod(0o600)
        upstream_path = work / "upstream.sock"
        upstream = Upstream(upstream_path, credential, {resource_a: value_a, resource_b: value_b})
        owned.callback(upstream.stop)
        policy_path = work / "policy.json"
        policy_path.write_text(json.dumps({
            "version": 1,
            "audience": audience,
            "run_id": run_id,
            "max_ttl": 120,
            "upstream_socket": str(upstream_path),
            "permissions": {resource_a: ["read"], resource_b: ["read"]},
        }), encoding="utf-8")
        broker_path = work / "broker.sock"
        process = subprocess.Popen(
            [sys.executable, str(agent), str(policy_path), str(key_path), str(credential_path), str(broker_path)],
            cwd=work,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        owned.callback(stop_process, process)
        ready = _wait_socket(broker_path, process)
        results["socket"] = ready and stat.S_IMODE(broker_path.stat().st_mode) == 0o600

        def ask(request):
            response = _ask(broker_path, request) if ready else None
            response_texts.append(json.dumps(response, sort_keys=True))
            return response

        initial_events = len(upstream.events)
        token = _mint(key, "read", resource_a, audience, run_id, {})
        approved = ask(_request(token, "read", resource_a, audience, run_id, {}))
        results["approved"] = bool(approved and approved.get("ok") is True and approved.get("result") == {"value": value_a})
        results["credential_used"] = len(upstream.events) == initial_events + 1 and upstream.events[-1].get("credential") == credential

        before = len(upstream.events)
        replay = ask(_request(token, "read", resource_a, audience, run_id, {}))
        results["replay"] = bool(replay and replay.get("ok") is False and len(upstream.events) == before)

        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        before = len(upstream.events)
        tamper_response = ask(_request(tampered, "read", resource_a, audience, run_id, {}))
        results["tamper"] = bool(tamper_response and tamper_response.get("ok") is False and len(upstream.events) == before)

        before = len(upstream.events)
        wrong_aud = "other-" + audience
        wrong_aud_response = ask(_request(_mint(key, "read", resource_a, wrong_aud, run_id, {}), "read", resource_a, wrong_aud, run_id, {}))
        wrong_run = "other-" + run_id
        wrong_run_response = ask(_request(_mint(key, "read", resource_a, audience, wrong_run, {}), "read", resource_a, audience, wrong_run, {}))
        results["identity"] = bool(wrong_aud_response and wrong_aud_response.get("ok") is False and wrong_run_response and wrong_run_response.get("ok") is False and len(upstream.events) == before)

        now = int(time.time())
        before = len(upstream.events)
        expired = _mint(key, "read", resource_a, audience, run_id, {}, issued=now - 10, expires=now - 1)
        future = _mint(key, "read", resource_a, audience, run_id, {}, issued=now + 10, expires=now + 20)
        long_lived = _mint(key, "read", resource_a, audience, run_id, {}, issued=now, expires=now + 121)
        time_responses = [ask(_request(item, "read", resource_a, audience, run_id, {})) for item in (expired, future, long_lived)]
        results["time"] = all(item and item.get("ok") is False for item in time_responses) and len(upstream.events) == before

        before = len(upstream.events)
        deputy_token = _mint(key, "read", resource_a, audience, run_id, {})
        resource_swap = ask(_request(deputy_token, "read", resource_b, audience, run_id, {}))
        operation_swap = ask(_request(_mint(key, "read", resource_a, audience, run_id, {}), "append", resource_a, audience, run_id, {}))
        input_swap = ask(_request(_mint(key, "read", resource_a, audience, run_id, {}), "read", resource_a, audience, run_id, {"extra": True}))
        results["binding"] = all(item and item.get("ok") is False for item in (resource_swap, operation_swap, input_swap)) and len(upstream.events) == before

        before = len(upstream.events)
        unauthorized = ask(_request(_mint(key, "append", resource_a, audience, run_id, {}), "append", resource_a, audience, run_id, {}))
        extra = _request(_mint(key, "read", resource_a, audience, run_id, {}), "read", resource_a, audience, run_id, {})
        extra["credential"] = credential
        malformed = ask(extra)
        results["policy_shape"] = bool(unauthorized and unauthorized.get("ok") is False and malformed and malformed.get("ok") is False and len(upstream.events) == before)

        stdout, stderr = _stop_process(process)
        for _ in range(30):
            if not broker_path.exists():
                break
            time.sleep(0.05)
        results["cleanup"] = process.returncode == 0 and not broker_path.exists()
        all_client_output = "\n".join(response_texts) + stdout + stderr
        results["secret"] = credential not in all_client_output and key.hex() not in all_client_output

        key_path.chmod(0o644)
        unsafe_path = work / "unsafe-broker.sock"
        unsafe = subprocess.Popen(
            [sys.executable, str(agent), str(policy_path), str(key_path), str(credential_path), str(unsafe_path)],
            cwd=work,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        owned.callback(stop_process, unsafe)
        unsafe_ready = _wait_socket(unsafe_path, unsafe)
        unsafe_stdout, unsafe_stderr = _stop_process(unsafe)
        results["secret_mode"] = not unsafe_ready and unsafe.returncode != 0 and not unsafe_path.exists()
        all_client_output += unsafe_stdout + unsafe_stderr
        results["secret"] = results["secret"] and credential not in all_client_output and key.hex() not in all_client_output

    return [
        Check("Broker creates a private Unix socket", results.get("socket", False), "Module 09 lesson 03"),
        Check("Valid operation capability reaches the synthetic upstream", results.get("approved", False), "Module 09 lessons 02-03"),
        Check("Broker uses the fake credential only upstream", results.get("credential_used", False), "Module 09 lessons 01 and 03"),
        Check("Fake credential and signing key are never disclosed", results.get("secret", False), "Module 09 lessons 01-03"),
        Check("A consumed capability cannot be replayed", results.get("replay", False), "Module 09 lesson 03"),
        Check("A modified token is denied before upstream contact", results.get("tamper", False), "Module 09 lesson 02"),
        Check("Audience and run identity are both bound", results.get("identity", False), "Module 09 lessons 02-03"),
        Check("Expired, future, and overlong capabilities are denied", results.get("time", False), "Module 09 lessons 02-03"),
        Check("Operation, resource, and input cannot be substituted", results.get("binding", False), "Module 09 lesson 03"),
        Check("Policy and request shape deny extra authority", results.get("policy_shape", False), "Module 09 lesson 03"),
        Check("Insecure secret-file permissions fail before listen", results.get("secret_mode", False), "Module 09 lesson 03"),
        Check("Broker exits cleanly and removes its socket", results.get("cleanup", False), "Module 09 lesson 03"),
    ]
