from __future__ import annotations

import sys
from types import SimpleNamespace

from actions.window_actions import WindowActions
from assistant.models import Intent


class FakeWindow:
    def __init__(self) -> None:
        self.maximized = False
        self.restored = False

    def maximize(self) -> None:
        self.maximized = True

    def restore(self) -> None:
        self.restored = True


def test_maximizes_active_window(monkeypatch) -> None:
    window = FakeWindow()
    monkeypatch.setitem(sys.modules, "pygetwindow", SimpleNamespace(getActiveWindow=lambda: window))

    result = WindowActions().maximize(Intent(action="maximize_window"))

    assert result.success
    assert window.maximized


def test_restores_active_window(monkeypatch) -> None:
    window = FakeWindow()
    monkeypatch.setitem(sys.modules, "pygetwindow", SimpleNamespace(getActiveWindow=lambda: window))

    result = WindowActions().restore(Intent(action="restore_window"))

    assert result.success
    assert window.restored
