"""Transcribe専用FFmpegの取得と管理を担当する。"""

import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path


FFMPEG_ARCHIVE_NAME = (
    "ffmpeg-n9.0-latest-win64-lgpl-9.0.zip"
)

FFMPEG_DOWNLOAD_URL = (
    "https://github.com/"
    "BtbN/FFmpeg-Builds/"
    "releases/download/latest/"
    f"{FFMPEG_ARCHIVE_NAME}"
)

FFMPEG_CHECKSUMS_URL = (
    "https://github.com/"
    "BtbN/FFmpeg-Builds/"
    "releases/download/latest/"
    "checksums.sha256"
)

USER_AGENT = (
    "Transcribe-FFmpeg-Downloader"
)


def get_ffmpeg_directory():
    """
    Transcribe専用FFmpegの保存先を返す。

    Windows:
        %LOCALAPPDATA%\\Transcribe\\ffmpeg
    """

    if os.name != "nt":
        raise RuntimeError(
            "現在のFFmpeg自動取得機能は"
            "Windowsのみ対応しています。"
        )

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if not local_app_data:
        raise RuntimeError(
            "LOCALAPPDATAを取得できませんでした。"
        )

    return (
        Path(local_app_data)
        / "Transcribe"
        / "ffmpeg"
    )


def get_ffmpeg_path():
    """
    Transcribe専用ffmpeg.exeのパスを返す。
    """

    return (
        get_ffmpeg_directory()
        / "ffmpeg.exe"
    )


def ensure_ffmpeg(
    on_download_start=None,
):
    """
    Transcribe専用FFmpegを利用可能な状態にする。

    既に専用FFmpegが存在して正常に動作する場合は、
    そのまま使用する。

    存在しない場合はBtbNからLGPL版を取得する。

    Windows全体のPATHは変更せず、
    現在のWorkerプロセス内だけPATHを変更する。

    Returns:
        tuple:
            ffmpeg.exeのPath
            今回ダウンロードしたかどうか
    """

    ffmpeg_path = (
        get_ffmpeg_path()
    )

    # =====================================
    # 既存の専用FFmpegを確認
    # =====================================

    if ffmpeg_path.is_file():
        if _is_ffmpeg_usable(
            ffmpeg_path
        ):
            _add_ffmpeg_to_process_path(
                ffmpeg_path.parent
            )

            return (
                ffmpeg_path,
                False,
            )

        # ファイルはあるが壊れている場合は削除
        try:
            ffmpeg_path.unlink()

        except OSError as exc:
            raise RuntimeError(
                "既存のFFmpegが正常ではなく、"
                "削除にも失敗しました。"
                "\n"
                f"{ffmpeg_path}"
            ) from exc

    # =====================================
    # 初回ダウンロード
    # =====================================

    if on_download_start is not None:
        on_download_start()

    ffmpeg_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    _download_and_install_ffmpeg(
        ffmpeg_path
    )

    # =====================================
    # インストール後の確認
    # =====================================

    if not _is_ffmpeg_usable(
        ffmpeg_path
    ):
        try:
            ffmpeg_path.unlink()

        except OSError:
            pass

        raise RuntimeError(
            "ダウンロードしたFFmpegを"
            "正常に実行できませんでした。"
        )

    # =====================================
    # Workerプロセス内だけPATHへ追加
    # =====================================

    _add_ffmpeg_to_process_path(
        ffmpeg_path.parent
    )

    return (
        ffmpeg_path,
        True,
    )


