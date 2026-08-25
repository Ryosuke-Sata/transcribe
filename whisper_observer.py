"""Whisperのtranscribe内部を監視し、segmentと進捗を通知する。"""

import sys

from whisper.audio import HOP_LENGTH, SAMPLE_RATE


class WhisperTranscribeObserver:
    """Whisper公式transcribe()の内部状態を読み取り、callbackへ通知する。"""

    TARGET_MODULE = "whisper.transcribe"
    TARGET_FUNCTION = "transcribe"

    def __init__(
        self,
        on_segments=None,
        on_progress=None,
    ):
        self.on_segments = on_segments
        self.on_progress = on_progress

        self._observed_segment_count = 0
        self._last_processed_seconds = -1.0
        self._total_seconds = None

    def run(self, transcribe_callable):
        """
        transcribe_callableを実行しながらWhisper内部を監視する。

        transcribe_callableは、model.transcribe(...) を実行する
        引数なしのcallableを想定する。
        """

        previous_trace = sys.gettrace()
        sys.settrace(self._global_trace)

        try:
            result = transcribe_callable()
        finally:
            sys.settrace(previous_trace)

        # 正常終了時は100%を保証する
        if (
            self.on_progress is not None
            and self._total_seconds is not None
        ):
            self.on_progress(
                self._total_seconds,
                self._total_seconds,
            )

        return result

    def _global_trace(self, frame, event, arg):
        """対象のwhisper.transcribe()だけline traceを有効にする。"""

        if event != "call":
            return None

        if (
            frame.f_globals.get("__name__")
            == self.TARGET_MODULE
            and frame.f_code.co_name
            == self.TARGET_FUNCTION
        ):
            return self._local_trace

        return None

    def _local_trace(self, frame, event, arg):
        """Whisperのtranscribe()実行中に内部状態を確認する。"""

        if event in {
            "line",
            "return",
            "exception",
        }:
            local_vars = frame.f_locals

            self._emit_new_segments(
                local_vars
            )

            self._emit_progress(
                local_vars
            )

        return self._local_trace

    def _emit_new_segments(self, local_vars):
        """all_segmentsへ新たに追加されたsegmentだけを通知する。"""

        if self.on_segments is None:
            return

        all_segments = local_vars.get(
            "all_segments"
        )

        if not isinstance(
            all_segments,
            list,
        ):
            return

        segment_count = len(
            all_segments
        )

        if (
            segment_count
            <= self._observed_segment_count
        ):
            return

        new_segments = []

        for segment in all_segments[
            self._observed_segment_count:
            segment_count
        ]:
            snapshot = (
                self._snapshot_segment(
                    segment
                )
            )

            if snapshot is not None:
                new_segments.append(
                    snapshot
                )

        self._observed_segment_count = (
            segment_count
        )

        if new_segments:
            self.on_segments(
                new_segments
            )

    def _emit_progress(self, local_vars):
        """seek/content_framesから現在の処理位置を通知する。"""

        if self.on_progress is None:
            return

        seek = local_vars.get(
            "seek"
        )

        content_frames = local_vars.get(
            "content_frames"
        )

        content_duration = (
            local_vars.get(
                "content_duration"
            )
        )

        if (
            not isinstance(
                seek,
                (int, float),
            )
            or not isinstance(
                content_frames,
                (int, float),
            )
            or content_frames <= 0
        ):
            return

        if isinstance(
            content_duration,
            (int, float),
        ):
            total_seconds = float(
                content_duration
            )
        else:
            total_seconds = (
                float(content_frames)
                * HOP_LENGTH
                / SAMPLE_RATE
            )

        processed_seconds = (
            float(seek)
            * HOP_LENGTH
            / SAMPLE_RATE
        )

        processed_seconds = max(
            0.0,
            min(
                processed_seconds,
                total_seconds,
            ),
        )

        # word_timestamps等でseekが微調整されても、
        # GUI上の進捗は後退させない。
        processed_seconds = max(
            processed_seconds,
            self._last_processed_seconds,
        )

        self._total_seconds = (
            total_seconds
        )

        # 同じ値を何度もQueueへ送らない
        if (
            processed_seconds
            <= self._last_processed_seconds
            + 0.01
        ):
            return

        self._last_processed_seconds = (
            processed_seconds
        )

        self.on_progress(
            processed_seconds,
            total_seconds,
        )

    @staticmethod
    def _snapshot_segment(segment):
        """
        multiprocessing Queueへ安全に渡せるように、
        必要なデータだけ通常のPython型へコピーする。
        """

        if not isinstance(
            segment,
            dict,
        ):
            return None

        text = str(
            segment.get(
                "text",
                "",
            )
        )

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

        words = []

        for word in (
            segment.get(
                "words"
            )
            or []
        ):
            if not isinstance(
                word,
                dict,
            ):
                continue

            word_text = str(
                word.get(
                    "word",
                    "",
                )
            )

            if not word_text:
                continue

            word_start = word.get(
                "start"
            )

            word_end = word.get(
                "end"
            )

            if (
                word_start is None
                or word_end is None
            ):
                continue

            words.append(
                {
                    "word": word_text,
                    "start": float(
                        word_start
                    ),
                    "end": float(
                        word_end
                    ),
                }
            )

        return {
            "start": start,
            "end": end,
            "text": text,
            "words": words,
        }