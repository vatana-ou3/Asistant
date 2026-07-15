from __future__ import annotations


class SpeechDetector:
    def contains_speech(self, audio: bytes) -> bool:
        raise NotImplementedError("Voice activity detection will be added in Phase 2.")
