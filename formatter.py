"""Whisperのsegmentを文字数に基づいてまとめる。"""

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
    Whisperが生成したsegmentを文字数に基づいてまとめる。

    segmentは途中で分割せず、
    複数segmentをmax_chars以下になる範囲で結合する。

    次のsegmentを追加するとmax_charsを超える場合は、
    それまでのsegment群を1つの文章として確定し、
    次のsegmentから新しいまとまりを開始する。

    1つのsegmentだけでmax_charsを超える場合は、
    そのsegmentを分割せず、そのまま1つの文章として扱う。
    """

    def __init__(
        self,
        max_chars=100,
    ):
        if max_chars <= 0:
            raise ValueError(
                "max_charsは1以上で指定してください。"
            )

        self.max_chars = max_chars

        self.current_start = None
        self.current_end = None
        self.current_text = ""

    def push_segment(
        self,
        segment,
    ):
        """
        Whisper segmentを追加する。

        Returns:
            list[Sentence]:
                文字数条件によって確定した文章。
                まだ確定しない場合は空リスト。
        """

        raw_text = str(
            segment.get(
                "text",
                "",
            )
        )

        text = self._normalize_segment_text(
            raw_text
        )

        if not text.strip():
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

        completed = []

        # =====================================
        # バッファが空の場合
        # =====================================

        if not self.current_text:
            self._start_new_group(
                start=start,
                end=end,
                text=text,
            )

            # 1segmentだけで上限を超える場合。
            # segment自体は分割しない。
            if (
                self._current_length()
                > self.max_chars
            ):
                sentence = (
                    self._flush_current()
                )

                if sentence is not None:
                    completed.append(
                        sentence
                    )

            return completed

        # =====================================
        # 現在の文章 + 次segment
        # =====================================

        candidate_text = (
            self.current_text
            + text
        )

        candidate_length = len(
            candidate_text.strip()
        )

        # =====================================
        # 上限以内なら結合
        # =====================================

        if (
            candidate_length
            <= self.max_chars
        ):
            self.current_text = (
                candidate_text
            )

            self.current_end = end

            return completed

        # =====================================
        # 上限を超える場合
        #
        # 現在までを確定し、
        # 今回のsegmentから新しく開始する。
        # =====================================

        sentence = (
            self._flush_current()
        )

        if sentence is not None:
            completed.append(
                sentence
            )

        self._start_new_group(
            start=start,
            end=end,
            text=text,
        )

        # 今回のsegment単体が上限を超えている場合は
        # segmentを分割せず、そのまま確定する。
        if (
            self._current_length()
            > self.max_chars
        ):
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
        音声終了時に、
        バッファに残っているsegment群を確定する。
        """

        sentence = (
            self._flush_current()
        )

        if sentence is None:
            return []

        return [
            sentence
        ]

    def _start_new_group(
        self,
        start,
        end,
        text,
    ):
        """新しいsegmentグループを開始する。"""

        self.current_start = start
        self.current_end = end

        # 最初のsegmentだけは
        # 先頭の空白を取り除く。
        self.current_text = (
            text.lstrip()
        )

    def _flush_current(self):
        """現在のsegmentグループを確定する。"""

        if not self.current_text:
            return None

        sentence = Sentence(
            start=float(
                self.current_start
            ),
            end=float(
                self.current_end
            ),
            text=self.current_text.strip(),
        )

        self.current_start = None
        self.current_end = None
        self.current_text = ""

        return sentence

    def _current_length(self):
        """現在の文章の文字数を返す。"""

        return len(
            self.current_text.strip()
        )

    @staticmethod
    def _normalize_segment_text(
        text,
    ):
        """
        Whisperのsegment内の空白を最低限整理する。

        segment先頭の空白は保持する。
        Whisperが英語などで付けた単語間スペースを
        segment結合時にも利用するため。

        連続する空白・タブ・改行は1つの空白にまとめる。
        """

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.rstrip()


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