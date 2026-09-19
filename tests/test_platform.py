from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="north-echo-test-")
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE, self.root, ignore=shutil.ignore_patterns(".student", ".fixtures", ".runtime", ".state", "__pycache__", "*.pyc"))
        for name in (".student", ".fixtures", ".runtime", ".state"):
            (self.root / name).mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, command: str, *args: str, expected: int = 0):
        run = subprocess.run(
            [sys.executable, str(self.root / "scripts" / "labctl.py"), command, *args],
            cwd=self.root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        return run

    def test_replay_rotates_fixture_and_preserves_only_metadata(self):
        self.run_cli("start", "01.01")
        first = json.loads((self.root / ".student" / "01.01" / ".north-echo.json").read_text())
        solution = self.root / ".student" / "01.01" / "my-solution.txt"
        solution.write_text("student work")
        self.run_cli("reset", "01.01", "--yes")
        self.assertFalse(solution.exists())
        self.run_cli("start", "01.01")
        second = json.loads((self.root / ".student" / "01.01" / ".north-echo.json").read_text())
        self.assertNotEqual(first["fixture_id"], second["fixture_id"])
        progress = json.loads((self.root / ".state" / "progress.json").read_text())
        self.assertEqual(progress["targets"]["01.01"]["starts"], 2)
        self.assertEqual(progress["targets"]["01.01"]["resets"], 1)
        self.assertNotIn("student work", json.dumps(progress))

    def test_module_scope_and_dry_run(self):
        self.run_cli("start", "01.01")
        self.run_cli("start", "01.02")
        dry = self.run_cli("reset", "module-01", "--dry-run")
        self.assertIn("DRY RUN", dry.stdout)
        self.assertTrue((self.root / ".student" / "01.01").exists())
        self.run_cli("reset", "module-01", "--yes")
        self.assertFalse((self.root / ".student" / "01.01").exists())
        self.assertFalse((self.root / ".student" / "01.02").exists())

    def test_canonical_change_blocks_start(self):
        lesson = self.root / "course" / "module-01-process-authority" / "lesson-01" / "README.md"
        lesson.write_text(lesson.read_text() + "\nchanged\n")
        run = self.run_cli("start", "01.01", expected=2)
        self.assertIn("changed canonical file", run.stderr)

    def test_symlink_escape_is_rejected(self):
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep")
        os.symlink(outside, self.root / ".student" / "01.01")
        run = self.run_cli("reset", "01.01", "--yes", expected=2)
        self.assertIn("outside lab root", run.stderr)
        self.assertEqual((outside / "keep.txt").read_text(), "keep")

    def test_starter_module_one_fails_security_properties(self):
        self.run_cli("start", "module-01")
        run = self.run_cli("grade", "module-01", expected=1)
        self.assertIn("RESULT: NOT PASSED", run.stdout)
        self.assertTrue(
            "environment authority" in run.stdout or "launcher builds cleanly" in run.stdout,
            run.stdout,
        )

    def test_module_four_starter_fails_then_reference_runner_passes(self):
        self.run_cli("start", "module-04")
        starter = self.run_cli("grade", "module-04", expected=1)
        self.assertIn("RESULT: NOT PASSED", starter.stdout)

        source = self.root / ".student" / "04.lab" / "agent.py"
        source.write_text(
            '''#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

def field_result(action):
    tool = action["tool"]
    if tool == "read_file":
        return {"content": Path(action["path"]).read_text(encoding="utf-8")}
    if tool == "write_file":
        content = action["content"]
        Path(action["path"]).write_text(content, encoding="utf-8")
        return {"bytes_written": len(content.encode())}
    if tool == "run_argv":
        run = subprocess.run(action["argv"], shell=False, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}, text=True, capture_output=True, check=False)
        return {"status": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    raise ValueError("unknown tool")

def main():
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    failed = False
    with Path(sys.argv[2]).open("w", encoding="utf-8") as trace:
        for action in task["actions"]:
            record = {"id": action["id"], "tool": action["tool"]}
            try:
                result = field_result(action)
                ok = result.get("status", 0) == 0
                record.update({"ok": ok, "result": result})
            except Exception as error:
                record.update({"ok": False, "error": str(error)})
            failed = failed or not record["ok"]
            trace.write(json.dumps(record, sort_keys=True) + "\\n")
            trace.flush()
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
''',
            encoding="utf-8",
        )
        passed = self.run_cli("grade", "module-04")
        self.assertIn("RESULT: PASSED", passed.stdout)
        self.run_cli("reset", "module-04", "--yes")
        self.assertFalse((self.root / ".student" / "04.lab").exists())

    def test_status_and_scaffold_messages(self):
        status = self.run_cli("status")
        self.assertIn("01.01", status.stdout)
        self.assertIn("Linux openat2 + Landlock ABI", status.stdout)
        self.assertIn("Linux seccomp filter mode", status.stdout)
        self.assertIn("delegated systemd user manager", status.stdout)
        self.assertIn("network namespaces and filesystem Unix sockets", status.stdout)
        self.assertIn("fake credentials only", status.stdout)
        self.assertIn("10.03", status.stdout)
        self.assertIn("static C toolchain", status.stdout)
        self.assertIn("11.03", status.stdout)
        self.assertIn("12.03", status.stdout)
        capstone = self.run_cli("start", "capstone", "--cold")
        self.assertIn("START capstone", capstone.stdout)
        self.assertTrue((self.root / ".student/capstone/cold_runtime.py").is_file())
        self.assertFalse((self.root / ".student/capstone" / "solution.py").exists())
        self.run_cli("reset", "capstone", "--yes")

    def test_cleanup_registry_dry_run_and_removal(self):
        runtime = self.root / ".runtime" / "01.01"
        temporary = runtime / "owned-temp"
        temporary.mkdir(parents=True)
        (temporary / "marker").write_text("synthetic")
        (runtime / "resources.json").write_text(json.dumps({"temp_paths": [str(temporary)]}))
        dry = self.run_cli("cleanup", "01.01", "--dry-run")
        self.assertIn("remove temp", dry.stdout)
        self.assertTrue(temporary.exists())
        self.run_cli("cleanup", "01.01")
        self.assertFalse(runtime.exists())

    def test_cleanup_registry_rejects_external_path(self):
        outside = Path(self.temporary.name) / "outside-cleanup"
        outside.mkdir()
        marker = outside / "keep"
        marker.write_text("keep")
        runtime = self.root / ".runtime" / "01.01"
        runtime.mkdir(parents=True)
        (runtime / "resources.json").write_text(json.dumps({"temp_paths": [str(outside)]}))
        run = self.run_cli("cleanup", "01.01", expected=2)
        self.assertIn("outside lab root", run.stderr)
        self.assertEqual(marker.read_text(), "keep")

    def test_user_unit_registration_is_scoped_to_active_target(self):
        self.run_cli("start", "06.01")
        unit = f"north-echo-{os.getuid()}-06-01-a1b2c3d4.service"
        registered = self.run_cli("register-unit", "06.01", unit)
        self.assertIn(unit, registered.stdout)
        registry = json.loads((self.root / ".runtime/06.01/resources.json").read_text())
        self.assertEqual(registry["user_units"], [unit])
        rejected = self.run_cli("register-unit", "06.01", "ssh.service", expected=2)
        self.assertIn("refusing unrelated user unit", rejected.stderr)

    def test_reset_preserves_pass_metadata(self):
        self.run_cli("start", "01.01")
        progress_path = self.root / ".state" / "progress.json"
        progress = json.loads(progress_path.read_text())
        progress["targets"]["01.01"]["passed"] = True
        progress_path.write_text(json.dumps(progress))
        self.run_cli("reset", "01.01", "--yes")
        preserved = json.loads(progress_path.read_text())
        self.assertTrue(preserved["targets"]["01.01"]["passed"])

    def test_exam_mode_withholds_lesson_references(self):
        self.run_cli("start", "module-01", "--mode", "exam")
        run = self.run_cli("grade", "module-01", expected=1)
        self.assertIn("EXAM MODE", run.stdout)
        self.assertNotIn("Review:", run.stdout)

    def test_every_guided_lesson_has_local_line_explanations(self):
        lessons = sorted((SOURCE / "course").glob("module-*/lesson-*/README.md"))
        self.assertEqual(len(lessons), 36)
        for lesson in lessons:
            text = lesson.read_text(encoding="utf-8")
            self.assertIn("### Line by line", text, str(lesson))

    def test_field_manual_is_self_contained_and_substantial(self):
        manual = (SOURCE / "docs" / "MANUAL_MODULES_01_03.md").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(manual.split()), 8000)
        for phrase in (
            "Reading command and code blocks",
            "Complete source:",
            "Troubleshooting and checkpoint",
            "Module 01 independent practical",
            "Module 02 independent practical",
            "Module 03 independent practical",
            "Integrated understanding",
            "Glossary",
        ):
            self.assertIn(phrase, manual)

        module_four = (SOURCE / "docs" / "MANUAL_MODULE_04.md").read_text(encoding="utf-8")
        for phrase in (
            "Run a deterministic tool loop and record every action",
            "Preserve argv boundaries and handle tool failure",
            "Inventory and remove ambient launcher authority",
            "Module 04 independent lab",
        ):
            self.assertIn(phrase, module_four)

        module_five = (SOURCE / "docs" / "MANUAL_MODULE_05.md").read_text(encoding="utf-8")
        for phrase in (
            "Break pathname string checks",
            "Make lookup descriptor-relative with `openat2`",
            "Restrict a child with Landlock",
            "Unhandled means allowed",
            "Module 05 independent lab",
        ):
            self.assertIn(phrase, module_five)

        module_six = (SOURCE / "docs" / "MANUAL_MODULE_06.md").read_text(encoding="utf-8")
        for phrase in (
            "Measure the workload before filtering",
            "Compare errno, kill, and blacklist bypass",
            "Launch with a native default-deny filter",
            "Module 06 independent lab",
        ):
            self.assertIn(phrase, module_six)

        module_seven = (SOURCE / "docs" / "MANUAL_MODULE_07.md").read_text(encoding="utf-8")
        for phrase in ("Observe an effective CPU quota", "Bound memory and observe OOM", "Bound process-tree growth", "Module 07 independent lab"):
            self.assertIn(phrase, module_seven)

        module_eight = (SOURCE / "docs" / "MANUAL_MODULE_08.md").read_text(encoding="utf-8")
        for phrase in ("Remove the inherited IP network", "Reach one service through a Unix-socket broker", "Reauthorize names, ports, redirects, and runs", "Module 08 independent lab"):
            self.assertIn(phrase, module_eight)

        module_nine = (SOURCE / "docs" / "MANUAL_MODULE_09.md").read_text(encoding="utf-8")
        for phrase in ("Remove ambient credential authority", "Bind a signed operation capability", "Deny replay and confused-deputy substitution", "Module 09 independent lab"):
            self.assertIn(phrase, module_nine)

        module_ten = (SOURCE / "docs" / "MANUAL_MODULE_10.md").read_text(encoding="utf-8")
        for phrase in ("Order the complete runtime by dependency", "Seal filesystem and syscall policy before exec", "Launch, attest, and collect the complete runtime", "Module 10 independent lab"):
            self.assertIn(phrase, module_ten)

        module_eleven = (SOURCE / "docs" / "MANUAL_MODULE_11.md").read_text(encoding="utf-8")
        for phrase in ("Reproduce a seeded weakness without an agent", "Identify invariants from an evidence matrix", "Repair and prove the hardened counterpart", "Module 11 independent lab"):
            self.assertIn(phrase, module_eleven)

        module_twelve = (SOURCE / "docs" / "MANUAL_MODULE_12.md").read_text(encoding="utf-8")
        for phrase in ("Establish a scripted baseline", "Adapt within an action budget", "Package a calibrated candidate experiment", "Module 12 independent lab"):
            self.assertIn(phrase, module_twelve)

    def test_landlock_lesson_tracks_known_filesystem_abi_rights(self):
        source = (SOURCE / "course" / "module-05-filesystem-landlock" / "lesson-03" / "landlock_launch.c").read_text(encoding="utf-8")
        lesson = (SOURCE / "course" / "module-05-filesystem-landlock" / "lesson-03" / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "LANDLOCK_ACCESS_FS_REFER",
            "LANDLOCK_ACCESS_FS_TRUNCATE",
            "LANDLOCK_ACCESS_FS_IOCTL_DEV",
            "LANDLOCK_ACCESS_FS_RESOLVE_UNIX",
            'fprintf(stderr, "Landlock ABI %d\\n", abi);',
        ):
            self.assertIn(phrase, source)
        self.assertIn("Unhandled means allowed", lesson)
        self.assertIn("build headers", lesson)

    def test_lima_appliance_is_pinned_idempotent_and_fail_closed(self):
        template = (SOURCE / "deploy" / "north-echo.yaml").read_text(encoding="utf-8")
        packages = (SOURCE / "deploy" / "ubuntu-packages.txt").read_text(encoding="utf-8").splitlines()
        workflow = (SOURCE / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertEqual(
            packages,
            [
                "apparmor",
                "build-essential",
                "ca-certificates",
                "curl",
                "iproute2",
                "libcap2-bin",
                "libseccomp-dev",
                "linux-libc-dev",
                "pkg-config",
                "procps",
                "python3",
                "strace",
                "util-linux",
            ],
        )
        self.assertIn("xargs sudo apt-get install -y < deploy/ubuntu-packages.txt", workflow)
        for phrase in (
            "minimumLimaVersion: 2.2.0",
            "release-20260911/ubuntu-24.04-server-cloudimg-amd64.img",
            "sha256:612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354",
            "release-20260911/ubuntu-24.04-server-cloudimg-arm64.img",
            "sha256:7b682958a67ff5de068e36de6af8b75fa645d296af5a70d6500527f6a33781db",
            "plain: true",
            "forwardAgent: false",
            "file: ubuntu-packages.txt",
            'sudo loginctl enable-linger "$(id -un)"',
            'if [[ -f "$ready_marker" ]]',
            "refusing to overwrite",
            'grep -F "  $archive"',
            "mode: readiness",
        ):
            self.assertIn(phrase, template)
        self.assertNotIn("template:ubuntu-24.04", template)
        self.assertLess(template.index('if [[ -f "$ready_marker" ]]'), template.index("apt-get update"))
        self.assertLess(template.rindex('if [[ -f "$ready_marker" ]]'), template.index('curl --fail'))

    def test_handoff_contract_is_present_and_explicit(self):
        agents = (SOURCE / "AGENTS.md").read_text(encoding="utf-8")
        handoff = (SOURCE / "docs" / "dev" / "HANDOFF.md").read_text(encoding="utf-8")
        acceptance = (SOURCE / "docs" / "dev" / "MODULE_ACCEPTANCE_TEMPLATE.md").read_text(encoding="utf-8")
        validation = (SOURCE / "docs" / "LINUX_VALIDATION.md").read_text(encoding="utf-8")
        for phrase in (
            "Never cut corners on the field manual",
            "AI is an optional tutor or debugger",
            "Cleanup is fail-closed",
        ):
            self.assertIn(phrase, agents)
        self.assertIn("Linux baseline for Modules 01-03", handoff)
        self.assertIn("Modules 04-06", handoff)
        self.assertIn("Modules 07-09", handoff)
        self.assertIn("Modules 10-12", handoff)
        self.assertIn("Every meaningful line", acceptance)
        self.assertIn("Gate 5: reset scopes and cleanup containment", validation)
        self.assertTrue(os.access(SOURCE / "scripts" / "linux-preflight", os.X_OK))


class LinuxLessonRegressionTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
    def test_module_03_capability_floor_works_after_map_root_user(self):
        probe = subprocess.run(
            ["unshare", "--user", "--map-root-user", "true"],
            text=True,
            capture_output=True,
        )
        if probe.returncode != 0:
            self.skipTest("unprivileged user namespaces are unavailable")

        run = subprocess.run(
            [
                "unshare",
                "--user",
                "--map-root-user",
                "setpriv",
                "--bounding-set=-all",
                "--inh-caps=-all",
                "--ambient-caps=-all",
                "sh",
                "-c",
                'grep -E "^Cap(Inh|Prm|Eff|Bnd|Amb):" /proc/self/status',
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        fields = dict(line.split(":", 1) for line in run.stdout.splitlines())
        self.assertEqual(
            fields,
            {
                "CapInh": "\t0000000000000000",
                "CapPrm": "\t0000000000000000",
                "CapEff": "\t0000000000000000",
                "CapBnd": "\t0000000000000000",
                "CapAmb": "\t0000000000000000",
            },
        )


if __name__ == "__main__":
    unittest.main()
