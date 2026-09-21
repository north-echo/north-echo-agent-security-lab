"""License distribution regressions; these do not establish legal provenance."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def builder():
    spec = importlib.util.spec_from_file_location(
        "licensed_manual_builder", ROOT / "scripts/build_field_manual.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LicensingTests(unittest.TestCase):
    def test_license_texts_match_reviewed_sources(self):
        # Upstream plain texts fetched 2026-09-20, plus the original MIT notice:
        # https://www.apache.org/licenses/LICENSE-2.0.txt
        # https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt
        expected = {
            "LICENSE": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
            "LICENSES/CC-BY-SA-4.0.txt": "23ee78c8bae49cf08ea2f0c84945c66b987ebe4520881fb51b3dad4fb43d07c2",
            "LICENSES/MIT.txt": "433637ed0e5f68e011c8d24eb9b46c564d2c7076d59d051298894dee28cd8d47",
        }
        for relative, digest in expected.items():
            with self.subTest(relative=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)

    def test_standalone_manual_retains_full_notices_and_scope(self):
        rendered = builder().render()
        self.assertEqual(rendered, (ROOT / "docs/FIELD_MANUAL.md").read_text())
        for relative in ("LICENSE", "NOTICE", "LICENSES/CC-BY-SA-4.0.txt", "LICENSES/MIT.txt"):
            with self.subTest(relative=relative):
                self.assertIn((ROOT / relative).read_text().rstrip(), rendered)
        self.assertIn("### Embedded-code exception", rendered)
        self.assertIn("does not revoke MIT permissions", rendered)
        self.assertIn("[LICENSE](../LICENSE)", rendered)
        self.assertIn("[CONTRIBUTING.md](../CONTRIBUTING.md)", rendered)

    def test_missing_license_fails_manual_generation(self):
        module = builder()
        with tempfile.TemporaryDirectory() as raw:
            module.ROOT = Path(raw)
            (module.ROOT / "LICENSING.md").write_text("# Licensing\n")
            with self.assertRaises(FileNotFoundError):
                module.licensing_appendix()

    def test_license_change_is_reflected_without_changing_course(self):
        module = builder()
        with tempfile.TemporaryDirectory() as raw:
            module.ROOT = Path(raw)
            (module.ROOT / "LICENSES").mkdir()
            for relative in ("LICENSING.md", "LICENSE", "NOTICE",
                             "LICENSES/CC-BY-SA-4.0.txt", "LICENSES/MIT.txt"):
                (module.ROOT / relative).write_text((ROOT / relative).read_text())
            previous = module.licensing_appendix()
            (module.ROOT / "NOTICE").write_text("Synthetic attribution update.\n")
            current = module.licensing_appendix()
            self.assertNotEqual(previous, current)
            self.assertIn("Synthetic attribution update.", current)
