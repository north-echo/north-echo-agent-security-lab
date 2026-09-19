import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.northecho import cleanup
from scripts.northecho.paths import SafetyError


class CleanupPlanningTests(unittest.TestCase):
    def test_registration_rejects_symlinked_registry(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".student/07.lab").mkdir(parents=True)
            runtime = root / ".runtime/07.lab"
            runtime.mkdir(parents=True)
            external = root / "keep.json"
            external.write_text('{}')
            (runtime / "resources.json").symlink_to(external)
            with self.assertRaises(SafetyError):
                cleanup.register_user_unit(root, "07.lab", f"north-echo-{os.getuid()}-07-lab-12345678.service")
            self.assertEqual(external.read_text(), '{}')

    def test_inspection_error_is_not_an_absent_unit(self):
        with patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "offline")):
            with self.assertRaises(SafetyError):
                cleanup._user_unit_properties("synthetic.service")

    def test_explicit_absence_is_accepted(self):
        with patch.object(cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "LoadState=not-found\n", "")):
            self.assertIsNone(cleanup._user_unit_properties("synthetic.service"))

    def test_invalid_later_entry_prevents_earlier_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            runtime = root / ".runtime/01.01"
            runtime.mkdir(parents=True)
            temporary = runtime / "keep"
            temporary.mkdir()
            (runtime / "resources.json").write_text(json.dumps({
                "temp_paths": [str(temporary)], "user_units": ["unowned.service"]
            }))
            with self.assertRaises(SafetyError):
                cleanup.cleanup_target(root, "01.01")
            self.assertTrue(temporary.exists())
            self.assertTrue((runtime / "resources.json").exists())

    def test_mount_must_belong_to_specific_target(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            runtime = root / ".runtime/01.01"
            runtime.mkdir(parents=True)
            (runtime / "resources.json").write_text(json.dumps({"mounts": [str(root / ".student/01.02/mount")]}))
            with self.assertRaises(SafetyError):
                cleanup.plan_cleanup(root, "01.01")

    def test_process_timeout_retains_registry(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            runtime = root / ".runtime/01.01"
            runtime.mkdir(parents=True)
            plan = cleanup.CleanupPlan(root, "01.01", runtime, ["terminate"], [(12345, "identity")])
            with patch.object(cleanup, "_pid_identity", return_value="identity"), \
                 patch.object(os, "pidfd_open", return_value=100, create=True), \
                 patch.object(cleanup.signal, "pidfd_send_signal", create=True), \
                 patch.object(cleanup.select, "select", return_value=([], [], [])), \
                 patch.object(os, "close"):
                with self.assertRaises(SafetyError):
                    cleanup.execute_cleanup(plan)
            self.assertTrue(runtime.exists())
