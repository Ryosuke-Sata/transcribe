# Transcribe

OpenAI Whisperを利用した、Windows向けのローカル文字起こしアプリケーションです。

GUIから音声・動画ファイルを選択し、Whisperモデルと言語を指定して文字起こしできます。

文字起こし処理はローカルPC上で実行され、音声データを外部の文字起こしAPIへ送信する必要はありません。

## Features

- GUIによる音声・動画ファイル選択
- 動画から音声のみを抽出して文字起こし
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

## Supported Audio / Video Formats

以下の音声ファイルをGUIから選択できます。

- `.m4a`
- `.mp3`
- `.wav`
- `.flac`
- `.aac`
- `.ogg`
- `.wma`

以下の動画ファイルもGUIから選択できます。

- `.mp4`, `.m4v`, `.mov`, `.mkv`, `.avi`, `.webm`, `.wmv`
- `.flv`, `.mpg`, `.mpeg`, `.ts`, `.mts`, `.m2ts`, `.3gp`

動画はFFmpegで最初の音声トラックのみを16kHz・モノラルに変換して文字起こしします。映像は処理せず、抽出した音声の中間ファイルも保存しません。音声トラックが複数ある場合は最初のトラックを使用します。音声トラックがない動画はエラーとして通知し、次のファイルの処理へ進みます。

実際に読み込めるコーデックは使用するFFmpegに依存します。

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
├─ LICENSE
├─ README.md
├─ BUILD_DEPENDENCIES.txt
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

### 4. 音声・動画ファイルを選択

「音声・動画ファイルを選択」ボタンから文字起こしするファイルを選択します。

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

文字起こし結果は、元の音声・動画ファイルと同じフォルダに保存されます。

例えば、

```text
lecture.mp4
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

音声・動画ファイルの音声読み込みにはFFmpegを使用します。

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

## Automated Build and Release

GitHub Actionsの `.github/workflows/release.yml` がWindows x64版を自動ビルドします。

| 操作 | 実行内容 |
| --- | --- |
| `develop` / `main` へのpush、これらを対象とするPR | テスト・EXEビルド・起動確認・ZIP作成。成果物はActionsからダウンロード可能 |
| `v1.1.0` などのタグをpush | 上記の確認に成功した後、GitHub Releaseと配布ZIP・SHA-256を自動公開 |
| `v1.1.0-rc.1` などのタグをpush | プレリリースとして自動公開 |
| Actionsの「Run workflow」 | ビルド確認のみ。リリースは公開しない |

タグは `vX.Y.Z` または `vX.Y.Z-alpha.N` / `-beta.N` / `-rc.N` 形式です。タグが指すコミットのソースをビルドします。ワークフローファイルを含むコミットにタグを付けてください。

例えば、動画対応を含む版を `v1.1.0` として公開する場合:

```powershell
git switch develop
git pull --ff-only origin develop
git tag -a v1.1.0 -m "Transcribe v1.1.0"
git push origin v1.1.0
```

これ以降のビルド・ライセンス収集・圧縮・リリースノート生成・公開は自動です。新しいリリースには毎回新しいタグを使用してください。既存の公開済みリリースや添付ファイルは上書きしません。失敗した実行はActionsから再実行できますが、既に公開済みのタグで公開処理を再実行すると失敗します。

Python 3.14・PyInstallerを使い、配布容量を抑えるためPyTorchはCPU版をインストールします。モデルとFFmpegは従来どおり初回利用時に取得し、ZIPには含めません。CIの音声抽出テストで使うFFmpegも配布物へは同梱しません。

ZIPには本体と実行環境のほか、MITの `LICENSE`、`THIRD_PARTY_NOTICES.txt`、`third_party_licenses/`、実際のビルド環境の依存バージョン一覧 `BUILD_DEPENDENCIES.txt` が入ります。ライセンス収集は `--strict` で実行し、収集対象のライセンスが見つからなければ公開しません。

公開処理は標準の `GITHUB_TOKEN` を使用するため、追加の個人アクセストークンは不要です。リポジトリでGitHub Actionsの実行が許可されている必要があります。「Run workflow」を使うには、このワークフローをデフォルトブランチ（`main`）にも反映してください。

## Manual Release Archive

ローカルでビルド済みの `dist/Transcribe` から配布ZIPを作る場合:

```powershell
python .\collect_licenses.py --strict
python .\scripts\package_release.py --version v1.1.0
```

`release/Transcribe-v1.1.0-win-x64.zip` と対応する `.zip.sha256` が生成されます。ZIP内部も検証してから出力します。生成物はGitへコミットしません。

## License

Transcribe is licensed under the MIT License.

See [LICENSE](LICENSE) for details.

Third-party software used by Transcribe is subject to its own
license terms. See [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)
for details.
