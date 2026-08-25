"""Whisper文字起こしを別Processで実行するWorker。"""

import os

from whisper.audio import (
    CHUNK_LENGTH,
    SAMPLE_RATE,
)

from formatter import (
    SentenceFormatter,
    format_sentence_line,
)
from transcriber import (
    WhisperTranscriber,
)


# Whisper標準チャンク長
# 現在は30秒
CHUNK_SECONDS = CHUNK_LENGTH


def transcribe_worker(
    event_queue,
    audio_paths,
    model_name,
    language,
):
    """
    複数ファイルを順番に文字起こしする。

    確定した文章は即座にtxtへ保存し、
    GUIへ進捗情報を送信する。
    """

    try:
        transcriber = (
            WhisperTranscriber()
        )

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
        # 全ファイル終了
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
    """1ファイルをチャンク単位で処理する。"""

    if not os.path.isfile(
        audio_path
    ):
        raise FileNotFoundError(
            "ファイルが見つかりません: "
            f"{audio_path}"
        )

    # =====================================
    # 音声読み込み
    # =====================================

    audio = (
        transcriber.load_audio(
            audio_path
        )
    )

    total_seconds = (
        transcriber
        .get_duration_seconds(
            audio
        )
    )

    total_samples = len(
        audio
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
    # 文章整形
    # =====================================

    formatter = (
        SentenceFormatter(
            pause_threshold=1.2,
            max_duration=25.0,
            max_chars=180,
        )
    )

    chunk_samples = int(
        CHUNK_SECONDS
        * SAMPLE_RATE
    )

    # =====================================
    # txtを文字起こし開始時点で作る
    # =====================================

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:

        # =================================
        # 30秒ごとに処理
        # =================================

        for chunk_start in range(
            0,
            total_samples,
            chunk_samples,
        ):
            chunk_end = min(
                chunk_start
                + chunk_samples,
                total_samples,
            )

            audio_chunk = audio[
                chunk_start:chunk_end
            ]

            chunk_offset = (
                chunk_start
                / SAMPLE_RATE
            )

            # =============================
            # Whisper
            # =============================

            segments = (
                transcriber
                .transcribe_chunk(
                    audio_chunk,
                    language,
                )
            )

            # =============================
            # segmentを文章化
            # =============================

            for segment in segments:
                start = (
                    chunk_offset
                    + float(
                        segment.get(
                            "start",
                            0.0,
                        )
                    )
                )

                end = (
                    chunk_offset
                    + float(
                        segment.get(
                            "end",
                            0.0,
                        )
                    )
                )

                text = (
                    segment.get(
                        "text",
                        "",
                    )
                )

                completed_sentences = (
                    formatter.push_segment(
                        start=start,
                        end=end,
                        text=text,
                    )
                )

                for sentence in (
                    completed_sentences
                ):
                    _save_sentence(
                        output_file=output_file,
                        event_queue=event_queue,
                        sentence=sentence,
                        file_index=file_index,
                        total_files=total_files,
                        audio_path=audio_path,
                        output_path=output_path,
                    )

            # =============================
            # GUI進捗更新
            # =============================

            processed_seconds = min(
                chunk_end
                / SAMPLE_RATE,
                total_seconds,
            )

            event_queue.put(
                (
                    "file_progress",
                    file_index,
                    total_files,
                    audio_path,
                    processed_seconds,
                    total_seconds,
                )
            )

        # =================================
        # 最後に残っている文章を保存
        # =================================

        for sentence in (
            formatter.flush()
        ):
            _save_sentence(
                output_file=output_file,
                event_queue=event_queue,
                sentence=sentence,
                file_index=file_index,
                total_files=total_files,
                audio_path=audio_path,
                output_path=output_path,
            )

    # =====================================
    # ファイル終了
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


def _save_sentence(
    output_file,
    event_queue,
    sentence,
    file_index,
    total_files,
    audio_path,
    output_path,
):
    """確定した文章を即座にtxtへ保存する。"""

    line = (
        format_sentence_line(
            sentence
        )
    )

    output_file.write(
        line
        + "\n"
    )

    # =====================================
    # 重要
    #
    # 停止されても、それまでの結果が
    # ファイルに残るよう即flushする
    # =====================================

    output_file.flush()

    # GUIにも直近の文字起こしを通知
    event_queue.put(
        (
            "text_saved",
            file_index,
            total_files,
            audio_path,
            output_path,
            line,
        )
    )