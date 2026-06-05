# Voice Transcription Tool (transcribe)

OpenAIのWhisperモデルを利用して、同じディレクトリ内にある音声ファイルをテキストへ文字起こしするPythonスクリプトです。ターミナル上で対話的に操作できます。

---

## 導入手順と実行方法

このプログラムを実行できるようにするための詳細な手順を解説します。

### ステップ 1: Pythonのインストール

本スクリプトの実行には **Python 3.8 〜 3.12** が必要です。

#### インストール状況の確認
すでにインストールされているか確認するには、コマンドプロンプトやPowerShell（Windows）またはターミナル（macOS/Linux）を開き、以下のコマンドを実行します。
```bash
python --version
```
バージョン番号が表示されればインストール済みです。

#### 新規インストール（未インストールの場合）
- **Windows**:
  Windows標準のパッケージマネージャー **winget** を使用して簡単にインストールできます。PowerShellを管理者として開き、以下を実行します。
  ```powershell
  winget install Python.Python.3.11
  ```
- **macOS** (Homebrewを使用):
  ```bash
  brew install python
  ```

---

### ステップ 2: FFmpegのインストール（必須）

Whisperは音声ファイルの処理に **FFmpeg** というツールを使用します。必ずシステムにインストールしてください。

- **Windows** (`winget` を使用):
  PowerShellを開き、以下のコマンドを実行します。
  ```powershell
  winget install Gyan.FFmpeg
  ```
  ※インストール完了後、環境変数を反映させるために**コマンドプロンプトやPowerShellを一度閉じて、開き直してください**。
- **macOS** (`Homebrew` を使用):
  ```bash
  brew install ffmpeg
  ```
- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt update && sudo apt install ffmpeg
  ```

---

### ステップ 3: プロジェクトの準備と依存ライブラリのインストール

1. 本リポジトリのファイル群を任意のフォルダ（例: `C:\transcribe`）にダウンロード・配置します。
2. コマンドプロンプトやPowerShell等で、配置したフォルダに移動します。
   ```powershell
   cd パス/to/transcribe
   ```
3. (推奨) 仮想環境の作成と有効化：
   システム全体を汚さずに実行するため、仮想環境を作成します。
   ```bash
   # 仮想環境を作成
   python -m venv .venv

   # 仮想環境を有効化 (Windows)
   .venv\Scripts\activate

   # 仮想環境を有効化 (macOS/Linux)
   source .venv/bin/activate
   ```
4. 必要なパッケージのインストール：
   `requirements.txt` を用いて、ライブラリを一括インストールします。
   ```bash
   pip install -r requirements.txt
   ```
   ※ `openai-whisper` に含まれる PyTorch 等の容量が大きいため、インストールには数分かかる場合があります。

---

### ステップ 4: 文字起こしの実行

1. 文字起こしを行いたい音声ファイル（`.mp3`, `.m4a`, `.wav`, `.flac` など）を、`transcribe.py` と**同じフォルダ内にコピー**します。
2. スクリプトを実行します。
   ```bash
   python transcribe.py
   ```
3. 画面に指示が表示されます：
   - **モデルの選択**: `tiny`, `base`, `small`, `medium`, `large` から矢印キー（↑ / ↓）で選択し、`Enter` で確定します（最初はダウンロードが発生します。高精度な `large` や、軽量で高速な `base`/`small` など用途に合わせて選んでください）。
   - **音声ファイルの選択**: 同じフォルダ内にある音声ファイルがリストアップされるので、対象ファイルを矢印キーで選択し、`Enter` で確定します。
4. 文字起こしが開始され、進捗がリアルタイムで画面に表示されます。
5. 処理が完了すると、音声ファイルと同じ名前のテキストファイル（例: `sample.txt`）が自動的に生成されます。

---

## Gitの追跡除外設定

音声ファイル（`*.mp3`, `*.m4a` 等）、生成されたテキストファイル（`*.txt`）、およびツールの一時ファイル（`.antigravitycli`）は、`.gitignore` によってGitの管理から自動的に除外されます。
※ ただし、依存パッケージ情報を記載した `requirements.txt` はテキストファイルですが、例外的にGitの追跡対象に含まれるように設定されています。
