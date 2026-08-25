"""Whisperモデルの読み込みと文字起こし処理。"""

import os

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

        audio = whisper.load_audio(
            audio_path
        )

        duration = (
            len(audio)
            / SAMPLE_RATE
        )

        return (
            audio,
            duration,
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

            # 前区間の文字列を次区間のpromptとして使用しない。
            # これまでの実音声で、この設定の方が
            # 文字起こし結果が安定していたためFalseとする。
            "condition_on_previous_text": True,

            # 今回はWhisper自身のsegmentをそのまま使用する。
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