from __future__ import annotations

import tempfile
import wave
from pathlib import Path

from audio.recorder import AudioRecording


class Transcriber:
    def __init__(self, model_size: str = "tiny.en", device: str = "cpu", compute_type: str = "int8") -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def prepare(self) -> None:
        self._load_model()

    def transcribe(self, audio: AudioRecording) -> str:
        model = self._load_model()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            self._write_wav(temp_path, audio)
            segments, _info = model.transcribe(
                str(temp_path),
                language="en",
                beam_size=1,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 300},
                condition_on_previous_text=False,
                without_timestamps=True,
                max_new_tokens=64,
                hallucination_silence_threshold=1.0,
                hotwords="Chrome YouTube Google volume brightness copy paste Ah Mark",
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            temp_path.unlink(missing_ok=True)

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from faster_whisper import WhisperModel
        except ModuleNotFoundError as exc:
            raise RuntimeError("Voice mode needs the 'faster-whisper' package. Run: pip install -r requirements.txt") from exc

        self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    def _write_wav(self, path: Path, audio: AudioRecording) -> None:
        try:
            import numpy as np
        except ModuleNotFoundError as exc:
            raise RuntimeError("Voice mode needs the 'numpy' package. Run: pip install -r requirements.txt") from exc

        samples = np.asarray(audio.samples, dtype=np.float32)
        if samples.ndim > 1:
            samples = samples[:, 0]
        samples = np.clip(samples, -1.0, 1.0)
        pcm = (samples * 32767).astype(np.int16)

        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(audio.sample_rate)
            wav_file.writeframes(pcm.tobytes())
