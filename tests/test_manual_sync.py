import importlib.util
from pathlib import Path
import tempfile
import unittest


class ManualSyncTests(unittest.TestCase):
    def test_source_change_is_detected_even_when_assembled_manual_is_unchanged(self):
        script = Path(__file__).resolve().parents[1] / "scripts/build_field_manual.py"
        spec = importlib.util.spec_from_file_location("manual_builder", script)
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "course").mkdir()
            (root / "course/example.py").write_text("print('new')\n")
            chapter = root / "chapter.md"
            chapter.write_text("<!-- source: course/example.py format=code -->\n```python\nprint('old')\n```\n<!-- /source -->\n")
            builder.ROOT = root
            refreshed = builder.synchronized_chapter(chapter)
            self.assertIn("print('new')", refreshed)
            self.assertNotEqual(refreshed, chapter.read_text())
