"""Create and verify the Windows distribution archive."""
import argparse
import hashlib
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

VERSION_PATTERN = re.compile(
    r"(?:v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:alpha|beta|rc)\.[1-9][0-9]*)?|dev-[0-9a-f]{7,40})"
)


def package_release(version, root=Path(".")):
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("Invalid archive version")
    root = Path(root)
    app = root / "dist" / "Transcribe"
    required = [
        app / "Transcribe.exe",
        root / "LICENSE",
        root / "README.md",
        root / "THIRD_PARTY_NOTICES.txt",
    ]
    for source in required:
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(f"Missing or empty distribution file: {source}")
    if not (app / "_internal").is_dir():
        raise FileNotFoundError("Missing PyInstaller runtime directory")
    licenses = root / "third_party_licenses"
    if not licenses.is_dir() or not any(p.is_file() for p in licenses.rglob("*")):
        raise FileNotFoundError("Third-party license files were not collected")
    if any(p.name.lower() in {"ffmpeg.exe", "ffprobe.exe"} for p in app.rglob("*")):
        raise ValueError("FFmpeg must not be bundled in this distribution")

    for name in ["LICENSE", "README.md", "THIRD_PARTY_NOTICES.txt"]:
        shutil.copy2(root / name, app / name)
    shutil.copytree(licenses, app / "third_party_licenses", dirs_exist_ok=True)
    freeze = subprocess.run(
        [__import__("sys").executable, "-m", "pip", "freeze"],
        check=True, capture_output=True, text=True,
    )
    (app / "BUILD_DEPENDENCIES.txt").write_text(freeze.stdout, encoding="utf-8")

    output = root / "release"
    output.mkdir(exist_ok=True)
    archive = output / f"Transcribe-{version}-win-x64.zip"
    # Keep Transcribe.exe at the archive root, matching the original release layout.
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as bundle:
        for source in sorted(app.rglob("*")):
            if source.is_file():
                bundle.write(source, source.relative_to(app).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        bad_file = bundle.testzip()
        if bad_file is not None:
            raise ValueError(f"Corrupt archive member: {bad_file}")
        for source in required:
            if source.name not in bundle.namelist():
                raise ValueError(f"Missing archive member: {source.name}")
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"Created {archive}")
    print(f"SHA-256 {digest}")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    package_release(args.version)
