from __future__ import annotations

from interface.tray import TrayController


def test_tray_pause_and_resume_toggle_listening() -> None:
    tray = TrayController("Ah Mark")

    assert tray.listening_enabled.is_set()
    tray._pause()
    assert not tray.listening_enabled.is_set()
    tray._resume()
    assert tray.listening_enabled.is_set()


def test_tray_icon_has_expected_size() -> None:
    assert TrayController._create_icon(active=True).size == (64, 64)
