"""GUIとWhisper処理をつなぐController。"""

import multiprocessing
import os
import queue

from ui import TranscribeView
from worker import transcribe_worker


class TranscribeApp:
    """文字起こしアプリ全体を制御する。"""

    def __init__(self, root):
        # -----------------------------
        # GUI
        # -----------------------------

        self.view = TranscribeView(
            root
        )

        # -----------------------------
        # multiprocessing
        # -----------------------------

        # Windowsと同じspawn方式を利用する
        self.mp_context = (
            multiprocessing.get_context(
                "spawn"
            )
        )

        self.worker_process = None
        self.event_queue = None

        # 停止処理中かどうか
        self.stopping = False

        # -----------------------------
        # GUIイベント
        # -----------------------------

        self.view.set_start_command(
            self.start_transcription
        )

        self.view.set_stop_command(
            self.stop_transcription
        )

        self.view.set_close_command(
            self.close_application
        )

        # Workerから送られてくるイベントを確認
        self.view.schedule(
            100,
            self._process_events,
        )

    # =========================================
    # 文字起こし開始
    # =========================================

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
                    "文字起こしする"
                    "音声ファイルを選択してください。"
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

        # Workerとの通信用Queue
        self.event_queue = (
            self.mp_context.Queue()
        )

        # -----------------------------
        # GUIを処理中状態へ
        # -----------------------------

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
            f"Whisperモデル '{model_name}' "
            "の読み込みを開始します。"
        )

        self.view.start_indeterminate_progress()

        # -----------------------------
        # Worker Process作成
        # -----------------------------

        self.worker_process = (
            self.mp_context.Process(
                target=transcribe_worker,
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
                    "開始できませんでした。\n\n"
                    f"{exc}"
                ),
            )

    # =========================================
    # 停止
    # =========================================

    def stop_transcription(self):
        """現在実行中の文字起こしを停止する。"""

        if not self._is_running():
            return

        self.stopping = True

        self.view.set_stopping()

        self.view.set_status(
            "文字起こしを停止しています..."
        )

        self.view.append_log(
            "文字起こしの停止を開始します。"
        )

        # Whisperを実行しているProcessを終了する
        self.worker_process.terminate()

        # Processが実際に終了したか確認する
        self.view.schedule(
            100,
            self._wait_for_stop,
        )

    def _wait_for_stop(self):
        """Worker Processが終了するまで確認する。"""

        if (
            self.worker_process is not None
            and self.worker_process.is_alive()
        ):
            self.view.schedule(
                100,
                self._wait_for_stop,
            )

            return

        self._cleanup_worker()

        self.stopping = False

        self.view.stop_indeterminate_progress()

        # 停止後はファイル選択も解除
        self.view.clear_audio_files()

        self.view.set_progress(
            0
        )

        self.view.set_running(
            False
        )

        self.view.set_status(
            "文字起こしを中断しました。"
        )

        self.view.append_log(
            "文字起こしを中断しました。"
        )

    # =========================================
    # Workerイベント処理
    # =========================================

    def _process_events(self):
        """
        Worker Processから届いたイベントを
        Tkinterへ反映する。
        """

        # 停止処理中は古いイベントを処理しない
        if not self.stopping:
            self._read_worker_events()

        # 100msごとに継続して確認
        self.view.schedule(
            100,
            self._process_events,
        )

    def _read_worker_events(self):
        """Queueに入っているWorkerイベントを処理する。"""

        if self.event_queue is None:
            return

        try:
            while True:
                event = (
                    self.event_queue.get_nowait()
                )

                event_type = event[0]

                # ---------------------------------
                # モデル読み込み完了
                # ---------------------------------

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

                # ---------------------------------
                # ファイル処理開始
                # ---------------------------------

                elif event_type == "file_started":
                    (
                        index,
                        total,
                        audio_path,
                    ) = event[1:]

                    filename = (
                        os.path.basename(
                            audio_path
                        )
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

                # ---------------------------------
                # ファイル処理完了
                # ---------------------------------

                elif event_type == "file_finished":
                    (
                        index,
                        total,
                        audio_path,
                        output_path,
                    ) = event[1:]

                    filename = (
                        os.path.basename(
                            audio_path
                        )
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

                # ---------------------------------
                # ファイル単位エラー
                # ---------------------------------

                elif event_type == "file_error":
                    (
                        index,
                        total,
                        audio_path,
                        error_message,
                    ) = event[1:]

                    filename = (
                        os.path.basename(
                            audio_path
                        )
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

                # ---------------------------------
                # 全処理完了
                # ---------------------------------

                elif event_type == "all_finished":
                    self._finish_transcription()

                    break

                # ---------------------------------
                # 致命的エラー
                # ---------------------------------

                elif event_type == "fatal_error":
                    self._handle_fatal_error(
                        event[1]
                    )

                    break

        except queue.Empty:
            pass

    # =========================================
    # 正常終了
    # =========================================

    def _finish_transcription(self):
        """すべての文字起こしが終了した後の処理。"""

        self.view.stop_indeterminate_progress()

        self.view.set_progress(
            100
        )

        # ---------------------------------
        # 重要
        #
        # 完了したファイルを自動的に解除する
        # ---------------------------------

        self.view.clear_audio_files()

        # GUIを待機状態へ戻す
        self.view.set_running(
            False
        )

        self.view.set_status(
            "すべての文字起こし処理が完了しました。"
        )

        self.view.append_log(
            "すべての処理が完了しました。"
        )

        self.view.show_info(
            "完了",
            "文字起こし処理が完了しました。",
        )

        # 終了したProcessを回収
        self.view.schedule(
            100,
            self._cleanup_finished_worker,
        )

    # =========================================
    # エラー
    # =========================================

    def _handle_fatal_error(
        self,
        error_message,
    ):
        """モデル読み込みなどの致命的エラーを処理する。"""

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
            "致命的なエラー:\n"
            f"{error_message}"
        )

        self.view.show_error(
            "エラー",
            (
                "文字起こしを開始"
                "できませんでした。\n\n"
                f"{error_message}"
            ),
        )

        self.view.schedule(
            100,
            self._cleanup_finished_worker,
        )

    # =========================================
    # Process後始末
    # =========================================

    def _cleanup_finished_worker(self):
        """終了したWorker Processを回収する。"""

        if (
            self.worker_process is not None
            and self.worker_process.is_alive()
        ):
            self.view.schedule(
                100,
                self._cleanup_finished_worker,
            )

            return

        self._cleanup_worker()

    def _cleanup_worker(self):
        """Worker ProcessとQueueを破棄する。"""

        if self.worker_process is not None:
            try:
                self.worker_process.join(
                    timeout=1
                )

            except Exception:
                pass

            self.worker_process = None

        self._close_event_queue()

    def _close_event_queue(self):
        """multiprocessing Queueを閉じる。"""

        if self.event_queue is None:
            return

        try:
            self.event_queue.close()

        except Exception:
            pass

        self.event_queue = None

    # =========================================
    # アプリ終了
    # =========================================

    def close_application(self):
        """
        ウィンドウを閉じた場合も
        Whisper Processを終了する。
        """

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
    # 状態確認
    # =========================================

    def _is_running(self):
        """Whisper Processが実行中か確認する。"""

        return (
            self.worker_process is not None
            and self.worker_process.is_alive()
        )