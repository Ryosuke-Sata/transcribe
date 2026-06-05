"""Whisperを使用した音声ファイルの文字起こしスクリプト。

このスクリプトは、カレントディレクトリ内の音声ファイルを探索し、
ユーザーがインタラクティブにモデルと音声ファイルを選択して文字起こしを行います。
"""

import os
import time
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


def select_audio_file():
    """カレントディレクトリ内の音声ファイルを探索し、矢印キーで選択します。

    Returns:
        str or None: 選択された音声ファイルのパス。音声ファイルが見つからない場合は None
    """
    # サポートする一般的な音声ファイルの拡張子
    audio_extensions = (".m4a", ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma")

    # スクリプトの実行ディレクトリからファイルをリストアップ
    current_dir = (
        os.path.dirname(os.path.abspath(__file__)) if __file__ else os.getcwd()
    )
    all_files = os.listdir(current_dir)

    # 拡張子に一致する音声ファイルを抽出
    audio_files = [f for f in all_files if f.lower().endswith(audio_extensions)]

    if not audio_files:
        print(
            "エラー: スクリプトと同じディレクトリに音声ファイル（.m4a, .mp3 など）が見つかりません。"
        )
        return None

    questions = [
        inquirer.List(
            "audio",
            message="文字起こしする音声ファイルを矢印キーで選択してください（Enterで確定）",
            choices=audio_files,
        )
    ]
    answers = inquirer.prompt(questions)
    return answers["audio"]


def transcribe_mac_voicememo(audio_path, model_size):
    """指定された音声ファイルをWhisperで文字起こしし、テキストファイルに保存します。

    Args:
        audio_path (str): 文字起こし対象の音声ファイルのパス
        model_size (str): 使用するWhisperモデルのサイズ
    """
    # ファイルの存在確認
    if not os.path.exists(audio_path):
        print(f"エラー: {audio_path} が見つかりません。")
        return

    # モデルのロード
    print(f"\n選択されたモデル '{model_size}' を読み込んでいます...")
    model = whisper.load_model(model_size)

    # 文字起こしの実行
    print(f"\n'{audio_path}' の文字起こしを開始します。")
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
    print(f"\n処理が完了しました。（所要時間: {elapsed_time:.1f} 秒）")
    print(f"結果は '{output_filename}' に保存されています。")


if __name__ == "__main__":
    # 1. 使用するWhisperモデルを選択
    selected_model = select_model()

    # 2. 対象の音声ファイルを選択
    selected_audio = select_audio_file()

    # 音声ファイルが選択された場合のみ文字起こしを実行
    if selected_audio:
        transcribe_mac_voicememo(selected_audio, selected_model)