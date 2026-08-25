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
            (
                "*.m4a",
                "*.mp3",
                "*.wav",
                "*.flac",
                "*.aac",
                "*.ogg",
                "*.wma",
            ),
        ),
        (
            "すべてのファイル",
            "*.*",
        ),
    ]

    def __init__(self, root):
        self.root = root

        self.audio_paths = []

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
        """画面を作成する。"""

        main_frame = ttk.Frame(
            self.root,
            padding=20,
        )

        main_frame.pack(
            fill="both",
            expand=True,
        )

        # -------------------------
        # タイトル
        # -------------------------

        title_label = ttk.Label(
            main_frame,
            text="Voice Transcription Tool",
            font=("", 18, "bold"),
        )

        title_label.pack(
            anchor="w",
            pady=(0, 18),
        )

        # -------------------------
        # モデル選択
        # -------------------------

        settings_frame = ttk.Frame(
            main_frame
        )

        settings_frame.pack(
            fill="x",
            pady=(0, 14),
        )

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

        # -------------------------
        # 言語選択
        # -------------------------

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

        # -------------------------
        # ファイル選択
        # -------------------------

        button_frame = ttk.Frame(
            main_frame
        )

        button_frame.pack(
            fill="x",
            pady=(0, 8),
        )

        self.select_button = ttk.Button(
            button_frame,
            text="音声ファイルを選択",
            command=self._select_audio_files,
        )

        self.select_button.pack(
            side="left"
        )

        self.clear_button = ttk.Button(
            button_frame,
            text="選択をクリア",
            command=self._clear_audio_files,
        )

        self.clear_button.pack(
            side="left",
            padx=(8, 0),
        )

        # -------------------------
        # ファイル一覧
        # -------------------------

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

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.file_listbox.yview,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.file_listbox.configure(
            yscrollcommand=scrollbar.set
        )

        # -------------------------
        # 開始ボタン
        # -------------------------

        self.start_button = ttk.Button(
            main_frame,
            text="文字起こし開始",
        )

        self.start_button.pack(
            fill="x",
            ipady=5,
            pady=(0, 14),
        )

        # -------------------------
        # プログレスバー
        # -------------------------

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

        # -------------------------
        # ステータス
        # -------------------------

        ttk.Label(
            main_frame,
            textvariable=self.status_var,
            wraplength=650,
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        # -------------------------
        # ログ
        # -------------------------

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

    # =====================================
    # ファイル操作
    # =====================================

    def _select_audio_files(self):
        paths = filedialog.askopenfilenames(
            title=(
                "文字起こしする音声ファイルを"
                "選択してください"
            ),
            filetypes=self.AUDIO_FILETYPES,
        )

        if not paths:
            return

        for path in paths:
            if path not in self.audio_paths:
                self.audio_paths.append(path)

                self.file_listbox.insert(
                    tk.END,
                    path,
                )

        self.status_var.set(
            f"{len(self.audio_paths)} 個の"
            "ファイルを選択しています。"
        )

    def _clear_audio_files(self):
        self.audio_paths.clear()

        self.file_listbox.delete(
            0,
            tk.END,
        )

        self.progress_var.set(0)

        self.status_var.set(
            "音声ファイルを選択してください。"
        )

    # =====================================
    # Controllerから使用するメソッド
    # =====================================

    def set_start_command(
        self,
        command,
    ):
        self.start_button.configure(
            command=command
        )

    def get_audio_paths(self):
        return list(
            self.audio_paths
        )

    def get_model(self):
        return self.model_var.get()

    def get_language(self):
        name = self.language_var.get()

        return self.LANGUAGES[name]

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

    def append_log(
        self,
        message,
    ):
        self.log_text.configure(
            state="normal"
        )

        self.log_text.insert(
            tk.END,
            message + "\n",
        )

        self.log_text.see(
            tk.END
        )

        self.log_text.configure(
            state="disabled"
        )

    def start_indeterminate_progress(
        self,
    ):
        self.progress_bar.configure(
            mode="indeterminate"
        )

        self.progress_bar.start(
            10
        )

    def stop_indeterminate_progress(
        self,
    ):
        self.progress_bar.stop()

        self.progress_bar.configure(
            mode="determinate"
        )

    def set_running(
        self,
        running,
    ):
        if running:
            self.select_button.configure(
                state="disabled"
            )

            self.clear_button.configure(
                state="disabled"
            )

            self.start_button.configure(
                state="disabled"
            )

            self.model_combo.configure(
                state="disabled"
            )

            self.language_combo.configure(
                state="disabled"
            )

        else:
            self.select_button.configure(
                state="normal"
            )

            self.clear_button.configure(
                state="normal"
            )

            self.start_button.configure(
                state="normal"
            )

            self.model_combo.configure(
                state="readonly"
            )

            self.language_combo.configure(
                state="readonly"
            )

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

    def schedule(
        self,
        milliseconds,
        callback,
    ):
        self.root.after(
            milliseconds,
            callback,
        )