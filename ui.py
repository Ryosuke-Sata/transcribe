"""TkinterによるGUI画面。"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class TranscribeView:
    """文字起こしアプリのGUI。"""

    MODELS = [
        "tiny",
        "base",
        "small",
        "medium",
        "large",
    ]

    LANGUAGES = {
        "自動判定": None,
        "英語": "en",
        "日本語": "ja",
        "韓国語": "ko",
    }

    AUDIO_FILETYPES = [
        (
            "音声ファイル",
            "*.m4a *.mp3 *.wav *.flac *.aac *.ogg *.wma",
        ),
        (
            "すべてのファイル",
            "*.*",
        ),
    ]

    def __init__(self, root):
        self.root = root

        # 選択された音声ファイル
        self.audio_paths = []

        # 現在文字起こし中か
        self._running = False

        # -----------------------------
        # Tkinter変数
        # -----------------------------

        self.model_var = tk.StringVar(
            value="small"
        )

        self.language_var = tk.StringVar(
            value="自動判定"
        )

        self.status_var = tk.StringVar(
            value="音声ファイルを選択してください。"
        )

        self.progress_var = tk.DoubleVar(
            value=0
        )

        # -----------------------------
        # ウィンドウ設定
        # -----------------------------

        self.root.title(
            "Voice Transcription Tool"
        )

        self.root.geometry(
            "720x620"
        )

        self.root.minsize(
            600,
            520,
        )

        self._build_ui()

    def _build_ui(self):
        """GUIを構築する。"""

        main_frame = ttk.Frame(
            self.root,
            padding=20,
        )

        main_frame.pack(
            fill="both",
            expand=True,
        )

        # =====================================
        # タイトル
        # =====================================

        title_label = ttk.Label(
            main_frame,
            text="Voice Transcription Tool",
            font=("", 18, "bold"),
        )

        title_label.pack(
            anchor="w",
            pady=(0, 18),
        )

        # =====================================
        # 設定
        # =====================================

        settings_frame = ttk.Frame(
            main_frame
        )

        settings_frame.pack(
            fill="x",
            pady=(0, 14),
        )

        # Whisperモデル

        ttk.Label(
            settings_frame,
            text="Whisperモデル:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.model_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.model_var,
            values=self.MODELS,
            state="readonly",
            width=15,
        )

        self.model_combo.grid(
            row=0,
            column=1,
            padx=(10, 25),
        )

        # 言語

        ttk.Label(
            settings_frame,
            text="言語:",
        ).grid(
            row=0,
            column=2,
            sticky="w",
        )

        self.language_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.language_var,
            values=list(
                self.LANGUAGES.keys()
            ),
            state="readonly",
            width=15,
        )

        self.language_combo.grid(
            row=0,
            column=3,
            padx=(10, 0),
        )

        # =====================================
        # ファイル操作
        # =====================================

        file_button_frame = ttk.Frame(
            main_frame
        )

        file_button_frame.pack(
            fill="x",
            pady=(0, 8),
        )

        self.select_button = ttk.Button(
            file_button_frame,
            text="音声ファイルを選択",
            command=self._select_audio_files,
        )

        self.select_button.pack(
            side="left"
        )

        self.clear_button = ttk.Button(
            file_button_frame,
            text="選択をクリア",
            command=self._clear_audio_files,
        )

        self.clear_button.pack(
            side="left",
            padx=(8, 0),
        )

        # =====================================
        # 選択されたファイル
        # =====================================

        ttk.Label(
            main_frame,
            text="選択されたファイル:",
        ).pack(
            anchor="w"
        )

        list_frame = ttk.Frame(
            main_frame
        )

        list_frame.pack(
            fill="both",
            expand=True,
            pady=(6, 14),
        )

        self.file_listbox = tk.Listbox(
            list_frame,
            height=8,
        )

        self.file_listbox.pack(
            side="left",
            fill="both",
            expand=True,
        )

        file_scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.file_listbox.yview,
        )

        file_scrollbar.pack(
            side="right",
            fill="y",
        )

        self.file_listbox.configure(
            yscrollcommand=file_scrollbar.set
        )

        # =====================================
        # 開始 / 停止ボタン
        # =====================================

        action_frame = ttk.Frame(
            main_frame
        )

        action_frame.pack(
            fill="x",
            pady=(0, 14),
        )

        # 最初はファイルがないためdisabled
        self.start_button = ttk.Button(
            action_frame,
            text="文字起こし開始",
            state="disabled",
        )

        self.start_button.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=5,
        )

        self.stop_button = ttk.Button(
            action_frame,
            text="停止",
            state="disabled",
        )

        self.stop_button.pack(
            side="left",
            padx=(8, 0),
            ipady=5,
        )

        # =====================================
        # プログレスバー
        # =====================================

        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )

        self.progress_bar.pack(
            fill="x",
            pady=(0, 8),
        )

        # =====================================
        # ステータス
        # =====================================

        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            wraplength=650,
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        # =====================================
        # ログ
        # =====================================

        ttk.Label(
            main_frame,
            text="ログ:",
        ).pack(
            anchor="w"
        )

        log_frame = ttk.Frame(
            main_frame
        )

        log_frame.pack(
            fill="both",
            expand=True,
            pady=(6, 0),
        )

        self.log_text = tk.Text(
            log_frame,
            height=8,
            wrap="word",
            state="disabled",
        )

        self.log_text.pack(
            side="left",
            fill="both",
            expand=True,
        )

        log_scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log_text.yview,
        )

        log_scrollbar.pack(
            side="right",
            fill="y",
        )

        self.log_text.configure(
            yscrollcommand=log_scrollbar.set
        )

    # =========================================
    # ファイル操作
    # =========================================

    def _select_audio_files(self):
        """音声ファイルを選択する。"""

        paths = filedialog.askopenfilenames(
            title=(
                "文字起こしする"
                "音声ファイルを選択してください"
            ),
            filetypes=self.AUDIO_FILETYPES,
        )

        if not paths:
            return

        added_count = 0

        for path in paths:
            # 重複登録しない
            if path not in self.audio_paths:
                self.audio_paths.append(
                    path
                )

                self.file_listbox.insert(
                    tk.END,
                    path,
                )

                added_count += 1

        self.status_var.set(
            f"{len(self.audio_paths)} 個の"
            "ファイルを選択しています。"
        )

        if added_count > 0:
            self.append_log(
                f"{added_count} 個の"
                "ファイルを追加しました。"
            )

        self._update_start_button()

    def _clear_audio_files(self):
        """クリアボタンからファイル選択を解除する。"""

        if self._running:
            return

        self.clear_audio_files()

        self.progress_var.set(
            0
        )

        self.status_var.set(
            "音声ファイルを選択してください。"
        )

        self.append_log(
            "ファイル選択をクリアしました。"
        )

    def clear_audio_files(self):
        """
        選択された音声ファイルをすべて解除する。

        Controllerからも使用する。
        """

        self.audio_paths.clear()

        self.file_listbox.delete(
            0,
            tk.END,
        )

        self._update_start_button()

    # =========================================
    # Controllerから取得する値
    # =========================================

    def get_audio_paths(self):
        """選択された音声ファイルを返す。"""

        return list(
            self.audio_paths
        )

    def get_model(self):
        """選択されたWhisperモデルを返す。"""

        return self.model_var.get()

    def get_language(self):
        """選択された言語コードを返す。"""

        language_name = (
            self.language_var.get()
        )

        return self.LANGUAGES[
            language_name
        ]

    # =========================================
    # Controllerからイベントを設定
    # =========================================

    def set_start_command(
        self,
        command,
    ):
        """文字起こし開始ボタンの処理を設定する。"""

        self.start_button.configure(
            command=command
        )

    def set_stop_command(
        self,
        command,
    ):
        """停止ボタンの処理を設定する。"""

        self.stop_button.configure(
            command=command
        )

    def set_close_command(
        self,
        command,
    ):
        """ウィンドウを閉じたときの処理を設定する。"""

        self.root.protocol(
            "WM_DELETE_WINDOW",
            command,
        )

    # =========================================
    # ステータス
    # =========================================

    def set_status(
        self,
        message,
    ):
        self.status_var.set(
            message
        )

    def set_progress(
        self,
        value,
    ):
        self.progress_var.set(
            value
        )

    # =========================================
    # プログレスバー
    # =========================================

    def start_indeterminate_progress(self):
        """
        進捗率が不明な処理用。

        主にモデル読み込み時に使用する。
        """

        self.progress_bar.configure(
            mode="indeterminate"
        )

        self.progress_bar.start(
            10
        )

    def stop_indeterminate_progress(self):
        """通常のプログレスバーに戻す。"""

        self.progress_bar.stop()

        self.progress_bar.configure(
            mode="determinate"
        )

    # =========================================
    # ログ
    # =========================================

    def append_log(
        self,
        message,
    ):
        """ログ欄にメッセージを追加する。"""

        self.log_text.configure(
            state="normal"
        )

        self.log_text.insert(
            tk.END,
            message + "\n",
        )

        # 最新ログまでスクロール
        self.log_text.see(
            tk.END
        )

        self.log_text.configure(
            state="disabled"
        )

    # =========================================
    # GUI操作状態
    # =========================================

    def set_running(
        self,
        running,
    ):
        """
        文字起こし中/停止中のGUI状態を変更する。
        """

        self._running = running

        if running:
            # 文字起こし中

            self.select_button.configure(
                state="disabled"
            )

            self.clear_button.configure(
                state="disabled"
            )

            self.start_button.configure(
                state="disabled"
            )

            self.stop_button.configure(
                state="normal"
            )

            self.model_combo.configure(
                state="disabled"
            )

            self.language_combo.configure(
                state="disabled"
            )

        else:
            # 待機中

            self.select_button.configure(
                state="normal"
            )

            self.clear_button.configure(
                state="normal"
            )

            self.stop_button.configure(
                state="disabled"
            )

            self.model_combo.configure(
                state="readonly"
            )

            self.language_combo.configure(
                state="readonly"
            )

            self._update_start_button()

    def set_stopping(self):
        """停止処理中は停止ボタンも無効にする。"""

        self.stop_button.configure(
            state="disabled"
        )

    def _update_start_button(self):
        """
        ファイルが選択されている場合だけ
        「文字起こし開始」を有効にする。
        """

        if self._running:
            self.start_button.configure(
                state="disabled"
            )

            return

        if self.audio_paths:
            self.start_button.configure(
                state="normal"
            )

        else:
            self.start_button.configure(
                state="disabled"
            )

    # =========================================
    # メッセージボックス
    # =========================================

    def show_info(
        self,
        title,
        message,
    ):
        messagebox.showinfo(
            title,
            message,
        )

    def show_warning(
        self,
        title,
        message,
    ):
        messagebox.showwarning(
            title,
            message,
        )

    def show_error(
        self,
        title,
        message,
    ):
        messagebox.showerror(
            title,
            message,
        )

    # =========================================
    # Tkinterイベント
    # =========================================

    def schedule(
        self,
        milliseconds,
        callback,
    ):
        """指定時間後にcallbackを実行する。"""

        self.root.after(
            milliseconds,
            callback,
        )

    def close(self):
        """GUIを終了する。"""

        self.root.destroy()