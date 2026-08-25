"""GUIとWhisper WorkerをつなぐController。"""

import multiprocessing
import os
import queue

from ui import TranscribeView
from worker import transcribe_worker


class TranscribeApp:
    """文字起こしアプリ全体を制御する。"""

    def __init__(
        self,
        root,
    ):
        self.view = (
            TranscribeView(
                root
            )
        )

        # Windowsと同じspawn方式
        self.mp_context = (
            multiprocessing
            .get_context(
                "spawn"
            )
        )

        self.worker_process = None
        self.event_queue = None

        self.stopping = False

        self.view.set_start_command(
            self.start_transcription
        )

        self.view.set_stop_command(
            self.stop_transcription
        )

        self.view.set_close_command(
            self.close_application
        )

        self.view.schedule(
            100,
            self._process_events,
        )

    # =========================================
    # Start
    # =========================================

    def start_transcription(self):
        if self._is_running():
            return

        audio_paths = (
            self.view
            .get_audio_paths()
        )

        if not audio_paths:
            self.view.show_warning(
                "ファイル未選択",
                (
                    "文字起こしする"
                    "音声ファイルを"
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

        self.stopping = False

        self.event_queue = (
            self.mp_context.Queue()
        )

        # =====================================
        # GUI
        # =====================================

        self.view.set_running(
            True
        )

        self.view.reset_progress_display()

        self.view.set_status(
            f"Whisperモデル "
            f"'{model_name}' "
            "を読み込んでいます..."
        )

        self.view.append_log(
            f"Whisperモデル "
            f"'{model_name}' "
            "の読み込みを開始します。"
        )

        self.view.start_indeterminate_progress()

        # =====================================
        # Process
        # =====================================

        self.worker_process = (
            self.mp_context.Process(
                target=(
                    transcribe_worker
                ),
                args=(
                    self.event_queue,
                    audio_paths,
                    model_name,
                    language,
                ),
            )
        )

        try:
            self.worker_process.start()

        except Exception as exc:
            self.worker_process = None

            self._close_event_queue()

            self.view.stop_indeterminate_progress()

            self.view.set_running(
                False
            )

            self.view.show_error(
                "エラー",
                (
                    "文字起こし処理を"
                    "開始できませんでした。"
                    "\n\n"
                    f"{exc}"
                ),
            )

    # =========================================
    # Stop
    # =========================================

    def stop_transcription(self):
        if not self._is_running():
            return

        self.stopping = True

        self.view.set_stopping()

        self.view.set_status(
            "文字起こしを"
            "停止しています..."
        )

        self.view.append_log(
            "文字起こしの"
            "停止を開始します。"
        )

        self.worker_process.terminate()

        self.view.schedule(
            100,
            self._wait_for_stop,
        )

    def _wait_for_stop(self):
        if (
            self.worker_process
            is not None
            and self.worker_process
            .is_alive()
        ):
            self.view.schedule(
                100,
                self._wait_for_stop,
            )

            return

        self._cleanup_worker()

        self.stopping = False

        self.view.stop_indeterminate_progress()

        # 誤再実行防止
        self.view.clear_audio_files()

        self.view.set_running(
            False
        )

        self.view.set_status(
            "文字起こしを"
            "中断しました。"
        )

        self.view.append_log(
            "文字起こしを"
            "中断しました。"
        )

        self.view.append_log(
            "停止時点までに"
            "確定した文章は"
            "txtへ保存されています。"
        )

    # =========================================
    # Events
    # =========================================

    def _process_events(self):
        if not self.stopping:
            self._read_worker_events()

        self.view.schedule(
            100,
            self._process_events,
        )

    def _read_worker_events(self):
        if self.event_queue is None:
            return

        try:
            while True:
                event = (
                    self.event_queue
                    .get_nowait()
                )

                event_type = (
                    event[0]
                )

                if (
                    event_type
                    == "model_loaded"
                ):
                    self._handle_model_loaded(
                        event
                    )

                elif (
                    event_type
                    == "file_started"
                ):
                    self._handle_file_started(
                        event
                    )

                elif (
                    event_type
                    == "file_progress"
                ):
                    self._handle_file_progress(
                        event
                    )

                elif (
                    event_type
                    == "text_saved"
                ):
                    self._handle_text_saved(
                        event
                    )

                elif (
                    event_type
                    == "file_finished"
                ):
                    self._handle_file_finished(
                        event
                    )

                elif (
                    event_type
                    == "file_error"
                ):
                    self._handle_file_error(
                        event
                    )

                elif (
                    event_type
                    == "all_finished"
                ):
                    self._finish_transcription()

                    break

                elif (
                    event_type
                    == "fatal_error"
                ):
                    self._handle_fatal_error(
                        event[1]
                    )

                    break

        except queue.Empty:
            pass

    # =========================================
    # Model
    # =========================================

    def _handle_model_loaded(
        self,
        event,
    ):
        model_name = event[1]

        self.view.stop_indeterminate_progress()

        self.view.set_progress(
            0
        )

        self.view.set_status(
            f"モデル '{model_name}' "
            "の読み込みが"
            "完了しました。"
        )

        self.view.append_log(
            f"モデル '{model_name}' "
            "の読み込みが"
            "完了しました。"
        )

    # =========================================
    # File start
    # =========================================

    def _handle_file_started(
        self,
        event,
    ):
        (
            _,
            file_index,
            total_files,
            audio_path,
            output_path,
            total_seconds,
        ) = event

        filename = os.path.basename(
            audio_path
        )

        overall_progress = (
            (
                file_index
                - 1
            )
            / total_files
            * 100
        )

        self.view.set_progress(
            overall_progress
        )

        self.view.set_time_progress(
            0,
            total_seconds,
        )

        self.view.set_status(
            f"[{file_index}/"
            f"{total_files}] "
            f"{filename} を"
            "文字起こししています..."
        )

        self.view.append_log(
            f"[{file_index}/"
            f"{total_files}] "
            f"{filename} "
            "の処理を開始しました。"
        )

        self.view.append_log(
            f"逐次保存先: "
            f"{output_path}"
        )

    # =========================================
    # Progress
    # =========================================

    def _handle_file_progress(
        self,
        event,
    ):
        (
            _,
            file_index,
            total_files,
            _audio_path,
            processed_seconds,
            total_seconds,
        ) = event

        if total_seconds > 0:
            file_ratio = (
                processed_seconds
                / total_seconds
            )
        else:
            file_ratio = 1.0

        overall_progress = (
            (
                file_index
                - 1
                + file_ratio
            )
            / total_files
            * 100
        )

        self.view.set_progress(
            overall_progress
        )

        self.view.set_time_progress(
            processed_seconds,
            total_seconds,
        )

    # =========================================
    # Saved text
    # =========================================

    def _handle_text_saved(
        self,
        event,
    ):
        line = event[5]

        self.view.set_latest_text(
            line
        )

    # =========================================
    # File finish
    # =========================================

    def _handle_file_finished(
        self,
        event,
    ):
        (
            _,
            file_index,
            total_files,
            audio_path,
            output_path,
            total_seconds,
        ) = event

        filename = os.path.basename(
            audio_path
        )

        overall_progress = (
            file_index
            / total_files
            * 100
        )

        self.view.set_progress(
            overall_progress
        )

        self.view.set_time_progress(
            total_seconds,
            total_seconds,
        )

        self.view.set_status(
            f"[{file_index}/"
            f"{total_files}] "
            f"{filename} "
            "の処理が"
            "完了しました。"
        )

        self.view.append_log(
            f"保存完了: "
            f"{output_path}"
        )

    # =========================================
    # File error
    # =========================================

    def _handle_file_error(
        self,
        event,
    ):
        (
            _,
            file_index,
            total_files,
            audio_path,
            error_message,
        ) = event

        filename = os.path.basename(
            audio_path
        )

        overall_progress = (
            file_index
            / total_files
            * 100
        )

        self.view.set_progress(
            overall_progress
        )

        self.view.append_log(
            f"エラー: {filename}"
            "\n"
            f"{error_message}"
        )

    # =========================================
    # Finish
    # =========================================

    def _finish_transcription(self):
        self.view.stop_indeterminate_progress()

        self.view.set_progress(
            100
        )

        # 完了後の誤再実行防止
        self.view.clear_audio_files()

        self.view.set_running(
            False
        )

        self.view.set_status(
            "すべての文字起こし"
            "処理が完了しました。"
        )

        self.view.append_log(
            "すべての処理が"
            "完了しました。"
        )

        self.view.show_info(
            "完了",
            "文字起こし処理が"
            "完了しました。",
        )

        self.view.schedule(
            100,
            self._cleanup_finished_worker,
        )

    # =========================================
    # Fatal error
    # =========================================

    def _handle_fatal_error(
        self,
        error_message,
    ):
        self.view.stop_indeterminate_progress()

        self.view.set_progress(
            0
        )

        self.view.set_running(
            False
        )

        self.view.set_status(
            "エラーが発生しました。"
        )

        self.view.append_log(
            "致命的なエラー:"
            "\n"
            f"{error_message}"
        )

        self.view.show_error(
            "エラー",
            (
                "文字起こしを"
                "開始できませんでした。"
                "\n\n"
                f"{error_message}"
            ),
        )

        self.view.schedule(
            100,
            self._cleanup_finished_worker,
        )

    # =========================================
    # Cleanup
    # =========================================

    def _cleanup_finished_worker(
        self,
    ):
        if (
            self.worker_process
            is not None
            and self.worker_process
            .is_alive()
        ):
            self.view.schedule(
                100,
                self._cleanup_finished_worker,
            )

            return

        self._cleanup_worker()

    def _cleanup_worker(self):
        if (
            self.worker_process
            is not None
        ):
            try:
                self.worker_process.join(
                    timeout=1
                )

            except Exception:
                pass

            self.worker_process = None

        self._close_event_queue()

    def _close_event_queue(self):
        if self.event_queue is None:
            return

        try:
            self.event_queue.close()

        except Exception:
            pass

        self.event_queue = None

    # =========================================
    # Close application
    # =========================================

    def close_application(self):
        if self._is_running():
            try:
                self.worker_process.terminate()

                self.worker_process.join(
                    timeout=1
                )

            except Exception:
                pass

        self.worker_process = None

        self._close_event_queue()

        self.view.close()

    # =========================================
    # State
    # =========================================

    def _is_running(self):
        return (
            self.worker_process
            is not None
            and self.worker_process
            .is_alive()
        )