"""Transcribeのエントリーポイント。"""

import multiprocessing
import sys


def main(smoke_report=None):
    import tkinter as tk

    from app import TranscribeApp

    root = tk.Tk()
    if smoke_report is not None:
        root.withdraw()
    try:
        TranscribeApp(root)
        if smoke_report is not None:
            # Verify bundled GUI, Whisper tokenizer assets and dynamic imports
            # without downloading a model or FFmpeg.
            import json
            from pathlib import Path
            from whisper.tokenizer import get_tokenizer

            tokens = get_tokenizer(multilingual=True).encode("起動確認")
            if not tokens:
                raise RuntimeError("Whisper tokenizer initialization failed")
            root.update_idletasks()
            Path(smoke_report).write_text(
                json.dumps({"status": "ok", "tokenizer": "ok"}),
                encoding="utf-8",
            )
        else:
            root.mainloop()
    finally:
        if smoke_report is not None:
            root.destroy()


if __name__ == "__main__":
    # 必ずGUIやWhisperを読み込む前に実行する。
    multiprocessing.freeze_support()
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        main(smoke_report=sys.argv[2])
    else:
        main()
