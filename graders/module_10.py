from __future__ import annotations

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

from northecho.grading import Check


class Broker:
    def __init__(self, path: Path, token: str, credential: str):
        self.path = path
        self.token = token
        self.credential = credential
        self.used_credentials: list[str] = []
        self.stop_event = threading.Event()
        self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listener.bind(str(path))
        os.chmod(path, 0o600)
        self.listener.listen(4)
        self.listener.settimeout(0.1)
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        while not self.stop_event.is_set():
            try:
                peer, _ = self.listener.accept()
            except TimeoutError:
                continue
            with peer:
                try:
                    request = json.loads(peer.makefile("rb").readline(16384))
                    if request == {"operation": "read", "resource": "synthetic:record", "token": self.token}:
                        self.used_credentials.append(self.credential)
                        response = {"ok": True, "result": {"value": "synthetic-result"}}
                    else:
                        response = {"ok": False, "error": "capability denied"}
                except (OSError, json.JSONDecodeError):
                    response = {"ok": False, "error": "invalid request"}
                try:
                    peer.sendall(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")
                except OSError:
                    pass

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=2)
        self.listener.close()
        self.path.unlink(missing_ok=True)


def _compile(source: Path, output: Path, *extra: str) -> bool:
    run = subprocess.run(
        ["gcc", "-O2", "-Wall", "-Wextra", "-static", str(source), "-o", str(output), *extra],
        text=True, capture_output=True, check=False,
    )
    return run.returncode == 0


def _invoke(agent: Path, spec: Path, result: Path, cwd: Path, credential: str):
    environment = dict(os.environ)
    environment["NORTH_ECHO_FAKE_CREDENTIAL"] = credential
    try:
        return subprocess.run(
            [sys.executable, str(agent), str(spec), str(result)], cwd=cwd,
            text=True, capture_output=True, timeout=25, env=environment,
        )
    except subprocess.TimeoutExpired:
        return None


