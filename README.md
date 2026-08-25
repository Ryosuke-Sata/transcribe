# Transcribe

OpenAI Whisperを利用した、Windows向けのローカル文字起こしアプリケーションです。

GUIから音声ファイルを選択し、Whisperモデルと言語を指定して文字起こしできます。

文字起こし処理はローカルPC上で実行され、音声データを外部の文字起こしAPIへ送信する必要はありません。

## Features

- GUIによる音声ファイル選択
- 複数ファイルの連続文字起こし
- Whisperモデルの選択
  - `tiny`
  - `base`
  - `small`
  - `medium`
  - `large`
- 言語の選択
  - 自動判定
  - 日本語
  - 英語
  - 韓国語
- 文字起こし進捗のリアルタイム表示
- 最新の文字起こし結果をGUI上に表示
- 処理途中での停止
- タイムスタンプ付きテキストファイルへの逐次保存
- FFmpegの自動取得
- PythonやFFmpegを事前にインストールせずに利用可能なWindows配布版

## Supported Platforms

現在の配布版は以下を対象としています。

- Windows x64

## Supported Audio Formats

以下の音声ファイルをGUIから選択できます。

- `.m4a`
- `.mp3`
- `.wav`
- `.flac`
- `.aac`
- `.ogg`
- `.wma`

## Installation

### Windows配布版を利用する場合

GitHub ReleasesからWindows向けZIPファイルをダウンロードします。

例:

```text
Transcribe-v1.0.0-win-x64.zip
```

ZIPファイルを任意の場所へ展開してください。

展開後のフォルダは、概ね次のような構成になります。

```text
Transcribe/
├─ Transcribe.exe
├─ THIRD_PARTY_NOTICES.txt
├─ third_party_licenses/
└─ _internal/
```

`Transcribe.exe` を実行するとアプリケーションが起動します。

`_internal` フォルダにはPythonやPyTorchなど、アプリケーションの実行に必要なファイルが含まれています。

そのため、`Transcribe.exe` だけを別の場所へ移動せず、フォルダ全体をそのまま使用してください。

## First Run

Transcribeでは、FFmpeg本体を配布ZIPに含めていません。

文字起こしを開始した際、Transcribe専用のFFmpegが存在しない場合は、BtbN/FFmpeg-BuildsからWindows x86_64向けのLGPL版FFmpegを自動的にダウンロードします。

FFmpegは以下に保存されます。

```text
%LOCALAPPDATA%\Transcribe\ffmpeg\ffmpeg.exe
```

Windows全体のPATHは変更しません。

また、使用するWhisperモデルがPCに保存されていない場合は、Whisperによってモデルのダウンロードが行われます。

そのため、初回利用時や未取得のモデルを初めて使用するときにはインターネット接続が必要です。

FFmpegおよび必要なWhisperモデルの取得後は、文字起こし処理自体はローカルPC上で実行されます。

## Usage

### 1. Transcribeを起動

```text
Transcribe.exe
```

を実行します。

### 2. Whisperモデルを選択

GUI上部の「Whisperモデル」から使用するモデルを選択します。

```text
tiny
base
small
medium
large
```

一般に、大きなモデルほど高い認識精度が期待できますが、処理時間やメモリ使用量も増加します。

初期設定では `small` が選択されています。

### 3. 言語を選択

以下から選択できます。

```text
自動判定
英語
日本語
韓国語
```

通常は「自動判定」のままでも利用できます。

### 4. 音声ファイルを選択

「音声ファイルを選択」ボタンから文字起こしするファイルを選択します。

複数ファイルを同時に選択することもできます。

選択したファイルは上から順番に処理されます。

### 5. 文字起こしを開始

「文字起こし開始」を押します。

処理中はGUIに以下の情報が表示されます。

- 全体進捗
- 現在の音声内での処理位置
- 最新の文字起こし結果
- 処理ログ

### 6. 結果を確認

文字起こし結果は、元の音声ファイルと同じフォルダに保存されます。

例えば、

```text
lecture.m4a
```

を文字起こしすると、

```text
lecture.txt
```

が生成されます。

## Output Format

出力ファイルは `.txt` ですが、各行はCSV互換の形式で保存されます。

例:

```text
[00:00:31.1 - 00:00:33.8],5番の問題について説明します。
[00:00:33.8 - 00:00:40.2],まず、この式を変形します。
```

各行は、

