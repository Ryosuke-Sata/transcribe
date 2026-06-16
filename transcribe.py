"""Whisperを使用した音声ファイルの文字起こしスクリプト。

ユーザーがインタラクティブにモデルを選択し、
GUIダイアログを通じて任意のディレクトリから音声ファイルを選択して文字起こしを行います。
"""

import os
import time
import tkinter as tk
from tkinter import filedialog
import inquirer
import whisper


def select_model():
    """ターミナル上で矢印キーを使って使用するWhisperのモデルを選択します。

    Returns:
        str: 選択されたWhisperモデル名 (例: 'tiny', 'base', 'small', 'medium', 'large')
    """
    models = ["tiny", "base", "small", "medium", "large"]

    questions = [
        inquirer.List(
            "model",
            message="使用するWhisperモデルを矢印キーで選択してください（Enterで確定）",
            choices=models,
            default="large",  # デフォルトは 'large'
        )
    ]
    answers = inquirer.prompt(questions)
    return answers["model"]


def select_audio_files():
    """GUIのファイルダイアログを開いて、任意の場所から複数の音声ファイルを選択します。

    Returns:
        list of str: 選択された音声ファイルのフルパスのリスト。キャンセル時は空のリスト
    """
    # Tkinterのルートウィンドウを初期化して非表示にする
    root = tk.Tk()
    root.withdraw()
    
    # ダイアログが他のウィンドウの後ろに隠れないように最前面に設定
    root.attributes("-topmost", True)

    print("\n音声ファイルを選択するダイアログを開いています...")
    
    # 選択可能な拡張子のフィルタ
    filetypes = [
        ("音声ファイル", "*.m4a;*.mp3;*.wav;*.flac;*.aac;*.ogg;*.wma"),
        ("すべてのファイル", "*.*")
    ]

    # ファイルダイアログを表示してファイルパスを取得（複数選択を許可）
    filepaths = filedialog.askopenfilenames(
        title="文字起こしする音声ファイルを選択してください（複数選択可）",
        filetypes=filetypes
    )

    if not filepaths:
        print("エラー: ファイルの選択がキャンセルされました。")
        return []

    # タプルをリストに変換して返す
    return list(filepaths)


def transcribe_mac_voicememo(audio_paths, model_size):
    """指定された音声ファイル（複数可）をWhisperで文字起こしし、それぞれのテキストファイルに保存します。

    Args:
        audio_paths (str or list of str): 文字起こし対象の音声ファイルのフルパス、またはそのリスト
        model_size (str): 使用するWhisperモデルのサイズ
    """
    # 単一パスが渡された場合はリストに変換
    if isinstance(audio_paths, str):
        audio_paths = [audio_paths]

    # 存在するファイルのみを対象にする
    valid_paths = []
    for path in audio_paths:
        if os.path.exists(path):
            valid_paths.append(path)
        else:
            print(f"エラー: {path} が見つかりません。")

    if not valid_paths:
        print("エラー: 処理可能な音声ファイルがありません。")
        return

    # モデルのロード（複数ファイルでもロードは1回のみ）
    print(f"\n選択されたモデル '{model_size}' を読み込んでいます...")
    model = whisper.load_model(model_size)

    total_start_time = time.time()

    for idx, audio_path in enumerate(valid_paths, 1):
        print(f"\n[{idx}/{len(valid_paths)}] '{audio_path}' の文字起こしを開始します。")
        print("==================================================")
        start_time = time.time()

        # verbose=True で進行状況（セグメント）を順次標準出力に表示
        result = model.transcribe(
            audio_path,
            language="ja",
            verbose=True,
            condition_on_previous_text=False,
        )

        print("==================================================")

        # 元の音声ファイルと同じベース名で .txt ファイル名を作成
        output_filename = os.path.splitext(audio_path)[0] + ".txt"

        # 文字起こし結果をテキストファイルとして保存
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(result["text"])

        elapsed_time = time.time() - start_time
        print(f"ファイル処理が完了しました。（所要時間: {elapsed_time:.1f} 秒）")
        print(f"結果は '{output_filename}' に保存されています。")

    if len(valid_paths) > 1:
        total_elapsed_time = time.time() - total_start_time
        print(f"\nすべての処理が完了しました。（総所要時間: {total_elapsed_time:.1f} 秒）")


if __name__ == "__main__":
    # 1. 使用するWhisperモデルをターミナルで選択
    selected_model = select_model()

    # 2. 対象の音声ファイルをGUIで選択（複数選択可）
    selected_audios = select_audio_files()

    # 音声ファイルが選択された場合のみ文字起こしを実行
    if selected_audios:
        transcribe_mac_voicememo(selected_audios, selected_model)