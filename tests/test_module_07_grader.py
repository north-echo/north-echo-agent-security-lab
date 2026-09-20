from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "scripts")); sys.path.insert(0, str(SOURCE / "graders"))
import module_07  # noqa: E402

REFERENCE = r'''#!/usr/bin/env python3
import json, os, secrets, subprocess, sys
from pathlib import Path
def integer(value, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high: raise ValueError("limit out of range")
    return value
def main():
    if len(sys.argv) != 3: return 2
    result_path=Path(sys.argv[2]); spec=json.loads(Path(sys.argv[1]).read_text())
    command=spec.get("command")
    if not isinstance(command,list) or not command or not all(isinstance(x,str) for x in command) or not os.path.isabs(command[0]): return 2
    memory=integer(spec.get("memory_max"),16*1024*1024,256*1024*1024)
    tasks=integer(spec.get("tasks_max"),4,64); cpu=integer(spec.get("cpu_percent"),10,100)
    unit=f"north-echo-{os.getuid()}-07-lab-{secrets.token_hex(4)}.service"
    description=f"North Echo 07.lab workspace={Path.cwd().resolve()}"
    owner={"unit":unit,"description":description,"uid":os.getuid()}
    argv=["systemd-run","--user","--wait","--pipe","--collect","--quiet","--expand-environment=no",f"--unit={owner['unit']}",f"--description={owner['description']}",f"--property=MemoryMax={memory}","--property=MemorySwapMax=0",f"--property=TasksMax={tasks}",f"--property=CPUQuota={cpu}%","--property=CPUQuotaPeriodSec=100ms","--property=RuntimeMaxSec=10s","--property=TimeoutStopSec=1s","--",*command]
    try: run=subprocess.run(argv,text=True,capture_output=True,timeout=15)
    except subprocess.TimeoutExpired:
        inspected=subprocess.run(["systemctl","--user","show",unit,"--property=LoadState","--property=Description","--property=ControlGroup"],text=True,capture_output=True,timeout=5)
        properties=dict(line.split("=",1) for line in inspected.stdout.splitlines() if "=" in line)
        if properties.get("LoadState") == "not-found": return 1
        group=properties.get("ControlGroup","")
        if inspected.returncode or properties.get("Description") != owner["description"] or not group.startswith(f"/user.slice/user-{owner['uid']}.slice/user@{owner['uid']}.service/") or not group.endswith("/"+unit):
            raise RuntimeError("unit ownership could not be established")
        subprocess.run(["systemctl","--user","stop",unit],check=True,timeout=5)
        return 1
    result_path.write_text(json.dumps({"status":run.returncode,"stdout":run.stdout,"stderr":run.stderr})+"\n")
    return 0 if run.returncode == 0 else 1
if __name__ == "__main__": raise SystemExit(main())
'''

def systemd_user_available():
    return subprocess.run(["systemctl","--user","show-environment"], capture_output=True).returncode == 0

@unittest.skipUnless(sys.platform.startswith("linux") and systemd_user_available(), "requires delegated systemd user manager")
class Module07GraderTests(unittest.TestCase):
    fixture={"hostname":"grade-07-test","canary":"GRADE-test"}
    def test_starter_fails_effective_limits(self):
        with tempfile.TemporaryDirectory() as raw:
            w=Path(raw); shutil.copy2(SOURCE/"course/module-07-cgroups/lab/resource_runner.py",w/"resource_runner.py")
            checks=module_07.grade(w,self.fixture)
        self.assertFalse(all(c.passed for c in checks))
    def test_reference_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            w=Path(raw); (w/"resource_runner.py").write_text(REFERENCE)
            checks=module_07.grade(w,self.fixture)
        self.assertTrue(all(c.passed for c in checks),json.dumps([(c.name,c.passed) for c in checks]))

    def test_default_manager_expansion_does_not_preserve_literal_argv(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            source = REFERENCE.replace('"--expand-environment=no",', '')
            (workspace / "resource_runner.py").write_text(source)
            checks = module_07.grade(workspace, self.fixture)
        literal = next(check for check in checks if check.name == "Literal argv is preserved without a shell")
        self.assertFalse(literal.passed)
if __name__ == "__main__": unittest.main()
