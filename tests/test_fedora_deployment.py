"""Offline guards for the actual Fedora template; boot evidence is separate."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "deploy/north-echo-fedora.yaml").read_text()
USER_SCRIPT = textwrap.dedent(TEMPLATE.split("  - mode: user\n", 1)[1]
                             .split("    script: |\n", 1)[1].split("\nprobes:", 1)[0])
VERIFIER = USER_SCRIPT.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


class FedoraTemplateTests(unittest.TestCase):
    def test_safety_and_readiness_contract(self):
        for text in ("minimumLimaVersion: 2.2.0", "plain: true", "mounts: []",
                     "forwardAgent: false", "loadDotSSHPubKeys: false",
                     "file: fedora-packages.txt", 'test "$(getenforce)" = Enforcing',
                     'sudo loginctl enable-linger "$(id -un)"',
                     "55c60a3b80d3616a08705afd0459e75fe9f03c54aba7a46e4002a41a72fa0d5b",
                     "mode: readiness", './scripts/linux-preflight >/dev/null'):
            self.assertIn(text, TEMPLATE)
        for forbidden in ("setenforce 0", "apparmor_parser", "template:fedora", "arch: x86_64"):
            self.assertNotIn(forbidden, TEMPLATE)
        self.assertLess(USER_SCRIPT.index('if [[ -f "$ready_marker" ]]'),
                        USER_SCRIPT.index("curl --fail"))
        self.assertLess(USER_SCRIPT.index('if [[ -e "$course_dir" || -L "$course_dir" ]]'),
                        USER_SCRIPT.index("curl --fail"))
        self.assertLess(USER_SCRIPT.index('./scripts/linux-preflight >'),
                        USER_SCRIPT.index('mv "$ready_marker.pending" "$ready_marker"'))
        packages = (ROOT / "deploy/fedora-packages.txt").read_text().splitlines()
        self.assertEqual(len(packages), len(set(packages)))
        self.assertTrue({"glibc-static", "libseccomp-static", "libseccomp-devel",
                         "nano", "less", "man-db"}.issubset(packages))

    def test_embedded_scripts_parse(self):
        blocks = TEMPLATE.split("    script: |\n")[1:]
        for block in blocks:
            lines = []
            for line in block.splitlines():
                if line and not line.startswith("      "):
                    break
                lines.append(line[6:] if line else "")
            run = subprocess.run(["bash", "-n"], input="\n".join(lines), text=True,
                                 capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
        compile(VERIFIER, "fedora-template-verifier", "exec")

    def run_user_guard(self, guest, version="v1.0.2"):
        # Relocate the guest-home references; do not change the host's HOME.
        script = USER_SCRIPT.replace("$HOME", "${NE_TEST_GUEST_HOME}")
        env = dict(os.environ, NE_TEST_GUEST_HOME=str(guest), PARAM_CourseVersion=version)
        return subprocess.run(["bash", "-c", script], env=env, text=True,
                              capture_output=True, timeout=5)

    def test_ready_marker_skips_reinstall_and_keeps_work(self):
        with tempfile.TemporaryDirectory() as raw:
            guest = Path(raw)
            marker = guest / ".local/state/north-echo-fedora/v1.0.2.ready"
            marker.parent.mkdir(parents=True)
            marker.write_text("ready")
            work = guest / "north-echo/.student/example/note.txt"
            work.parent.mkdir(parents=True)
            work.write_text("synthetic saved work")
            self.assertEqual(self.run_user_guard(guest).returncode, 0)
            self.assertEqual(work.read_text(), "synthetic saved work")
            self.assertEqual(marker.read_text(), "ready")

    def test_incomplete_install_and_dangling_link_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as raw:
            guest = Path(raw)
            course = guest / "north-echo"
            course.mkdir()
            run = self.run_user_guard(guest)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("refusing to overwrite", run.stderr)
            self.assertEqual(list(course.iterdir()), [])
            course.rmdir()
            course.symlink_to(guest / "absent")
            run = self.run_user_guard(guest)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("refusing to overwrite", run.stderr)
            self.assertTrue(course.is_symlink())

    def test_invalid_version_stops_before_installation(self):
        with tempfile.TemporaryDirectory() as raw:
            for version in ("../other", "latest", "v1.0.2/other"):
                self.assertNotEqual(self.run_user_guard(raw, version).returncode, 0)
            self.assertEqual(list(Path(raw).iterdir()), [])

    def test_both_templates_accept_beta_marker_without_reinstalling(self):
        for name, state in (("north-echo-fedora.yaml", "north-echo-fedora"),
                            ("north-echo.yaml", "north-echo")):
            with self.subTest(template=name), tempfile.TemporaryDirectory() as raw:
                guest = Path(raw)
                version = "v2.0.0-beta.1"
                marker = guest / ".local/state" / state / (version + ".ready")
                marker.parent.mkdir(parents=True)
                marker.write_text("ready")
                content = (ROOT / "deploy" / name).read_text()
                self.assertIn("CourseVersion: " + version, content)
                script = textwrap.dedent(content.split("  - mode: user\n", 1)[1]
                    .split("    script: |\n", 1)[1].split("\nprobes:", 1)[0])
                script = script.replace("$HOME", "${NE_TEST_GUEST_HOME}")
                env = dict(os.environ, NE_TEST_GUEST_HOME=str(guest), PARAM_CourseVersion=version)
                run = subprocess.run(["bash", "-c", script], env=env, capture_output=True, timeout=5)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(marker.read_text(), "ready")

    def test_ubuntu_reuses_the_exact_archive_verifier(self):
        content = (ROOT / "deploy/north-echo.yaml").read_text()
        script = textwrap.dedent(content.split("  - mode: user\n", 1)[1]
            .split("    script: |\n", 1)[1].split("\nprobes:", 1)[0])
        self.assertEqual(script.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0], VERIFIER)
        self.assertIn('if [[ -e "$course_dir" || -L "$course_dir" ]]', script)

    def test_validation_uses_importable_runner_in_user_manager_context(self):
        for name in ("north-echo-fedora.yaml", "north-echo.yaml"):
            with self.subTest(template=name):
                content = (ROOT / "deploy" / name).read_text()
                self.assertNotIn('python3 - > "$evidence_dir/tests.txt"', content)
                self.assertIn('test -f scripts/run_tests.py', content)
                self.assertIn('systemd-run --user --wait --pipe --collect --quiet --service-type=exec', content)
                self.assertIn('--property="WorkingDirectory=$course_dir"', content)
                self.assertIn('--property=RuntimeMaxSec=600s --property=TimeoutStopSec=5s', content)
                self.assertIn('-- /usr/bin/python3 "$course_dir/scripts/run_tests.py" --require-no-skips', content)
                self.assertNotIn('setenforce 0', content)
                self.assertNotIn('runcon ', content)

    def test_empty_runtime_check_rejects_missing_paths_content_and_find_errors(self):
        begin = USER_SCRIPT.index("for managed in .student .fixtures .runtime; do")
        end = USER_SCRIPT.index("printf '%s\\n' 'EMPTY MANAGED RUNTIME: PASS'")
        code = USER_SCRIPT[begin:end]
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            def run(prefix=""):
                return subprocess.run(["bash", "-e", "-c", prefix + code], cwd=root,
                                      capture_output=True, text=True, timeout=5)
            self.assertNotEqual(run().returncode, 0)
            for name in (".student", ".fixtures", ".runtime"):
                (root / name).mkdir()
                (root / name / ".gitkeep").touch()
            self.assertEqual(run().returncode, 0)
            self.assertEqual(run("find() { return 17; };\n").returncode, 17)
            entry = root / ".runtime/uncollected"
            entry.write_text("synthetic record")
            self.assertNotEqual(run().returncode, 0)


class FedoraArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ne-fedora-archive-")
        self.staging = Path(self.temp.name)
        self.root_name = "north-echo-agent-security-lab-v1.0.2"
        self.archive = self.root_name + ".tar.gz"

    def tearDown(self):
        self.temp.cleanup()

    def bundle(self, member=None, kind=tarfile.REGTYPE):
        info = tarfile.TarInfo(member or self.root_name + "/.north-echo-root")
        info.type = kind
        info.mode = 0o644
        info.size = 2 if kind == tarfile.REGTYPE else 0
        if kind == tarfile.SYMTYPE:
            info.linkname = "../outside"
        with tarfile.open(self.staging / self.archive, "w:gz") as archive:
            archive.addfile(info, io.BytesIO(b"ok") if info.size else None)
        digest = hashlib.sha256((self.staging / self.archive).read_bytes()).hexdigest()
        return f"{digest}  {self.archive}\n"

    def verify(self, sums):
        (self.staging / "SHA256SUMS").write_text(sums)
        return subprocess.run([sys.executable, "-c", VERIFIER, str(self.staging),
                               self.archive, self.root_name], text=True,
                              capture_output=True, timeout=5)

    def test_only_selected_artifact_is_required(self):
        sums = self.bundle()
        run = self.verify(sums + "f" * 64 + "  FIELD_MANUAL.pdf\n")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual((self.staging / self.root_name / ".north-echo-root").read_text(), "ok")

    def test_missing_duplicate_malformed_and_mismatched_hash_stop_before_extract(self):
        valid = self.bundle()
        for sums in ("", valid + valid, "bad  " + self.archive + "\n",
                     "0" * 64 + "  " + self.archive + "\n",
                     valid.replace(self.archive, self.archive + ".other")):
            with self.subTest(sums=sums):
                self.assertNotEqual(self.verify(sums).returncode, 0)
                self.assertFalse((self.staging / self.root_name).exists())

    def test_wrong_root_parent_components_and_links_are_rejected(self):
        for name, kind in (("other/file", tarfile.REGTYPE),
                           (self.root_name + "/../outside", tarfile.REGTYPE),
                           (self.root_name + "/link", tarfile.SYMTYPE)):
            with self.subTest(name=name):
                self.assertNotEqual(self.verify(self.bundle(name, kind)).returncode, 0)
                self.assertFalse((self.staging / self.root_name).exists())


if __name__ == "__main__":
    unittest.main()
