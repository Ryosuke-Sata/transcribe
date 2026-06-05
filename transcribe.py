import whisper
import time
import os
import inquirer

def select_model():
    """ターミナル上で矢印キーを使ってWhisperのモデルを選択する"""
    models = ["tiny", "base", "small", "medium", "large"]
    
    questions = [
        inquirer.List(
            'model',
            message="使用するWhisperモデルを矢印キーで選択してください（Enterで確定）",
            choices=models,
            default='large'  # デフォルトは元のプログラムの large
        )
    ]
    answers = inquirer.prompt(questions)
    return answers['model']

def select_audio_file():
    """カレントディレクトリ内の音声ファイルを探索し、矢印キーで選択する"""
    # 一般的な音声ファイルの拡張子
    audio_extensions = ('.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma')
    
    # ディレクトリ内のファイルをリストアップ
    current_dir = os.path.dirname(os.path.abspath(__file__)) if __file__ else os.getcwd()
    all_files = os.listdir(current_dir)
    
    audio_files = [f for f in all_files if f.lower().endswith(audio_extensions)]
    
    if not audio_files:
        print("エラー: スクリプトと同じディレクトリに音声ファイル（.m4a, .mp3 など）が見つかりません。")
        return None

    questions = [
        inquirer.List(
            'audio',
            message="文字起こしする音声ファイルを矢印キーで選択してください（Enterで確定）",
            choices=audio_files
        )
    ]
    answers = inquirer.prompt(questions)
    return answers['audio']

def transcribe_mac_voicememo(audio_path, model_size):
    # ファイルの存在確認
    if not os.path.exists(audio_path):
        print(f"エラー: {audio_path} が見つかりません。")
        return

    print(f"\n選択されたモデル '{model_size}' を読み込んでいます...")
    model = whisper.load_model(model_size)

    print(f"\n'{audio_path}' の文字起こしを開始します。")
    print("==================================================")
    start_time = time.time()

    # ★変更点1: verbose=True を追加して進行状況（セグメント）を順次表示する
    result = model.transcribe(
        audio_path, 
        language="ja", 
        verbose=True, 
        condition_on_previous_text=False
    )

    print("==================================================")

    # ★変更点2: 元の音声ファイル名と同じ名前の .txt ファイルを作成する
    output_filename = os.path.splitext(audio_path)[0] + ".txt"

    # テキストファイルとして保存
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(result["text"])

    elapsed_time = time.time() - start_time
    print(f"\n処理が完了しました。（所要時間: {elapsed_time:.1f} 秒）")
    print(f"結果は '{output_filename}' に保存されています。")

if __name__ == "__main__":
    # 1. 矢印キーでモデルを選択
    selected_model = select_model()
    
    # 2. 矢印キーで音声ファイルを選択
    selected_audio = select_audio_file()
    
    # 音声ファイルが見つかった場合のみ実行
    if selected_audio:
        transcribe_mac_voicememo(selected_audio, selected_model)