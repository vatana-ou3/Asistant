from __future__ import annotations

from pathlib import Path

from audio.wake_word import WakeWordDetector


def detector() -> WakeWordDetector:
    return WakeWordDetector(Path("unused-model"), "hey bro")


def test_matches_configured_wake_phrase() -> None:
    assert detector().matches_wake_phrase("hey bro")


def test_rejects_old_wake_phrase() -> None:
    assert not detector().matches_wake_phrase("hey ah mark")


def test_rejects_unrelated_speech() -> None:
    assert not detector().matches_wake_phrase("open youtube")
