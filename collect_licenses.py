"""Transcribe配布用の第三者ライセンス情報を収集する。"""

import importlib.metadata as metadata
import platform
import re
import shutil
import sys
from collections import deque
from pathlib import Path

from packaging.requirements import (
    InvalidRequirement,
    Requirement,
)


# ==========================================
# ライセンス収集の起点
# ==========================================

# Transcribeの実行時依存関係
ROOT_PACKAGES = (
    "openai-whisper",
)

# PyInstallerによる配布物に実際に含まれていることを
# 確認したパッケージ。
#
# setuptoolsはdist/Transcribe/_internal/setuptools
# として含まれているため、明示的に収集する。
ADDITIONAL_PACKAGES = (
    "setuptools",
)


# ==========================================
# 出力
# ==========================================

OUTPUT_DIRECTORY = Path(
    "third_party_licenses"
)

SUMMARY_PATH = Path(
    "THIRD_PARTY_NOTICES.txt"
)


# ==========================================
# ライセンスファイル名
# ==========================================

LICENSE_PREFIXES = (
    "license",
    "licence",
    "copying",
    "notice",
    "copyright",
)


def normalize_package_name(
    name,
):
    """
    Python package名を比較用に正規化する。
    """

    return re.sub(
        r"[-_.]+",
        "-",
        name,
    ).lower()


def get_active_dependency_name(
    requirement_text,
):
    """
    Requires-Distの1行を解析し、
    現在の実行環境で有効な依存関係だけ返す。

    extra == "test" や
    extra == "dev" などの追加依存は除外する。

    Windows / Pythonバージョンなどの
    environment markerも評価する。

    Returns:
        str | None:
            有効な依存package名。
            対象外ならNone。
    """

    try:
        requirement = Requirement(
            requirement_text
        )

    except InvalidRequirement:
        return None

    marker = requirement.marker

    if marker is not None:
        try:
            is_active = marker.evaluate(
                {
                    # extra依存を有効化しない
                    "extra": "",
                }
            )

        except Exception:
            return None

        if not is_active:
            return None

    return requirement.name


def get_runtime_distributions():
    """
    実行時に必要なPython Distributionを取得する。

    openai-whisperから依存関係を再帰的にたどる。

    test / dev / docsなどのextra依存は除外する。

    また、PyInstaller配布物に実際に含まれている
    setuptoolsなどはADDITIONAL_PACKAGESから追加する。
    """

    queue = deque(
        ROOT_PACKAGES
        + ADDITIONAL_PACKAGES
    )

    distributions = {}

    while queue:
        package_name = (
            queue.popleft()
        )

        normalized_name = (
            normalize_package_name(
                package_name
            )
        )

        if (
            normalized_name
            in distributions
        ):
            continue

        try:
            distribution = (
                metadata.distribution(
                    package_name
                )
            )

        except (
            metadata.PackageNotFoundError
        ):
            print(
                "Warning: "
                f"{package_name} "
                "is not installed."
            )

            continue

        actual_name = (
            distribution.metadata.get(
                "Name"
            )
            or package_name
        )

        actual_normalized_name = (
            normalize_package_name(
                actual_name
            )
        )

        distributions[
            actual_normalized_name
        ] = distribution

        # ==================================
        # 実行時依存を再帰的に追加
        # ==================================

        for requirement_text in (
            distribution.requires
            or []
        ):
            dependency_name = (
                get_active_dependency_name(
                    requirement_text
                )
            )

            if dependency_name is None:
                continue

            dependency_normalized_name = (
                normalize_package_name(
                    dependency_name
                )
            )

            if (
                dependency_normalized_name
                in distributions
            ):
                continue

            try:
                metadata.distribution(
                    dependency_name
                )

            except (
                metadata.PackageNotFoundError
            ):
                # OSや環境によって
                # インストールされていない依存は無視する。
                continue

            queue.append(
                dependency_name
            )

    return sorted(
        distributions.values(),
        key=lambda distribution: (
            distribution.metadata.get(
                "Name",
                "",
            ).lower()
        ),
    )


def is_license_file(
    file_path,
):
    """
    LICENSE / COPYING / NOTICE系ファイルか判定する。
    """

    filename = (
        Path(
            str(file_path)
        )
        .name
        .lower()
    )

    return any(
        filename.startswith(
            prefix
        )
        for prefix
        in LICENSE_PREFIXES
    )