def _download_and_install_ffmpeg(
    destination,
):
    """
    BtbNからFFmpegのZIPを取得し、
    SHA-256を確認したうえで
    ffmpeg.exeだけを保存する。
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_directory = Path(
            temp_dir
        )

        archive_path = (
            temp_directory
            / FFMPEG_ARCHIVE_NAME
        )

        # =================================
        # BtbN公開チェックサム取得
        # =================================

        expected_sha256 = (
            _get_expected_sha256()
        )

        # =================================
        # ZIPダウンロード
        # =================================

        _download_file(
            FFMPEG_DOWNLOAD_URL,
            archive_path,
        )

        # =================================
        # SHA-256確認
        # =================================

        actual_sha256 = (
            _calculate_sha256(
                archive_path
            )
        )

        if (
            actual_sha256.lower()
            != expected_sha256.lower()
        ):
            raise RuntimeError(
                "FFmpegダウンロードファイルの"
                "SHA-256が一致しません。"
                "\n"
                "安全のためインストールを"
                "中止しました。"
            )

        # =================================
        # ZIPからffmpeg.exeだけ取得
        # =================================

        temporary_exe = (
            destination.parent
            / "ffmpeg.download.exe"
        )

        try:
            with zipfile.ZipFile(
                archive_path,
                "r",
            ) as archive:

                ffmpeg_member = (
                    _find_ffmpeg_member(
                        archive
                    )
                )

                if ffmpeg_member is None:
                    raise RuntimeError(
                        "ダウンロードしたZIP内に"
                        "ffmpeg.exeが"
                        "見つかりませんでした。"
                    )

                with (
                    archive.open(
                        ffmpeg_member,
                        "r",
                    ) as source,
                    open(
                        temporary_exe,
                        "wb",
                    ) as target,
                ):
                    shutil.copyfileobj(
                        source,
                        target,
                    )

            # 一時ファイルを正式なffmpeg.exeへ置換
            os.replace(
                temporary_exe,
                destination,
            )

        except zipfile.BadZipFile as exc:
            raise RuntimeError(
                "ダウンロードしたFFmpegの"
                "ZIPファイルが壊れています。"
            ) from exc

        finally:
            if temporary_exe.exists():
                try:
                    temporary_exe.unlink()

                except OSError:
                    pass


def _get_expected_sha256():
    """
    BtbNが公開しているchecksums.sha256から
    対象ZIPのSHA-256を取得する。
    """

    request = urllib.request.Request(
        FFMPEG_CHECKSUMS_URL,
        headers={
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            checksum_text = (
                response
                .read()
                .decode(
                    "utf-8",
                    errors="replace",
                )
            )

    except Exception as exc:
        raise RuntimeError(
            "FFmpegのチェックサム情報を"
            "取得できませんでした。"
            "\n"
            f"{exc}"
        ) from exc

    for line in (
        checksum_text.splitlines()
    ):
        parts = line.strip().split()

        if len(parts) < 2:
            continue

        checksum = parts[0]

        filename = (
            parts[-1]
            .lstrip("*")
        )

        if (
            filename
            == FFMPEG_ARCHIVE_NAME
        ):
            return checksum

    raise RuntimeError(
        "FFmpegのSHA-256情報が"
        "見つかりませんでした。"
    )


def _download_file(
    url,
    destination,
):
    """
    URLからファイルをダウンロードする。
    """

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with (
            urllib.request.urlopen(
                request,
                timeout=60,
            ) as response,
            open(
                destination,
                "wb",
            ) as output_file,
        ):
            while True:
                chunk = response.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                output_file.write(
                    chunk
                )

    except Exception as exc:
        if destination.exists():
            try:
                destination.unlink()

            except OSError:
                pass

        raise RuntimeError(
            "FFmpegのダウンロードに"
            "失敗しました。"
            "\n"
            f"{exc}"
        ) from exc


def _calculate_sha256(
    file_path,
):
    """
    ファイルのSHA-256を計算する。
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:
        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(
                chunk
            )

    return sha256.hexdigest()


def _find_ffmpeg_member(
    archive,
):
    """
    ZIP内のbin/ffmpeg.exeを探す。
    """

    for member in (
        archive.namelist()
    ):
        normalized = (
            member
            .replace(
                "\\",
                "/",
            )
            .lower()
        )

        if normalized.endswith(
            "/bin/ffmpeg.exe"
        ):
            return member

    return None


def _is_ffmpeg_usable(
    ffmpeg_path,
):
    """
    ffmpeg.exeが実際に起動できるか確認する。
    """

    creation_flags = 0

    if os.name == "nt":
        creation_flags = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

    try:
        result = subprocess.run(
            [
                str(ffmpeg_path),
                "-version",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
            creationflags=creation_flags,
        )

        return (
            result.returncode
            == 0
        )

    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return False


def _add_ffmpeg_to_process_path(
    ffmpeg_directory,
):
    """
    現在のPythonプロセスのPATH先頭に
    Transcribe専用FFmpegを追加する。

    Windows全体の環境変数は変更しない。
    """

    directory = str(
        ffmpeg_directory
    )

    current_path = os.environ.get(
        "PATH",
        "",
    )

    existing_paths = (
        current_path.split(
            os.pathsep
        )
    )

    normalized_directory = (
        os.path.normcase(
            os.path.normpath(
                directory
            )
        )
    )

    for existing_path in (
        existing_paths
    ):
        normalized_existing = (
            os.path.normcase(
                os.path.normpath(
                    existing_path
                )
            )
        )

        if (
            normalized_existing
            == normalized_directory
        ):
            return

    os.environ["PATH"] = (
        directory
        + os.pathsep
        + current_path
    )