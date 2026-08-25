"""Whisper文字起こしを別Processで実行するWorker。"""

import csv
import os

from formatter import (
    SentenceFormatter,
    format_timestamp_range,
)
from transcriber import WhisperTranscriber


def transcribe_worker(
    event_queue,
    audio_paths,
    model_name,
    language,
):
    """
    複数ファイルを順番に文字起こしする。

    各音声ファイルはWhisperへ1回だけ渡し、
    Whisper内部で確定したsegmentを取得する。

    segmentは一定文字数以下になるようにまとめ、
    確定したまとまりを逐次保存する。
    """

    try:
        transcriber = WhisperTranscriber()

        # =====================================
        # Whisperモデル読み込み
        # =====================================

        transcriber.load_model(
            model_name
        )

        event_queue.put(
            (
                "model_loaded",
                model_name,
            )
        )

        total_files = len(
            audio_paths
        )

        # =====================================
        # ファイルを順番に処理
        # =====================================

        for (
            file_index,
            audio_path,
        ) in enumerate(
            audio_paths,
            start=1,
        ):
            try:
                _transcribe_one_file(
                    event_queue=event_queue,
                    transcriber=transcriber,
                    audio_path=audio_path,
                    file_index=file_index,
                    total_files=total_files,
                    language=language,
                )

            except Exception as exc:
                event_queue.put(
                    (
                        "file_error",
                        file_index,
                        total_files,
                        audio_path,
                        str(exc),
                    )
                )

        # =====================================
        # 全ファイル完了
        # =====================================

        event_queue.put(
            (
                "all_finished",
            )
        )

    except Exception as exc:
        event_queue.put(
            (
                "fatal_error",
                str(exc),
            )
        )


def _transcribe_one_file(
    event_queue,
    transcriber,
    audio_path,
    file_index,
    total_files,
    language,
):
    """
    1つの音声ファイルをWhisperで連続的に処理する。
    """

    # =====================================
    # 音声読み込み
    # =====================================

    (
        audio,
        total_seconds,
    ) = transcriber.load_audio(
        audio_path
    )

    # =====================================
    # 保存先
    # =====================================

    output_path = (
        os.path.splitext(
            audio_path
        )[0]
        + ".txt"
    )

    event_queue.put(
        (
            "file_started",
            file_index,
            total_files,
            audio_path,
            output_path,
            total_seconds,
        )
    )

    # =====================================
    # segment整形
    #
    # 複数segmentを100文字以下になる範囲でまとめる。
    # =====================================

    formatter = SentenceFormatter(
        max_chars=100,
    )

    # Observer経由で何segment取得できたか
    observed_segment_count = 0

    # =====================================
    # 出力ファイル
    # =====================================

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:

        writer = csv.writer(
            output_file,
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )

        # =================================
        # 確定したsegmentグループを保存
        # =================================

        def save_sentence(
            sentence,
        ):
            timestamp = (
                format_timestamp_range(
                    sentence
                )
            )

            # CSVとして正しく保存
            writer.writerow(
                [
                    timestamp,
                    sentence.text,
                ]
            )

            # =================================
            # 確定したまとまりごとに
            # ディスクへ即座に反映する。
            #
            # 処理を途中停止しても、
            # ここまで確定した結果は残る。
            # =================================

            output_file.flush()

            # GUI表示用
            display_line = (
                f"{timestamp}, "
                f"{sentence.text}"
            )

            event_queue.put(
                (
                    "text_saved",
                    file_index,
                    total_files,
                    audio_path,
                    output_path,
                    display_line,
                )
            )

        # =================================
        # Whisper segment通知
        # =================================

        def on_segments(
            new_segments,
        ):
            nonlocal observed_segment_count

            observed_segment_count += len(
                new_segments
            )

            for segment in new_segments:

                completed_sentences = (
                    formatter.push_segment(
                        segment
                    )
                )

                # 文字数条件によって
                # 確定したまとまりだけ保存する。
                for sentence in (
                    completed_sentences
                ):
                    save_sentence(
                        sentence
                    )

        # =================================
        # Whisper進捗通知
        # =================================

        def on_progress(
            processed_seconds,
            detected_total_seconds,
        ):
            if (
                detected_total_seconds
                > 0
            ):
                progress_total = (
                    detected_total_seconds
                )

            else:
                progress_total = (
                    total_seconds
                )

            event_queue.put(
                (
                    "file_progress",
                    file_index,
                    total_files,
                    audio_path,
                    processed_seconds,
                    progress_total,
                )
            )

        # =====================================
        # 文字起こし
        #
        # 音声全体を1回だけWhisperへ渡す。
        # =====================================

        result = (
            transcriber.transcribe_audio(
                audio=audio,
                language=language,
                on_segments=on_segments,
                on_progress=on_progress,
            )
        )

        # =====================================
        # Observerがsegmentを取得できなかった場合
        #
        # Whisper内部実装変更などへのfallback。
        # =====================================

        if (
            observed_segment_count == 0
            and result.get(
                "segments"
            )
        ):
            for segment in (
                result["segments"]
            ):

                completed_sentences = (
                    formatter.push_segment(
                        segment
                    )
                )

                for sentence in (
                    completed_sentences
                ):
                    save_sentence(
                        sentence
                    )

        # =====================================
        # 音声終了時、
        # 最後にバッファへ残っているsegment群を保存
        # =====================================

        for sentence in (
            formatter.flush()
        ):
            save_sentence(
                sentence
            )

    # =====================================
    # 100%まで進捗更新
    # =====================================

    event_queue.put(
        (
            "file_progress",
            file_index,
            total_files,
            audio_path,
            total_seconds,
            total_seconds,
        )
    )

    # =====================================
    # ファイル完了
    # =====================================

    event_queue.put(
        (
            "file_finished",
            file_index,
            total_files,
            audio_path,
            output_path,
            total_seconds,
        )
    )