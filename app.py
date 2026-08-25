"""GUIとWhisper処理をつなぐController。"""

import os
import queue
import threading

from transcriber import WhisperTranscriber
from ui import TranscribeView


class TranscribeApp:
    """文字起こしアプリ全体を制御する。"""

    def __init__(self, root):
        self.view = TranscribeView(root)

        self.transcriber = WhisperTranscriber()

        self.event_queue = queue.Queue()

        self.worker_thread = None

        self.view.set_start_command(
            self.start_transcription
        )

        self.view.schedule(
            100,
            self._process_events,
        )

    def start_transcription(self):
        """文字起こしを開始する。"""

        if self._is_running():
            return

        audio_paths = (
            self.view.get_audio_paths()
        )

        if not audio_paths:
            self.view.show_warning(
                "ファイル未選択",
                (
                    "文字起こしする音声ファイルを"
                    "選択してください。"
                ),
            )

            return

        model_name = (
            self.view.get_model()
        )

        language = (
            self.view.get_language()
        )

        self.view.set_running(
            True
        )

        self.view.set_progress(
            0
        )

        self.view.set_status(
            f"Whisperモデル '{model_name}' "
            "を読み込んでいます..."
        )

        self.view.append_log(
            f"モデル '{model_name}' "
            "の読み込みを開始します。"
        )

        self.view.start_indeterminate_progress()

        self.worker_thread = threading.Thread(
            target=self._worker,
            args=(
                audio_paths,
                model_name,
                language,
            ),
            daemon=True,
        )

        self.worker_thread.start()

    def _worker(
        self,
        audio_paths,
        model_name,
        language,
    ):
        """別スレッドでWhisperを実行する。"""

        try:
            self.transcriber.load_model(
                model_name
            )

            self.event_queue.put(
                (
                    "model_loaded",
                    model_name,
                )
            )

            total = len(
                audio_paths
            )

            for index, audio_path in enumerate(
                audio_paths,
                start=1,
            ):
                self.event_queue.put(
                    (
                        "file_started",
                        index,
                        total,
                        audio_path,
                    )
                )

                try:
                    output_path = (
                        self.transcriber
                        .transcribe_file(
                            audio_path,
                            language,
                        )
                    )

                except Exception as exc:
                    self.event_queue.put(
                        (
                            "file_error",
                            index,
                            total,
                            audio_path,
                            str(exc),
                        )
                    )

                    continue

                self.event_queue.put(
                    (
                        "file_finished",
                        index,
                        total,
                        audio_path,
                        output_path,
                    )
                )

            self.event_queue.put(
                (
                    "all_finished",
                )
            )

        except Exception as exc:
            self.event_queue.put(
                (
                    "fatal_error",
                    str(exc),
                )
            )

    def _process_events(self):
        """Whisperスレッドから届いた情報をGUIへ反映する。"""

        try:
            while True:
                event = (
                    self.event_queue.get_nowait()
                )

                event_type = event[0]

                if event_type == "model_loaded":
                    model_name = event[1]

                    self.view.stop_indeterminate_progress()

                    self.view.set_progress(
                        0
                    )

                    self.view.set_status(
                        f"モデル '{model_name}' "
                        "の読み込みが完了しました。"
                    )

                    self.view.append_log(
                        f"モデル '{model_name}' "
                        "の読み込みが完了しました。"
                    )

                elif event_type == "file_started":
                    (
                        index,
                        total,
                        audio_path,
                    ) = event[1:]

                    filename = os.path.basename(
                        audio_path
                    )

                    self.view.set_status(
                        f"[{index}/{total}] "
                        f"{filename} を"
                        "文字起こししています..."
                    )

                    self.view.append_log(
                        f"[{index}/{total}] "
                        f"{filename} "
                        "の処理を開始しました。"
                    )

                elif event_type == "file_finished":
                    (
                        index,
                        total,
                        audio_path,
                        output_path,
                    ) = event[1:]

                    filename = os.path.basename(
                        audio_path
                    )

                    progress = (
                        index
                        / total
                        * 100
                    )

                    self.view.set_progress(
                        progress
                    )

                    self.view.set_status(
                        f"[{index}/{total}] "
                        f"{filename} "
                        "の処理が完了しました。"
                    )

                    self.view.append_log(
                        f"保存完了: {output_path}"
                    )

                elif event_type == "file_error":
                    (
                        index,
                        total,
                        audio_path,
                        error_message,
                    ) = event[1:]

                    filename = os.path.basename(
                        audio_path
                    )

                    progress = (
                        index
                        / total
                        * 100
                    )

                    self.view.set_progress(
                        progress
                    )

                    self.view.append_log(
                        f"エラー: {filename}\n"
                        f"{error_message}"
                    )

                elif event_type == "all_finished":
                    self.view.stop_indeterminate_progress()

                    self.view.set_progress(
                        100
                    )

                    self.view.set_status(
                        "すべての文字起こし処理が"
                        "完了しました。"
                    )

                    self.view.append_log(
                        "すべての処理が完了しました。"
                    )

                    self.view.set_running(
                        False
                    )

                    self.view.show_info(
                        "完了",
                        "文字起こし処理が完了しました。",
                    )

                elif event_type == "fatal_error":
                    error_message = event[1]

                    self.view.stop_indeterminate_progress()

                    self.view.set_progress(
                        0
                    )

                    self.view.set_status(
                        "エラーが発生しました。"
                    )

                    self.view.append_log(
                        "致命的なエラー:\n"
                        f"{error_message}"
                    )

                    self.view.set_running(
                        False
                    )

                    self.view.show_error(
                        "エラー",
                        (
                            "文字起こしを開始"
                            "できませんでした。\n\n"
                            f"{error_message}"
                        ),
                    )

        except queue.Empty:
            pass

        self.view.schedule(
            100,
            self._process_events,
        )

    def _is_running(self):
        return (
            self.worker_thread is not None
            and self.worker_thread.is_alive()
        )