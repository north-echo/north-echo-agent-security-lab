from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from northecho.grading import Check, result_object, run_bounded


PROBE = r'''import json, os, sys
cg = next(line.split("::", 1)[1].strip() for line in open("/proc/self/cgroup") if line.startswith("0::"))
base = "/sys/fs/cgroup" + cg
def read(name): return open(base + "/" + name).read().strip()
mode = sys.argv[1]
if mode == "inspect":
 print(json.dumps({"cpu":read("cpu.max"),"memory":read("memory.max"),"swap":read("memory.swap.max"),"pids":read("pids.max"),"literal":sys.argv[2]}))
elif mode == "fork":
 children=[]
 for _ in range(64):
  try:
   pid=os.fork()
   if pid == 0: os._exit(0)
   children.append(pid)
  except OSError: break
 for pid in children: os.waitpid(pid,0)
 print(json.dumps({"created":len(children),"events":read("pids.events")}))
elif mode == "fail":
 print("failure-signal", file=sys.stderr); sys.exit(7)
'''


def _run(agent: Path, spec: Path, result: Path, cwd: Path):
    try:
        return run_bounded([sys.executable, str(agent), str(spec), str(result)], cwd=cwd, text=True, capture_output=True, timeout=20)
    except subprocess.TimeoutExpired:
        return None


def _result(path: Path):
    try:
        return result_object(path)
    except (OSError, ValueError):
        return None


def grade(workspace: Path, fixture: dict) -> list[Check]:
    source = workspace / "resource_runner.py"
    if not source.is_file():
        return [Check("A resource runner is present", False, "Module 07 lab contract")]
    with tempfile.TemporaryDirectory(prefix="north-echo-grade-07-") as raw:
        work = Path(raw)
        agent = work / "resource_runner.py"
        shutil.copy2(source, agent); agent.chmod(0o444)
        probe = work / "probe.py"; probe.write_text(PROBE)
        literal = f"literal {fixture['hostname']} $(not-a-shell)"
        spec = work / "spec.json"; result_path = work / "result.json"
        spec.write_text(json.dumps({"command":[sys.executable,str(probe),"inspect",literal],"memory_max":33554432,"tasks_max":16,"cpu_percent":50}))
        run = _run(agent, spec, result_path, work); result = _result(result_path)
        payload = None
        if isinstance(result, dict):
            try: payload = json.loads(result.get("stdout", ""))
            except json.JSONDecodeError: pass
        limits = payload == {"cpu":"50000 100000","memory":"33554432","swap":"0","pids":"16","literal":literal}

        fork_spec = work / "fork.json"; fork_result = work / "fork-result.json"
        fork_spec.write_text(json.dumps({"command":[sys.executable,str(probe),"fork"],"memory_max":33554432,"tasks_max":12,"cpu_percent":50}))
        fork_run = _run(agent, fork_spec, fork_result, work); fork_data = _result(fork_result)
        bounded = False
        if isinstance(fork_data, dict):
            try:
                observed = json.loads(fork_data.get("stdout", "")); bounded = observed["created"] < 64 and "max " in observed["events"]
            except (json.JSONDecodeError, KeyError): pass

        fail_spec = work / "fail.json"; fail_result = work / "fail-result.json"
        fail_spec.write_text(json.dumps({"command":[sys.executable,str(probe),"fail"],"memory_max":33554432,"tasks_max":16,"cpu_percent":50}))
        failed = _run(agent, fail_spec, fail_result, work); fail_data = _result(fail_result)

        bad = work / "bad.json"; bad_result = work / "bad-result.json"
        bad.write_text(json.dumps({"command":["/bin/true"],"memory_max":0,"tasks_max":100000,"cpu_percent":0}))
        denied = _run(agent, bad, bad_result, work)

        units = run_bounded(["systemctl", "--user", "list-units", "--all", "--plain", "--no-legend",
                             f"north-echo-{os.getuid()}-07-lab-*.service"])
    return [
        Check("Approved workload completes with valid result", run is not None and run.returncode == 0 and isinstance(result, dict), "Module 07 lesson 01"),
        Check("Effective CPU, memory, swap, and PID limits match", limits, "Module 07 lessons 01-03"),
        Check("Literal argv is preserved without a shell", payload is not None and payload.get("literal") == literal, "Module 04 lesson 02"),
        Check("PID pressure is bounded and recorded", fork_run is not None and bounded, "Module 07 lesson 03"),
        Check("Nonzero workload status and stderr propagate", failed is not None and isinstance(fail_data, dict) and fail_data.get("status") == 7 and "failure-signal" in fail_data.get("stderr", "") and failed.returncode != 0, "Module 07 lesson 01"),
        Check("Invalid or unbounded limits fail closed", denied is not None and denied.returncode != 0 and not bad_result.exists(), "Module 07 lab contract"),
        Check("Transient units are collected after evaluation", units.returncode == 0 and not units.stdout.strip(), "Module 07 lesson 03"),
    ]
