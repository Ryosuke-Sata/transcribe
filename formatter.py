"""Whisperのsegmentを保存用の文章へ整形する。"""

import re
from dataclasses import dataclass


@dataclass
class Sentence:
    """保存する1つの文字起こし区間。"""

    start: float
    end: float
    text: str


class SentenceFormatter:
    """
    Whisperが生成したsegmentをそのまま文章単位として扱う。

    Python側では文章の意味的な分割は行わず、
    不要な空白など最低限の整形のみを行う。
    """

    def push_segment(
        self,
        segment,
    ):
        """
        Whisper segmentをSentenceへ変換する。

        Args:
            segment (dict):
                Whisperが生成したsegment

        Returns:
            list[Sentence]:
                通常はSentenceを1つ含むリスト。
                テキストが空の場合は空リスト。
        """

        text = str(
            segment.get(
                "text",
                "",
            )
        )

        text = self._clean_text(
            text
        )

        if not text:
            return []

        start = float(
            segment.get(
                "start",
                0.0,
            )
        )

        end = float(
            segment.get(
                "end",
                start,
            )
        )

        sentence = Sentence(
            start=start,
            end=end,
            text=text,
        )

        return [
            sentence
        ]

    def flush(self):
        """
        現在は内部バッファを使用しないため、
        flush時に追加で保存する文章はない。
        """

        return []

    @staticmethod
    def _clean_text(
        text,
    ):
        """
        Whisperのsegment文字列を最低限整形する。

        - 先頭・末尾の空白を削除
        - 連続した半角スペースやタブを1つにする
        """

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        return text.strip()


def format_timestamp(
    seconds,
):
    """
    秒数をHH:MM:SS.s形式へ変換する。

    例:
        65.4
        ->
        00:01:05.4
    """

    seconds = max(
        0.0,
        float(seconds),
    )

    hours = int(
        seconds
        // 3600
    )

    seconds -= (
        hours
        * 3600
    )

    minutes = int(
        seconds
        // 60
    )

    seconds -= (
        minutes
        * 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:04.1f}"
    )


def format_timestamp_range(
    sentence,
):
    """
    Sentenceの開始・終了時刻を表示用文字列にする。

    例:
        [00:01:03.2 - 00:01:09.7]
    """

    return (
        "["
        f"{format_timestamp(sentence.start)}"
        " - "
        f"{format_timestamp(sentence.end)}"
        "]"
    )