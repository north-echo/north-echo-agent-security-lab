from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from northecho.grading import Check

ORACLE='''import json,sys
w=sys.argv[1]; p=sys.argv[2]; allowed=["argv","credential","filesystem","network","cleanup"]
if p=="inventory": print(json.dumps({"ok":True,"surface":allowed,"next_probe":None if w=="none" else w}))
elif p in allowed: print(json.dumps({"ok":True,"probe":p,"observed":p==w,"evidence":("synthetic-"+p+"-effect") if p==w else None}))
else: sys.exit(2)
'''

def grade(workspace: Path, fixture: dict) -> list[Check]:
    source=workspace/"adaptive_runner.py"
    if not source.is_file(): return [Check("An adaptive runner is present",False,"Module 12 lab contract")]
    values={k:True for k in ("valid","budget","discover","allowed","trace","calibrated","deterministic","preserve")}
    with tempfile.TemporaryDirectory(prefix="ne12-") as raw:
        work=Path(raw); agent=work/"adaptive_runner.py"; shutil.copy2(source,agent); agent.chmod(0o444)
        oracle=work/"oracle.py"; oracle.write_text(ORACLE)
        for weakness in ("argv","credential","filesystem","network","cleanup","none"):
            spec={"oracle_command":[sys.executable,str(oracle),weakness],"budget":2,"run_id":f"{fixture['hostname']}-{weakness}"}
            sp=work/f"{weakness}.spec"; out=work/f"{weakness}.out"; sp.write_text(json.dumps(spec)); before=sp.read_bytes()
            run=subprocess.run([sys.executable,str(agent),str(sp),str(out)],text=True,capture_output=True,timeout=8)
            try: result=json.loads(out.read_text())
            except Exception: result={}
            values["valid"] &= run.returncode==0 and result.get("schema")==1
            values["budget"] &= 1 <= result.get("actions_used",99) <= 2
            probes=[x.get("probe") for x in result.get("trace",[])]
            values["allowed"] &= all(x in {"inventory","argv","credential","filesystem","network","cleanup"} for x in probes)
            values["trace"] &= probes[:1]==["inventory"] and [x.get("action") for x in result.get("trace",[])]==list(range(1,len(probes)+1))
            values["preserve"] &= sp.read_bytes()==before and result.get("run_id")==spec["run_id"]
            if weakness=="none": values["calibrated"] &= result.get("status")=="not_observed" and "not established" in result.get("claim","") and result.get("finding") is None
            else: values["discover"] &= result.get("status")=="observed" and result.get("finding",{}).get("probe")==weakness and result.get("finding",{}).get("observation",{}).get("observed") is True
            again=work/f"{weakness}.again"; subprocess.run([sys.executable,str(agent),str(sp),str(again)],timeout=8)
            values["deterministic"] &= json.loads(again.read_text())==result
    return [Check("Results are structured and preserve run identity",values["valid"] and values["preserve"],"Module 12 lesson 02"),Check("Every run respects the two-action budget",values["budget"],"Module 12 lesson 02"),Check("All randomized weakness classes are discovered",values["discover"],"Module 12 lesson 02"),Check("Only allowlisted probes are invoked",values["allowed"],"Module 12 lesson 02"),Check("Trace order and action numbers are complete",values["trace"],"Module 12 lesson 02"),Check("Non-discovery is explicitly not a security claim",values["calibrated"],"Module 12 lessons 01-03"),Check("Identical inputs produce identical results",values["deterministic"],"Module 12 lesson 03")]
