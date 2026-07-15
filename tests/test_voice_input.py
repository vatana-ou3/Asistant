from __future__ import annotations

import sys
import threading
from types import SimpleNamespace

import numpy as np

import app
from audio.recorder import AudioRecorder, AudioRecording
from audio.speech_detector import SpeechDetector
from audio.transcriber import Transcriber


def test_speech_detector_rejects_silence() -> None:
    recording = AudioRecording(samples=np.zeros((160, 1), dtype=np.float32), sample_rate=16000)
    assert not SpeechDetector().contains_speech(recording)


def test_speech_detector_accepts_audio_above_threshold() -> None:
    recording = AudioRecording(samples=np.full((160, 1), 0.001, dtype=np.float32), sample_rate=16000)
    assert SpeechDetector().contains_speech(recording)


def test_process_voice_command_transcribes_and_handles_command(monkeypatch) -> None:
    recording = AudioRecording(samples=np.full((160, 1), 0.05, dtype=np.float32), sample_rate=16000)

    class Recorder:
        def record_command(self, duration_seconds):
            assert duration_seconds == 3
            return recording

    class Transcriber:
        def transcribe(self, audio):
            assert audio is recording
            return "open chrome"

    monkeypatch.setattr(
        app,
        "handle_command",
        lambda command, dry_run, conversation=None: f"handled {command} {dry_run}",
    )

    result = app.process_voice_command(Recorder(), SpeechDetector(), Transcriber(), 3, dry_run=True)
    assert result == "handled open chrome True"


def test_process_voice_command_does_not_transcribe_silence() -> None:
    recording = AudioRecording(samples=np.zeros((160, 1), dtype=np.float32), sample_rate=16000)

    class Recorder:
        def record_command(self, duration_seconds):
            return recording

    class Transcriber:
        def transcribe(self, audio):
            raise AssertionError("Silence should not be transcribed")

    result = app.process_voice_command(Recorder(), SpeechDetector(), Transcriber(), 1)
    assert result == "I did not hear any speech (microphone level: 0.000000)."


def test_recorder_stops_after_post_speech_silence(monkeypatch) -> None:
    block_frames = 800
    blocks = [np.zeros((block_frames, 1), dtype=np.float32) for _ in range(3)]
    blocks.extend(np.full((block_frames, 1), 0.05, dtype=np.float32) for _ in range(4))
    blocks.extend(np.zeros((block_frames, 1), dtype=np.float32) for _ in range(10))
    reads = 0

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, frames):
            nonlocal reads
            block = blocks[min(reads, len(blocks) - 1)]
            reads += 1
            return block, False

    fake_sounddevice = SimpleNamespace(InputStream=lambda **kwargs: FakeStream())
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sounddevice)

    recording = AudioRecorder().record_command(duration_seconds=5)

    assert reads == 17
    assert len(recording.samples) == reads * block_frames
    assert recording.speech_detected


def test_recorder_stops_when_listening_is_paused(monkeypatch) -> None:
    reads = 0
    listening_enabled = threading.Event()
    listening_enabled.set()

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, frames):
            nonlocal reads
            reads += 1
            listening_enabled.clear()
            return np.zeros((frames, 1), dtype=np.float32), False

    fake_sounddevice = SimpleNamespace(InputStream=lambda **kwargs: FakeStream())
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sounddevice)

    recording = AudioRecorder().record_command(
        duration_seconds=10,
        cancellation_event=listening_enabled,
    )

    assert reads == 1
    assert not recording.speech_detected


def test_transcriber_forces_english_and_uses_command_prompt() -> None:
    captured = {}

    class Model:
        def transcribe(self, path, **kwargs):
            captured.update(kwargs)
            return [SimpleNamespace(text=" Open YouTube ")], None

    transcriber = Transcriber()
    transcriber._model = Model()
    recording = AudioRecording(samples=np.zeros((160, 1), dtype=np.float32), sample_rate=16000)

    assert transcriber.transcribe(recording) == "Open YouTube"
    assert captured["language"] == "en"
    assert "YouTube" in captured["hotwords"]
    assert captured["max_new_tokens"] == 64
