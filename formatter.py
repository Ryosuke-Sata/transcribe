"""Whisperのsegmentを読みやすい文章単位にまとめる。"""

import math
import re
from dataclasses import dataclass


# 日本語・英語・韓国語で使用する文末記号
END_MARKS = (
    "。",
    "！",
    "？",
    ".",
    "!",
    "?",
)

# この記号の前にはスペースを入れない
CLOSING_PUNCTUATION = (
    "。、，．！？!?.,:;"
    ")]}"
    "」』】〉》"
    "”’"
)

# この記号の直後にはスペースを入れない
OPENING_PUNCTUATION = (
    "([{"
    "\"'"
    "「『【〈《"
    "“‘"
)


@dataclass
class Sentence:
    """整形後の1文章。"""

    start: float
    end: float
    text: str


class SentenceFormatter:
    """Whisperのsegmentを文章単位にまとめる。"""

    def __init__(
        self,
        pause_threshold=1.2,
        max_duration=25.0,
        max_chars=180,
    ):
        # segment間にこれ以上の無音があれば文章を区切る
        self.pause_threshold = pause_threshold

        # 文章が長時間続いた場合は強制的に区切る
        self.max_duration = max_duration

        # 文字数が多すぎた場合も強制的に区切る
        self.max_chars = max_chars

        self.current_start = None
        self.current_end = None
        self.current_text = ""

    def push_segment(
        self,
        start,
        end,
        text,
    ):
        """
        Whisper segmentを追加する。

        文章が確定した場合は
        Sentenceのリストを返す。
        """

        text = text.strip()

        if not text:
            return []

        completed = []

        # =====================================
        # 長い無音があった場合
        # =====================================

        if (
            self.current_text
            and self.current_end is not None
            and (
                start - self.current_end
                >= self.pause_threshold
            )
        ):
            sentence = (
                self._flush_current()
            )

            if sentence is not None:
                completed.append(
                    sentence
                )

        # =====================================
        # segment追加
        # =====================================

        if not self.current_text:
            self.current_start = start
            self.current_end = end
            self.current_text = text

        else:
            self.current_text = (
                self._join_text(
                    self.current_text,
                    text,
                )
            )

            self.current_end = end

        # =====================================
        # 現在の文章長
        # =====================================

        if self.current_start is not None:
            duration = (
                self.current_end
                - self.current_start
            )
        else:
            duration = 0

        # =====================================
        # 文章確定条件
        # =====================================

        should_flush = (
            self._ends_sentence(
                self.current_text
            )
            or duration
            >= self.max_duration
            or len(self.current_text)
            >= self.max_chars
        )

        if should_flush:
            sentence = (
                self._flush_current()
            )

            if sentence is not None:
                completed.append(
                    sentence
                )

        return completed

    def flush(self):
        """
        音声終了時などに、
        残っている文章を強制的に確定する。
        """

        sentence = (
            self._flush_current()
        )

        if sentence is None:
            return []

        return [
            sentence
        ]

    def _flush_current(self):
        """現在の文章を確定する。"""

        if not self.current_text:
            return None

        sentence = Sentence(
            start=self.current_start,
            end=self.current_end,
            text=self.current_text.strip(),
        )

        self.current_start = None
        self.current_end = None
        self.current_text = ""

        return sentence

    @staticmethod
    def _ends_sentence(text):
        """文末記号で終了しているか確認する。"""

        return (
            text.rstrip()
            .endswith(
                END_MARKS
            )
        )

    @staticmethod
    def _is_japanese_char(char):
        """
        日本語文字かどうかを簡易判定する。

        日本語segment同士では
        不要なスペースを挿入しないために使用。
        """

        if not char:
            return False

        code = ord(char)

        return (
            # ひらがな
            0x3040
            <= code
            <= 0x309F

            # カタカナ
            or 0x30A0
            <= code
            <= 0x30FF

            # CJK Extension A
            or 0x3400
            <= code
            <= 0x4DBF

            # 漢字
            or 0x4E00
            <= code
            <= 0x9FFF
        )

    def _join_text(
        self,
        left,
        right,
    ):
        """
        segment同士を自然に連結する。

        日本語:
            基本的にスペースなし

        英語・韓国語:
            基本的にスペースあり
        """

        left = left.rstrip()
        right = right.lstrip()

        if not left:
            return right

        if not right:
            return left

        # 句読点の直前にはスペース不要
        if (
            right[0]
            in CLOSING_PUNCTUATION
        ):
            return (
                left
                + right
            )

        # 開き括弧などの直後もスペース不要
        if (
            left[-1]
            in OPENING_PUNCTUATION
        ):
            return (
                left
                + right
            )

        # 日本語同士
        if (
            self._is_japanese_char(
                left[-1]
            )
            and self._is_japanese_char(
                right[0]
            )
        ):
            return (
                left
                + right
            )

        # 英語・韓国語など
        return (
            left
            + " "
            + right
        )


def format_timestamp(
    seconds,
):
    """秒数をHH:MM:SSへ変換する。"""

    seconds = max(
        0,
        int(seconds),
    )

    hours, remainder = divmod(
        seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


def format_sentence_line(
    sentence,
):
    """
    Sentenceをtxt保存用の形式へ変換する。

    例:
    [00:12:03 - 00:12:10] 本文
    """

    start = format_timestamp(
        math.floor(
            sentence.start
        )
    )

    end = format_timestamp(
        math.ceil(
            sentence.end
        )
    )

    # 連続する空白などを整理
    text = re.sub(
        r"\s+",
        " ",
        sentence.text,
    ).strip()

    return (
        f"[{start} - {end}] "
        f"{text}"
    )