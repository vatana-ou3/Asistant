from __future__ import annotations

import json
from pathlib import Path


class WakeWordDetector:
    def __init__(self, model_path: Path, wake_phrase: str = "hey bro", sample_rate: int = 16000) -> None:
        self.model_path = Path(model_path)
        self.wake_phrase = self._normalize(wake_phrase)
        self.sample_rate = sample_rate
        self._model = None

    def prepare(self) -> None:
        if self._model is not None:
            return
        if not self.model_path.exists():
            raise RuntimeError(f"Vosk wake-word model was not found at {self.model_path}.")

        try:
            from vosk import Model, SetLogLevel
        except ModuleNotFoundError as exc:
            raise RuntimeError("Wake-word mode needs Vosk. Run: pip install -r requirements.txt") from exc

        SetLogLevel(-1)
        self._model = Model(str(self.model_path))

    def listen(self) -> bool:
        self.prepare()
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer
        except ModuleNotFoundError as exc:
            raise RuntimeError("Wake-word mode needs Vosk and sounddevice.") from exc

        phrases = [self.wake_phrase, "[unk]"]
        recognizer = KaldiRecognizer(self._model, self.sample_rate, json.dumps(phrases))
        block_frames = 4000

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=block_frames,
            dtype="int16",
            channels=1,
        ) as stream:
            while True:
                audio, _overflowed = stream.read(block_frames)
                if recognizer.AcceptWaveform(bytes(audio)):
                    text = json.loads(recognizer.Result()).get("text", "")
                else:
                    text = json.loads(recognizer.PartialResult()).get("partial", "")
                if self.matches_wake_phrase(text):
                    return True

    def matches_wake_phrase(self, text: str) -> bool:
        normalized = self._normalize(text)
        return self.wake_phrase in normalized

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().strip().split())
