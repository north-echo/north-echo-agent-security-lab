import json,shutil,sys,tempfile,unittest
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(SOURCE/"scripts"),str(SOURCE/"graders")]
import capstone
class CapstoneTests(unittest.TestCase):
 @unittest.skipUnless(sys.platform.startswith("linux"),"requires Linux containment")
 def test_starter_fails_and_reference_passes(self):
  fixture={"hostname":"cold-test","canary":"COLD-only"}
  with tempfile.TemporaryDirectory() as raw:
   w=Path(raw);shutil.copy2(SOURCE/"course/capstone/lab/cold_runtime.py",w/"cold_runtime.py");self.assertFalse(all(x.passed for x in capstone.grade(w,fixture)))
   shutil.copy2(SOURCE/"course/module-10-complete-runtime/lesson-03/complete_runtime.py",w/"cold_runtime.py");checks=capstone.grade(w,fixture)
  self.assertTrue(all(x.passed for x in checks),json.dumps([(x.name,x.passed) for x in checks]))
