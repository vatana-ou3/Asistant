from __future__ import annotations

import base64
import re
import subprocess
import sys


class Speaker:
    def __init__(self, rate: int = 185, volume: float = 1.0, engine=None) -> None:
        self.rate = rate
        self.volume = volume
        self._engine = engine
        self._windows_fallback = False

    def prepare(self) -> None:
        if self._engine is not None or self._windows_fallback:
            return

        # System.Speech is more reliable than pyttsx3's long-running SAPI event
        # loop for the minimized wake-word process on Windows.
        if sys.platform == "win32":
            self._windows_fallback = True
            return

        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
        except Exception as exc:
            raise RuntimeError(
                "Speech output needs a working pyttsx3 installation."
            ) from exc

    def speak(self, text: str) -> None:
        spoken_text = self._clean_text(text)
        if not spoken_text:
            return

        self.prepare()
        if self._windows_fallback:
            self._speak_with_windows(spoken_text)
        else:
            self._engine.say(spoken_text)
            self._engine.runAndWait()

    def _speak_with_windows(self, text: str) -> None:
        text64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        script = (
            "Add-Type -AssemblyName System.Speech;"
            f"$t=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{text64}'));"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$s.Rate={max(-10, min(10, round((self.rate - 185) / 15)))};"
            f"$s.Volume={max(0, min(100, round(self.volume * 100)))};"
            "$s.Speak($t);$s.Dispose()"
        )
        encoded_script = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded_script],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or "unknown Windows speech error"
            raise RuntimeError(detail)

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"```.*?```", " Code omitted. ", text, flags=re.DOTALL)
        text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
        text = re.sub(r"https?://\S+", "link", text)
        text = re.sub(r"[*_`#>]", "", text)
        return re.sub(r"\s+", " ", text).strip()
