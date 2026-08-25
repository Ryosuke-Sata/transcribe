"""Whisperモデルの読み込みと文字起こし処理。"""

import os
import subprocess

import numpy as np
import whisper
from whisper.audio import SAMPLE_RATE

from whisper_observer import WhisperTranscribeObserver


class WhisperTranscriber:
    """Whisperによるローカル文字起こしを担当する。"""

    def __init__(self):
        self.model = None
        self.model_name = None

    def load_model(self, model_name):
        """指定されたWhisperモデルを読み込む。"""

        if (
            self.model is not None
            and self.model_name == model_name
        ):
            return

        self.model = whisper.load_model(
            model_name
        )

        self.model_name = model_name

    @staticmethod
    def load_audio(audio_path):
        """
        音声ファイルを16kHz monoのNumPy配列として読み込む。

        WindowsではFFmpeg実行時に
        コンソールウィンドウを表示しない。

        Returns:
            tuple:
                音声データ
                音声時間（秒）
        """

        if not os.path.isfile(
            audio_path
        ):
            raise FileNotFoundError(
                "ファイルが見つかりません: "
                f"{audio_path}"
            )

        audio = (
            WhisperTranscriber
            ._load_audio_with_ffmpeg(
                audio_path
            )
        )

        duration = (
            len(audio)
            / SAMPLE_RATE
        )

        return (
            audio,
            duration,
        )

    @staticmethod
    def _load_audio_with_ffmpeg(
        audio_path,
    ):
        """
        FFmpegを使用して音声を
        16kHz mono PCMへ変換する。

        Whisperのload_audio()と同等の処理を行うが、
        WindowsではCREATE_NO_WINDOWを指定する。
        """

        command = [
            "ffmpeg",
            "-nostdin",
            "-threads",
            "0",
            "-i",
            audio_path,
            "-f",
            "s16le",
            "-ac",
            "1",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(
                SAMPLE_RATE
            ),
            "-",
        ]

        creation_flags = 0

        if os.name == "nt":
            creation_flags = getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            )

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                creationflags=(
                    creation_flags
                ),
            )

        except FileNotFoundError as exc:
            raise RuntimeError(
                "FFmpegを実行できませんでした。"
            ) from exc

        except subprocess.CalledProcessError as exc:
            error_message = (
                exc.stderr.decode(
                    "utf-8",
                    errors="replace",
                )
            )

            raise RuntimeError(
                "音声ファイルの読み込みに"
                "失敗しました。"
                "\n"
                f"{error_message}"
            ) from exc

        return (
            np.frombuffer(
                result.stdout,
                np.int16,
            )
            .flatten()
            .astype(
                np.float32
            )
            / 32768.0
        )

    def transcribe_audio(
        self,
        audio,
        language=None,
        on_segments=None,
        on_progress=None,
    ):
        """
        音声全体を1回のWhisper transcribe()で処理する。

        Whisper内部でsegmentが確定した時点と、
        処理位置が進んだ時点をObserverから通知する。
        """

        if self.model is None:
            raise RuntimeError(
                "Whisperモデルが読み込まれていません。"
            )

        options = {
            # ターミナルへの出力を抑制
            "verbose": None,

            # 前区間の認識結果を、
            # 次区間を認識するときの文脈として利用する。
            "condition_on_previous_text": True,

            # Whisper自身のsegment timestampを使用するため、
            # 単語単位のtimestampは取得しない。
            "word_timestamps": False,

            "task": "transcribe",
        }

        if language is not None:
            options["language"] = language

        observer = WhisperTranscribeObserver(
            on_segments=on_segments,
            on_progress=on_progress,
        )

        return observer.run(
            lambda: self.model.transcribe(
                audio,
                **options,
            )
        )