from __future__ import annotations

from audio.recorder import AudioRecording


class SpeechDetector:
    def __init__(self, minimum_rms: float = 0.0001) -> None:
        self.minimum_rms = minimum_rms

    def contains_speech(self, audio: AudioRecording) -> bool:
        if audio.speech_detected is not None:
            return audio.speech_detected
        return self.input_level(audio) >= self.minimum_rms

    def input_level(self, audio: AudioRecording) -> float:
        try:
            import numpy as np
        except ModuleNotFoundError as exc:
            raise RuntimeError("Voice mode needs the 'numpy' package. Run: pip install -r requirements.txt") from exc

        samples = np.asarray(audio.samples, dtype=np.float32)
        if samples.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(samples))))
