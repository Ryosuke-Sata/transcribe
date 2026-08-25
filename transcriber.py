"""Whisperモデルの読み込みと音声区間の文字起こし。"""

import whisper
from whisper.audio import SAMPLE_RATE


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
        音声ファイルを16kHz・monoのNumPy配列として読み込む。
        """

        return whisper.load_audio(
            audio_path
        )

    def transcribe_chunk(
        self,
        audio_chunk,
        language=None,
    ):
        """
        音声の1区間を文字起こしする。

        Args:
            audio_chunk:
                Whisperで読み込んだ音声データ

            language:
                None -> 自動判定
                "en" -> 英語
                "ja" -> 日本語
                "ko" -> 韓国語

        Returns:
            Whisperのsegment一覧
        """

        if self.model is None:
            raise RuntimeError(
                "Whisperモデルが読み込まれていません。"
            )

        options = {
            "verbose": False,
            "condition_on_previous_text": False,
            "task": "transcribe",
        }

        if language is not None:
            options["language"] = language

        result = self.model.transcribe(
            audio_chunk,
            **options,
        )

        return result.get(
            "segments",
            [],
        )

    @staticmethod
    def get_duration_seconds(audio):
        """読み込み済み音声の長さを秒で返す。"""

        return (
            len(audio)
            / SAMPLE_RATE
        )