def _load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "complete_runtime.py"
    if not source.is_file():
        return [Check("A complete-runtime launcher is present", False, "Module 10 lab contract")]

    results: dict[str, bool] = {}
    output = ""
    broker: Broker | None = None
    with tempfile.TemporaryDirectory(prefix="north-echo-grade-10-") as raw:
        work = Path(raw)
        agent = work / "complete_runtime.py"
        shutil.copy2(source, agent)
        agent.chmod(0o444)
        course = Path(__file__).resolve().parents[1] / "course" / "module-10-complete-runtime"
        guard = work / "runtime_guard"
        probe = work / "runtime_probe"
        compiled = _compile(course / "lesson-02" / "runtime_guard.c", guard, "-lseccomp")
        compiled = _compile(course / "lesson-03" / "runtime_probe.c", probe) and compiled
        if not compiled:
            return [Check("Native composition probes compile", False, "Module 10 lessons 02-03")]

        allowed = work / "allowed literal $(not-a-shell)"
        allowed.mkdir(mode=0o700)
        workload = allowed / "runtime_probe"
        shutil.copy2(probe, workload)
        allowed_file = allowed / "allowed.txt"
        protected_file = work / "protected.txt"
        allowed_file.write_text("allowed\n", encoding="utf-8")
        protected_file.write_text(fixture["canary"] + "\n", encoding="utf-8")
        token = "CAP-" + fixture["hostname"]
        credential = "FAKE-CREDENTIAL-" + fixture["canary"]
        request = allowed / "request.json"
        request.write_text(json.dumps({
            "operation": "read", "resource": "synthetic:record", "token": token,
        }, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        broker_path = allowed / "broker.sock"
        broker = Broker(broker_path, token, credential)
        host_net_inode = os.stat("/proc/self/ns/net").st_ino
        host_user_inode = os.stat("/proc/self/ns/user").st_ino
        spec_value = {
            "guard": str(guard), "allowed_root": str(allowed),
            "command": [str(workload), str(allowed_file), str(protected_file),
                        str(broker_path), str(request), str(host_net_inode), str(host_user_inode),
                        "FAKE-CREDENTIAL-"],
            "memory_max": 50331648, "tasks_max": 16, "cpu_percent": 50,
        }
        spec = work / "spec.json"
        result_path = work / "result.json"
        spec.write_text(json.dumps(spec_value), encoding="utf-8")
        run = _invoke(agent, spec, result_path, work, credential)
        result = _load(result_path)
        attestation = result.get("attestation") if isinstance(result, dict) else None
        output = ((result.get("stdout", "") + result.get("stderr", ""))
                  if isinstance(result, dict) else "")
        results["result"] = bool(run and run.returncode == 0 and result and
                                 result.get("schema") == 1 and result.get("status") == 0 and
                                 isinstance(attestation, dict))
        results["cgroup"] = bool(attestation and attestation.get("cpu") == "50000 100000" and
                                 attestation.get("memory") == "50331648" and
                                 attestation.get("swap") == "0" and attestation.get("pids") == "16")
        results["network"] = bool(attestation and attestation.get("private_net") is True and
                                  attestation.get("private_user") is True and
                                  attestation.get("inet_denied") is True)
        results["privilege"] = bool(attestation and attestation.get("caps_zero") is True and
                                    attestation.get("no_new_privs") == 1)
        results["kernel_policy"] = bool(attestation and attestation.get("seccomp") == 2 and
                                        attestation.get("allowed_read") is True and
                                        attestation.get("protected_denied") is True)
        results["broker"] = bool(attestation and attestation.get("broker_ok") is True and
                                 broker.used_credentials == [credential])
        results["credential"] = bool(attestation and attestation.get("credential_absent") is True and
                                     credential not in output and fixture["canary"] not in output)
        results["literal"] = not (work / "not-a-shell").exists()

        failing = allowed / "failing_probe"
        failing_source = work / "failing_probe.c"
        failing_source.write_text(
            '#include <stdio.h>\nint main(void){fputs("expected-failure\\n",stderr);return 7;}\n',
            encoding="utf-8",
        )
        fail_compiled = _compile(failing_source, failing)
        fail_spec_value = dict(spec_value)
        fail_spec_value["command"] = [str(failing)]
        fail_spec = work / "fail-spec.json"
        fail_result_path = work / "fail-result.json"
        fail_spec.write_text(json.dumps(fail_spec_value), encoding="utf-8")
        fail_run = _invoke(agent, fail_spec, fail_result_path, work, credential) if fail_compiled else None
        fail_result = _load(fail_result_path)
        results["failure"] = bool(fail_run and fail_run.returncode != 0 and fail_result and
                                  fail_result.get("status") == 7 and
                                  "expected-failure" in fail_result.get("stderr", ""))

        bad_root_value = dict(spec_value)
        bad_root_value["command"] = ["/bin/true"]
        bad_root_spec = work / "bad-root-spec.json"
        bad_root_result = work / "bad-root-result.json"
        bad_root_spec.write_text(json.dumps(bad_root_value), encoding="utf-8")
        bad_root_run = _invoke(agent, bad_root_spec, bad_root_result, work, credential)

        bad_limit_value = dict(spec_value)
        bad_limit_value["memory_max"] = 0
        bad_limit_spec = work / "bad-limit-spec.json"
        bad_limit_result = work / "bad-limit-result.json"
        bad_limit_spec.write_text(json.dumps(bad_limit_value), encoding="utf-8")
        bad_limit_run = _invoke(agent, bad_limit_spec, bad_limit_result, work, credential)
        results["invalid"] = bool(
            bad_root_run and bad_root_run.returncode != 0 and not bad_root_result.exists() and
            bad_limit_run and bad_limit_run.returncode != 0 and not bad_limit_result.exists()
        )

        units = subprocess.run(
            ["systemctl", "--user", "list-units", "--all", "--plain", "--no-legend",
             f"north-echo-{os.getuid()}-10-lab-*.service"],
            text=True, capture_output=True, check=False,
        )
        results["cleanup"] = units.returncode == 0 and not units.stdout.strip()
        broker.stop()
        broker = None
        results["socket_cleanup"] = not broker_path.exists()
    if broker is not None:
        broker.stop()

    return [
        Check("A structured effective-state attestation is returned", results.get("result", False), "Module 10 lesson 03"),
        Check("CPU, memory, swap, and PID limits are effective", results.get("cgroup", False), "Module 10 lesson 03; Module 07"),
        Check("Private user/network namespaces and direct-IP denial are effective", results.get("network", False), "Module 10 lesson 03; Modules 02 and 08"),
        Check("Capability sets are empty and no-new-privileges is set", results.get("privilege", False), "Module 10 lesson 02; Module 03"),
        Check("Landlock and seccomp enforce the workload policy", results.get("kernel_policy", False), "Module 10 lesson 02; Modules 05-06"),
        Check("The operation broker uses its fake credential", results.get("broker", False), "Module 10 lesson 03; Module 09"),
        Check("The workload and its output contain no fake credential", results.get("credential", False), "Module 10 lesson 03; Module 09"),
        Check("Literal paths are preserved without shell evaluation", results.get("literal", False), "Module 10 lesson 03; Module 04"),
        Check("Workload failure status and stderr propagate", results.get("failure", False), "Module 10 lesson 03"),
        Check("Invalid roots and unbounded limits fail closed", results.get("invalid", False), "Module 10 lab contract"),
        Check("Transient units and broker sockets are removed", results.get("cleanup", False) and results.get("socket_cleanup", False), "Module 10 lesson 03"),
    ]
