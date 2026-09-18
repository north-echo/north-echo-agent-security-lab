#!/usr/bin/env python3
"""Cold starter: useful direct execution with no outer containment."""
import json, subprocess, sys
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit(2)
s=json.loads(Path(sys.argv[1]).read_text());r=subprocess.run([s["guard"],s["allowed_root"],*s["command"]],text=True,capture_output=True)
Path(sys.argv[2]).write_text(json.dumps({"schema":1,"status":r.returncode,"unit":None,"stdout":r.stdout,"stderr":r.stderr,"attestation":None})+"\n")
raise SystemExit(r.returncode!=0)