def safe_directory_name(
    text,
):
    """
    package名・versionを
    Windowsで安全なディレクトリ名へ変換する。
    """

    return re.sub(
        r'[^A-Za-z0-9._+-]',
        "_",
        text,
    )


def copy_distribution_licenses(
    distribution,
):
    """
    1つのDistributionに含まれる
    LICENSE / NOTICE / COPYING等を
    third_party_licensesへコピーする。

    package内部に含まれるvendored libraryの
    LICENSEも対象になる。
    """

    package_name = (
        distribution.metadata.get(
            "Name"
        )
        or "unknown"
    )

    version = (
        distribution.version
        or "unknown"
    )

    destination_root = (
        OUTPUT_DIRECTORY
        / safe_directory_name(
            f"{package_name}-{version}"
        )
    )

    copied_count = 0

    for file_entry in (
        distribution.files
        or []
    ):
        if not is_license_file(
            file_entry
        ):
            continue

        source = Path(
            distribution.locate_file(
                file_entry
            )
        )

        if not source.is_file():
            continue

        relative_path = Path(
            str(file_entry)
        )

        # 念のため危険なパスを除外
        if (
            relative_path.is_absolute()
            or ".."
            in relative_path.parts
        ):
            continue

        destination = (
            destination_root
            / relative_path
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        copied_count += 1

    return copied_count


def copy_python_license():
    """
    PyInstallerにより同梱される
    Python Runtimeのライセンスを保存する。
    """

    python_version = (
        platform.python_version()
    )

    destination_root = (
        OUTPUT_DIRECTORY
        / f"Python-{python_version}"
    )

    candidates = (
        Path(
            sys.base_prefix
        )
        / "LICENSE.txt",
        Path(
            sys.base_prefix
        )
        / "LICENSE",
    )

    for source in candidates:
        if not source.is_file():
            continue

        destination_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination_root
            / source.name,
        )

        return True

    return False


