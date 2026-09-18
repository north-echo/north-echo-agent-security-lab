import json,shutil,sys,tempfile,unittest
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(SOURCE/"scripts"),str(SOURCE/"graders")]
import module_12
class Module12Tests(unittest.TestCase):
 fixture={"hostname":"grade12","canary":"GRADE-only"}
 def test_starter_fails_discovery(self):
  with tempfile.TemporaryDirectory() as raw:
   w=Path(raw);shutil.copy2(SOURCE/"course/module-12-adaptive-adversary/lab/adaptive_runner.py",w/"adaptive_runner.py");c=module_12.grade(w,self.fixture)
  self.assertFalse(all(x.passed for x in c))
 def test_reference_passes(self):
  with tempfile.TemporaryDirectory() as raw:
   w=Path(raw);shutil.copy2(SOURCE/"course/module-12-adaptive-adversary/lesson-02/adaptive_runner.py",w/"adaptive_runner.py");c=module_12.grade(w,self.fixture)
  self.assertTrue(all(x.passed for x in c),json.dumps([(x.name,x.passed) for x in c]))
