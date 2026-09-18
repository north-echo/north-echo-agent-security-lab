from pathlib import Path
import importlib.util,shutil,tempfile
from northecho.grading import Check

_spec=importlib.util.spec_from_file_location("capstone_runtime_grader",Path(__file__).with_name("module_10.py"))
_module=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_module)

def grade(workspace:Path,fixture:dict)->list[Check]:
 source=workspace/"cold_runtime.py"
 if not source.is_file(): return [Check("A cold runtime implementation is present",False,"")]
 with tempfile.TemporaryDirectory(prefix="ne-capstone-") as raw:
  proxy=Path(raw);shutil.copy2(source,proxy/"complete_runtime.py")
  checks=_module.grade(proxy,fixture)
 return [Check(item.name,item.passed,"") for item in checks]
