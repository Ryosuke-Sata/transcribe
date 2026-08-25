"""Whisper処理を別プロセスで実行するWorker。"""

from transcriber import WhisperTranscriber


def transcribe_worker(
    event_queue,
    audio_paths,
    model_name,
    language,
):
    """
    Whisperによる文字起こしを実行する。

    この関数自体が別Processで実行される。
    """

    try:
        transcriber = WhisperTranscriber()

        # -----------------------------
        # モデル読み込み
        # -----------------------------

        transcriber.load_model(
            model_name
        )

        event_queue.put(
            (
                "model_loaded",
                model_name,
            )
        )

        total = len(audio_paths)

        # -----------------------------
        # ファイルを順番に処理
        # -----------------------------

        for index, audio_path in enumerate(
            audio_paths,
            start=1,
        ):
            event_queue.put(
                (
                    "file_started",
                    index,
                    total,
                    audio_path,
                )
            )

            try:
                output_path = (
                    transcriber.transcribe_file(
                        audio_path,
                        language,
                    )
                )

            except Exception as exc:
                event_queue.put(
                    (
                        "file_error",
                        index,
                        total,
                        audio_path,
                        str(exc),
                    )
                )

                continue

            event_queue.put(
                (
                    "file_finished",
                    index,
                    total,
                    audio_path,
                    output_path,
                )
            )

        # -----------------------------
        # 全処理完了
        # -----------------------------

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