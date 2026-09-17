from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from scripts.northecho.cleanup import (
    expected_user_unit_description,
    validate_user_unit_name,
    validate_user_unit_state,
)
from scripts.northecho.paths import SafetyError


class DelegatedUserUnitCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="north-echo-unit-test-")
        self.root = Path(self.temporary.name) / "repo"
        (self.root / ".student" / "07.01").mkdir(parents=True)
        self.uid = os.getuid()
        self.unit = f"north-echo-{self.uid}-07-01-a1b2c3d4.service"

    def tearDown(self):
        self.temporary.cleanup()

    def properties(self) -> dict[str, str]:
        return {
            "LoadState": "loaded",
            "Description": expected_user_unit_description(self.root, "07.01"),
            "ControlGroup": (
                f"/user.slice/user-{self.uid}.slice/user@{self.uid}.service/"
                f"app.slice/{self.unit}"
            ),
        }

    def test_accepts_exact_owned_name_description_and_delegated_cgroup(self):
        unit = validate_user_unit_name("07.01", self.uid, self.unit)
        control_group = validate_user_unit_state(self.root, "07.01", self.uid, unit, self.properties())
        self.assertTrue(control_group.endswith("/" + self.unit))

    def test_rejects_unrelated_or_ambiguous_unit_names(self):
        for value in (
            "ssh.service",
            f"north-echo-{self.uid}-07-02-a1b2c3d4.service",
            f"north-echo-{self.uid}-07-01-short.service",
            f"north-echo-{self.uid}-07-01-a1b2c3d4.service/../ssh.service",
            17,
        ):
            with self.subTest(value=value):
                with self.assertRaises(SafetyError):
                    validate_user_unit_name("07.01", self.uid, value)

    def test_rejects_forged_description(self):
        properties = self.properties()
        properties["Description"] = "North Echo 07.01 workspace=/tmp/other"
        with self.assertRaises(SafetyError):
            validate_user_unit_state(self.root, "07.01", self.uid, self.unit, properties)

    def test_rejects_cgroup_outside_delegated_user_manager(self):
        properties = self.properties()
        properties["ControlGroup"] = f"/system.slice/{self.unit}"
        with self.assertRaises(SafetyError):
            validate_user_unit_state(self.root, "07.01", self.uid, self.unit, properties)


if __name__ == "__main__":
    unittest.main()
