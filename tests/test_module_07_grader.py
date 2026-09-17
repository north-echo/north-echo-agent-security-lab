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
    argv=["systemd-run","--user","--wait","--pipe","--collect","--quiet",f"--unit={unit[:-8]}",f"--property=MemoryMax={memory}","--property=MemorySwapMax=0",f"--property=TasksMax={tasks}",f"--property=CPUQuota={cpu}%","--",*command]
    try: run=subprocess.run(argv,text=True,capture_output=True,timeout=15)
    except subprocess.TimeoutExpired:
        subprocess.run(["systemctl","--user","stop",unit],check=False); return 1
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
if __name__ == "__main__": unittest.main()
