from __future__ import annotations

from audio.speaker import Speaker


class FakeEngine:
    def __init__(self) -> None:
        self.spoken = []
        self.ran = False

    def say(self, text: str) -> None:
        self.spoken.append(text)

    def runAndWait(self) -> None:
        self.ran = True


def test_speaker_cleans_and_speaks_response() -> None:
    engine = FakeEngine()
    speaker = Speaker(engine=engine)

    speaker.speak("**Hello!** See [the docs](https://example.com).")

    assert engine.spoken == ["Hello! See the docs."]
    assert engine.ran


def test_speaker_ignores_empty_text() -> None:
    engine = FakeEngine()
    Speaker(engine=engine).speak("  ")
    assert engine.spoken == []
