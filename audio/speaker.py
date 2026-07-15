from __future__ import annotations

import re


class Speaker:
    def __init__(self, rate: int = 185, volume: float = 1.0, engine=None) -> None:
        self.rate = rate
        self.volume = volume
        self._engine = engine

    def prepare(self) -> None:
        if self._engine is not None:
            return

        try:
            import pyttsx3
        except ModuleNotFoundError as exc:
            raise RuntimeError("Speech output needs pyttsx3. Run: pip install -r requirements.txt") from exc

        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", self.rate)
        self._engine.setProperty("volume", self.volume)

    def speak(self, text: str) -> None:
        spoken_text = self._clean_text(text)
        if not spoken_text:
            return

        self.prepare()
        self._engine.say(spoken_text)
        self._engine.runAndWait()

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"```.*?```", " Code omitted. ", text, flags=re.DOTALL)
        text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
        text = re.sub(r"https?://\S+", "link", text)
        text = re.sub(r"[*_`#>]", "", text)
        return re.sub(r"\s+", " ", text).strip()
