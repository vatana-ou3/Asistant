from __future__ import annotations

import sys
from types import SimpleNamespace

from actions.mouse_actions import MouseActions
from assistant.models import Intent


def test_scroll_down_uses_active_window_page_key(monkeypatch) -> None:
    pressed = []
    monkeypatch.setitem(sys.modules, "pyautogui", SimpleNamespace(press=pressed.append))

    result = MouseActions().scroll(Intent(action="scroll", target="down", parameters={"amount": -1}))

    assert result.success
    assert pressed == ["pagedown"]


def test_scroll_up_uses_active_window_page_key(monkeypatch) -> None:
    pressed = []
    monkeypatch.setitem(sys.modules, "pyautogui", SimpleNamespace(press=pressed.append))

    result = MouseActions().scroll(Intent(action="scroll", target="up", parameters={"amount": 1}))

    assert result.success
    assert pressed == ["pageup"]
