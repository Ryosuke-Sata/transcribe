"""Whisperによる文字起こし処理。"""

import os

import whisper


class WhisperTranscriber:
    """Whisperモデルの読み込みと文字起こしを担当する。"""

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

        self.model = whisper.load_model(model_name)
        self.model_name = model_name

    def transcribe_file(self, audio_path, language=None):
        """
        1つの音声ファイルを文字起こしする。

        Args:
            audio_path (str):
                音声ファイルのパス

            language (str | None):
                "en"   英語
                "ja"   日本語
                "ko"   韓国語
                None   自動判定

        Returns:
            str:
                保存されたテキストファイルのパス
        """

        if self.model is None:
            raise RuntimeError(
                "Whisperモデルが読み込まれていません。"
            )

        if not os.path.isfile(audio_path):
            raise FileNotFoundError(
                f"ファイルが見つかりません: {audio_path}"
            )

        options = {
            "verbose": False,
            "condition_on_previous_text": False,
        }

        # Noneの場合はWhisperによる自動言語判定
        if language is not None:
            options["language"] = language

        result = self.model.transcribe(
            audio_path,
            **options,
        )

        # 音声ファイルと同じ場所に.txtを保存
        output_path = (
            os.path.splitext(audio_path)[0]
            + ".txt"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(
                result["text"].strip()
            )

        return output_path