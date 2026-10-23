"""Video/audio extraction tests. Run: python -m unittest discover -s tests -v

Whisper is stubbed when importing the loader; no model download is required.
FFmpeg integration tests use generated fixtures in a temporary directory.
"""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
whisper_stub = types.ModuleType("whisper")
audio_stub = types.ModuleType("whisper.audio")
audio_stub.SAMPLE_RATE = 16000
audio_stub.HOP_LENGTH = 160
observer_stub = types.ModuleType("whisper_observer")
observer_stub.WhisperTranscribeObserver = object
spec = importlib.util.spec_from_file_location(
    "_media_test_transcriber", ROOT / "transcriber.py"
)
module = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {
    "whisper": whisper_stub,
    "whisper.audio": audio_stub,
    "whisper_observer": observer_stub,
}):
    spec.loader.exec_module(module)
WhisperTranscriber = module.WhisperTranscriber


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
class MediaExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / "日本語 動画"
        self.directory.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def generate(self, name, *options):
        target = self.directory / name
        subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-y", *options, str(target)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return str(target)

    def test_video_formats_extract_audio(self):
        for extension, video_codec, audio_codec in [
            ("mp4", "mpeg4", "aac"),
            ("mov", "mpeg4", "aac"),
            ("mkv", "mpeg4", "aac"),
            ("avi", "mpeg4", "pcm_s16le"),
            ("webm", "libvpx", "libopus"),
        ]:
            with self.subTest(extension=extension):
                source = self.generate(
                    "録画." + extension,
                    "-f", "lavfi", "-i", "color=size=32x32:rate=5:duration=1",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
                    "-c:v", video_codec, "-c:a", audio_codec, "-shortest",
                )
                audio, duration = WhisperTranscriber.load_audio(source)
                self.assertEqual(audio.dtype, np.float32)
                self.assertEqual(audio.ndim, 1)
                self.assertAlmostEqual(duration, 1.0, delta=0.1)
                self.assertGreater(float(np.max(np.abs(audio))), 0.01)
                self.assertEqual(sorted(p.name for p in self.directory.iterdir()),
                                 ["録画." + extension])
                Path(source).unlink()

    def test_existing_audio_formats(self):
        for extension in ["wav", "mp3", "m4a"]:
            with self.subTest(extension=extension):
                source = self.generate(
                    "音声." + extension,
                    "-f", "lavfi", "-i", "sine=duration=1:sample_rate=44100",
                    "-ac", "2",
                )
                audio, duration = WhisperTranscriber.load_audio(source)
                self.assertEqual(audio.ndim, 1)
                self.assertAlmostEqual(duration, 1.0, delta=0.1)

    def test_first_audio_track_is_selected(self):
        source = self.generate(
            "複数音声.mkv",
            "-f", "lavfi", "-i", "color=size=32x32:duration=1",
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo:d=1",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=1",
            "-map", "0:v", "-map", "1:a", "-map", "2:a",
            "-c:v", "mpeg4", "-c:a", "pcm_s16le",
            "-disposition:a:0", "0", "-disposition:a:1", "default",
        )
        audio, _ = WhisperTranscriber.load_audio(source)
        self.assertEqual(float(np.max(np.abs(audio))), 0.0)

    def test_video_without_audio_reports_clear_error(self):
        source = self.generate(
            "映像のみ.mp4",
            "-f", "lavfi", "-i", "color=size=32x32:duration=1",
            "-c:v", "mpeg4",
        )
        with self.assertRaisesRegex(RuntimeError, "音声トラックがありません"):
            WhisperTranscriber.load_audio(source)

    def test_invalid_input(self):
        source = self.directory / "壊れた.mp4"
        source.write_bytes(b"invalid video")
        with self.assertRaisesRegex(RuntimeError, "音声.*読み込み"):
            WhisperTranscriber.load_audio(str(source))
        with self.assertRaises(FileNotFoundError):
            WhisperTranscriber.load_audio(str(self.directory / "missing.mp4"))


class FileSelectionTests(unittest.TestCase):
    def test_default_filter_includes_audio_and_video(self):
        from ui import TranscribeView
        filters = dict(TranscribeView.MEDIA_FILETYPES)
        for pattern in ["*.mp4", "*.mov", "*.mkv", "*.webm", "*.m4a", "*.mp3"]:
            self.assertIn(pattern, filters["音声・動画ファイル"].split())
        self.assertIn("動画ファイル", filters)


if __name__ == "__main__":
    unittest.main()