def copy_tcl_tk_licenses():
    """
    Tkinterで使用されるTcl/Tkの
    license.termsを収集する。
    """

    tcl_root = (
        Path(
            sys.base_prefix
        )
        / "tcl"
    )

    if not tcl_root.is_dir():
        return 0

    destination_root = (
        OUTPUT_DIRECTORY
        / "Tcl-Tk"
    )

    copied_count = 0

    for source in (
        tcl_root.rglob(
            "license.terms"
        )
    ):
        relative_path = (
            source.relative_to(
                tcl_root
            )
        )

        destination = (
            destination_root
            / relative_path
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        copied_count += 1

    return copied_count


def get_license_description(
    distribution,
):
    """
    package metadataから
    短いライセンス表記を取得する。
    """

    expression = (
        distribution.metadata.get(
            "License-Expression"
        )
    )

    if expression:
        return expression.strip()

    license_text = (
        distribution.metadata.get(
            "License"
        )
    )

    if not license_text:
        return (
            "See bundled license files"
        )

    license_text = (
        license_text.strip()
    )

    # Licenseフィールド自体に
    # ライセンス全文が入っているpackageもある。
    if (
        "\n"
        in license_text
        or len(
            license_text
        )
        > 160
    ):
        return (
            "See bundled license files"
        )

    return license_text


def get_project_information(
    distribution,
):
    """
    package metadataから
    Project URL等を取得する。
    """

    result = []

    home_page = (
        distribution.metadata.get(
            "Home-page"
        )
    )

    if home_page:
        result.append(
            (
                "Project",
                home_page,
            )
        )

    project_urls = (
        distribution.metadata.get_all(
            "Project-URL"
        )
        or []
    )

    for project_url in (
        project_urls
    ):
        result.append(
            (
                "Project URL",
                project_url,
            )
        )

    return result


def write_summary(
    distributions,
):
    """
    THIRD_PARTY_NOTICES.txtを生成する。
    """

    lines = [
        "Transcribe - Third-Party Notices",
        "=================================",
        "",
        (
            "This application includes or depends on "
            "third-party software."
        ),
        (
            "The corresponding license and notice files "
            "collected from the build environment are "
            "stored in the third_party_licenses directory."
        ),
        "",
        "Python runtime dependencies",
        "---------------------------",
        "",
    ]

    for distribution in distributions:
        name = (
            distribution.metadata.get(
                "Name"
            )
            or "unknown"
        )

        version = (
            distribution.version
            or "unknown"
        )

        license_description = (
            get_license_description(
                distribution
            )
        )

        lines.append(
            f"{name} {version}"
        )

        lines.append(
            "License: "
            f"{license_description}"
        )

        for (
            label,
            url,
        ) in get_project_information(
            distribution
        ):
            lines.append(
                f"{label}: {url}"
            )

        lines.append("")

    # ======================================
    # Python
    # ======================================

    lines.extend(
        [
            "Python",
            "------",
            "",
            (
                f"Python {platform.python_version()} "
                "is included in the packaged application."
            ),
            (
                "Python is distributed under the "
                "Python Software Foundation License."
            ),
            (
                "See third_party_licenses/Python-* "
                "for the license text."
            ),
            "",
        ]
    )

    # ======================================
    # Tcl/Tk
    # ======================================

    lines.extend(
        [
            "Tcl/Tk",
            "------",
            "",
            (
                "Tkinter uses Tcl/Tk."
            ),
            (
                "Available Tcl/Tk license.terms files "
                "from the Python installation are included "
                "under third_party_licenses/Tcl-Tk."
            ),
            "",
        ]
    )

    # ======================================
    # FFmpeg
    # ======================================

    lines.extend(
        [
            "FFmpeg",
            "------",
            "",
            (
                "FFmpeg is not included in the "
                "Transcribe distribution archive."
            ),
            (
                "When required, Transcribe downloads "
                "an FFmpeg Windows x86_64 LGPL build "
                "provided by BtbN/FFmpeg-Builds."
            ),
            (
                "The selected FFmpeg build is used as "
                "a separate executable."
            ),
            (
                "FFmpeg is licensed under the "
                "GNU Lesser General Public License "
                "version 2.1 or later when built "
                "without GPL-only components."
            ),
            (
                "BtbN/FFmpeg-Builds is a third-party "
                "build provider and is not the author "
                "of FFmpeg."
            ),
            "",
        ]
    )

    # ======================================
    # PyInstaller
    # ======================================

    lines.extend(
        [
            "PyInstaller",
            "-----------",
            "",
            (
                "PyInstaller is used as the "
                "application packaging tool."
            ),
            (
                "The PyInstaller bootloader exception "
                "permits applications built with "
                "PyInstaller to be distributed under "
                "a separate license."
            ),
            "",
        ]
    )

    # ======================================
    # Disclaimer
    # ======================================

    lines.extend(
        [
            "Disclaimer",
            "----------",
            "",
            (
                "Third-party software remains subject "
                "to its respective copyright and "
                "license terms."
            ),
            (
                "This notice does not replace the "
                "original license files included in "
                "third_party_licenses."
            ),
            "",
        ]
    )

    SUMMARY_PATH.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )


def main():
    """
    第三者ライセンス情報を生成する。
    """

    # ======================================
    # 前回生成物を削除
    # ======================================

    if OUTPUT_DIRECTORY.exists():
        shutil.rmtree(
            OUTPUT_DIRECTORY
        )

    if SUMMARY_PATH.exists():
        SUMMARY_PATH.unlink()

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ======================================
    # Runtime dependencies
    # ======================================

    distributions = (
        get_runtime_distributions()
    )

    print(
        "Runtime packages:"
    )

    print()

    for distribution in distributions:
        name = (
            distribution.metadata.get(
                "Name"
            )
            or "unknown"
        )

        version = (
            distribution.version
            or "unknown"
        )

        copied_count = (
            copy_distribution_licenses(
                distribution
            )
        )

        print(
            f"  {name} "
            f"{version}: "
            f"{copied_count} "
            "license file(s)"
        )

    # ======================================
    # Python
    # ======================================

    python_license_found = (
        copy_python_license()
    )

    # ======================================
    # Tcl/Tk
    # ======================================

    tcl_tk_count = (
        copy_tcl_tk_licenses()
    )

    # ======================================
    # Summary
    # ======================================

    write_summary(
        distributions
    )

    # ======================================
    # Result
    # ======================================

    print()

    print(
        "Python license: "
        f"{'found' if python_license_found else 'not found'}"
    )

    print(
        "Tcl/Tk license files: "
        f"{tcl_tk_count}"
    )

    print()

    print(
        f"Created: "
        f"{SUMMARY_PATH}"
    )

    print(
        f"Created: "
        f"{OUTPUT_DIRECTORY}"
    )


if __name__ == "__main__":
    main()