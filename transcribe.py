"""Transcribeのエントリーポイント。"""

import multiprocessing


def main():
    import tkinter as tk

    from app import TranscribeApp

    root = tk.Tk()

    TranscribeApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    # PyInstallerでmultiprocessingを使用するために必要。
    # GUIやWhisperを読み込む前に実行する。
    multiprocessing.freeze_support()

    main()