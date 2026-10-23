"""Release packaging regression tests; no build dependencies required."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "package_release", ROOT / "scripts" / "package_release.py"
)
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        app = self.root / "dist" / "Transcribe"
        (app / "_internal").mkdir(parents=True)
        (app / "Transcribe.exe").write_bytes(b"test executable")
        (app / "_internal" / "runtime.dll").write_bytes(b"test runtime")
        for name in ["LICENSE", "README.md", "THIRD_PARTY_NOTICES.txt"]:
            (self.root / name).write_text(name, encoding="utf-8")
        licenses = self.root / "third_party_licenses" / "test-package"
        licenses.mkdir(parents=True)
        (licenses / "LICENSE").write_text("third-party license", encoding="utf-8")

    def test_archive_contains_runtime_licenses_and_checksum(self):
        with patch.object(package.subprocess, "run",
                          return_value=types.SimpleNamespace(stdout="test==1.0\n")):
            archive = package.package_release("v1.1.0", self.root)
        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())
            self.assertTrue({
                "Transcribe.exe", "_internal/runtime.dll", "LICENSE", "README.md",
                "THIRD_PARTY_NOTICES.txt", "third_party_licenses/test-package/LICENSE",
                "BUILD_DEPENDENCIES.txt",
            }.issubset(names))
            self.assertIsNone(bundle.testzip())
        expected = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.assertEqual(archive.with_suffix(".zip.sha256").read_text().strip(),
                         f"{expected}  {archive.name}")

    def test_rejects_missing_license(self):
        (self.root / "LICENSE").unlink()
        with self.assertRaises(FileNotFoundError):
            package.package_release("v1.1.0", self.root)
        self.assertFalse((self.root / "release").exists())

    def test_rejects_empty_third_party_licenses(self):
        (self.root / "third_party_licenses" / "test-package" / "LICENSE").unlink()
        with self.assertRaises(FileNotFoundError):
            package.package_release("v1.1.0", self.root)

    def test_rejects_bundled_ffmpeg(self):
        (self.root / "dist" / "Transcribe" / "ffmpeg.exe").write_bytes(b"ffmpeg")
        with self.assertRaisesRegex(ValueError, "FFmpeg"):
            package.package_release("v1.1.0", self.root)

    def test_version_validation(self):
        for version in ["v1.2.3", "v1.2.3-rc.1", "v1.2.3-beta.2", "dev-abcdef0"]:
            self.assertIsNotNone(package.VERSION_PATTERN.fullmatch(version))
        for version in ["../bad", "v1.2", "v01.2.3", "v1.2.3;cmd", "v1.2.3-rc.0"]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                package.package_release(version, self.root)


if __name__ == "__main__":
    unittest.main()
