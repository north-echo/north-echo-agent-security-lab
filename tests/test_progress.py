from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import tempfile
import unittest

from scripts.northecho.state import entry, lifecycle_lock, load, record_grade, save


def increment(raw):
    root = Path(raw)
    with lifecycle_lock(root):
        progress = load(root)
        entry(progress, "01.lab")["starts"] += 1
        save(root, progress)


class ProgressTests(unittest.TestCase):
    def test_failed_regrade_keeps_achievement_and_records_failure(self):
        record = {"starts": 1, "grade_attempts": 0, "passed": False}
        record_grade(record, True, "practice", [])
        record_grade(record, False, "exam", ["synthetic property"])
        self.assertTrue(record["ever_passed"])
        self.assertEqual(record["last_result"], "failed")
        self.assertEqual(record["last_mode"], "exam")
        self.assertEqual(record["failed_properties"], ["synthetic property"])

    def test_concurrent_transactions_do_not_lose_updates(self):
        with tempfile.TemporaryDirectory() as raw:
            with ProcessPoolExecutor(max_workers=2) as pool:
                list(pool.map(increment, [raw] * 8))
            self.assertEqual(load(Path(raw))["targets"]["01.lab"]["starts"], 8)