```text
[開始時刻 - 終了時刻],文字起こし結果
```

の形式です。

文章中にカンマなどが含まれる場合は、CSVとして正しく扱えるように必要に応じて引用符が付加されます。

Whisperが生成したsegmentを基準として、複数segmentを一定文字数以下になる範囲でまとめて保存します。

## Stopping Transcription

処理中に「停止」ボタンを押すと、文字起こし処理を中断できます。

文字起こし結果は処理中にも逐次保存されるため、停止時点までに確定して保存された文章は `.txt` ファイルに残ります。

ただし、停止した瞬間にまだ確定していなかった文章については保存されない場合があります。

## FFmpeg

Whisperは音声ファイルの読み込みにFFmpegを使用します。

TranscribeではFFmpegを配布ZIPへ直接同梱せず、必要になった際に以下のBtbN/FFmpeg-Buildsから取得します。

- Windows x86_64
- LGPL build
- static build

ダウンロードしたZIPのSHA-256は、同じBtbNリリースで公開されている `checksums.sha256` と照合してから使用します。

Transcribeが取得したFFmpegは、Transcribe専用の保存領域に配置されます。

システム全体のFFmpegやWindowsのPATH設定は変更しません。

## Development

ソースコードから実行する場合は、Python環境を用意してください。

このプロジェクトのWindows配布版はPython 3.14環境でビルドしています。

### Clone

```powershell
git clone https://github.com/Ryosuke-Sata/transcribe.git
cd transcribe
```

開発中の最新版を利用する場合:

```powershell
git switch develop
```

### Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Runtime Dependencies

```powershell
pip install -r requirements.txt
```

現在、Whisperは以下のバージョンに固定しています。

```text
openai-whisper==20250625
```

このプロジェクトではWhisper内部のsegment生成状況を監視して進捗・逐次保存を行っているため、Whisperの内部実装変更による影響を避ける目的でバージョンを固定しています。

### Run

```powershell
python .\transcribe.py
```

## Building the Windows Application

PyInstallerをインストールします。

```powershell
pip install -r requirements-build.txt
```

Windows配布版をビルドします。

```powershell
pyinstaller --clean --noconfirm transcribe.spec
```

ビルドに成功すると、以下に配布用フォルダが生成されます。

```text
dist\Transcribe\
```

実行ファイルは、

```text
dist\Transcribe\Transcribe.exe
```

です。

## Third-Party Licenses

TranscribeのWindows配布版には、Python、OpenAI Whisper、PyTorch、NumPy、tiktokenなどの第三者ソフトウェアが含まれています。

使用している第三者ソフトウェアとライセンスの概要については、

```text
THIRD_PARTY_NOTICES.txt
```

を参照してください。

配布ZIPには、各ソフトウェアから収集したライセンス・Noticeファイルを、

```text
third_party_licenses/
```

として同梱します。

### FFmpeg

FFmpeg本体はTranscribeの配布ZIPには含まれていません。

必要になった場合にBtbN/FFmpeg-BuildsからLGPL版を取得し、独立した実行ファイルとして使用します。

FFmpegはTranscribeとは別のライセンス条件に従います。

## Generating Third-Party License Files

リリース用の第三者ライセンス情報は、ビルドに使用する仮想環境から生成できます。

```powershell
python .\collect_licenses.py
```

以下が生成されます。

```text
THIRD_PARTY_NOTICES.txt
third_party_licenses/
```

`THIRD_PARTY_NOTICES.txt` はGitで管理します。

`third_party_licenses/` は生成物のためGitでは管理せず、Windows配布ZIPへ含めます。

## Release Archive

配布フォルダへライセンス情報をコピーします。

```powershell
Copy-Item `
    .\THIRD_PARTY_NOTICES.txt `
    .\dist\Transcribe\ `
    -Force

Copy-Item `
    .\third_party_licenses `
    .\dist\Transcribe\third_party_licenses `
    -Recurse `
    -Force
```

その後、配布フォルダをZIP化します。

```powershell
Compress-Archive `
    -Path .\dist\Transcribe\* `
    -DestinationPath .\Transcribe-v1.0.0-win-x64.zip `
    -Force
```

生成したZIPはGitリポジトリにはコミットせず、GitHub Releasesから配布します。

## License

Transcribe is licensed under the MIT License.

See [LICENSE](LICENSE) for details.

Third-party software used by Transcribe is subject to its own
license terms. See [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)
for details.