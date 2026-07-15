from __future__ import annotations

import sys
import time
from types import SimpleNamespace

from actions.mouse_actions import MouseActions
from assistant.models import Intent


def test_scroll_down_runs_until_stopped(monkeypatch) -> None:
    scrolled = []
    monkeypatch.setitem(sys.modules, "pyautogui", SimpleNamespace(scroll=scrolled.append))

    result = MouseActions().scroll(Intent(action="scroll", target="down", parameters={"amount": -1}))
    deadline = time.monotonic() + 0.5
    while not scrolled and time.monotonic() < deadline:
        time.sleep(0.01)
    stopped = MouseActions().stop_scroll(Intent(action="stop_scroll"))

    assert result.success
    assert stopped.success
    assert scrolled
    assert all(amount == -1 for amount in scrolled)


def test_scroll_up_runs_until_stopped(monkeypatch) -> None:
    scrolled = []
    monkeypatch.setitem(sys.modules, "pyautogui", SimpleNamespace(scroll=scrolled.append))

    result = MouseActions().scroll(Intent(action="scroll", target="up", parameters={"amount": 1}))
    deadline = time.monotonic() + 0.5
    while not scrolled and time.monotonic() < deadline:
        time.sleep(0.01)
    MouseActions().stop_scroll(Intent(action="stop_scroll"))

    assert result.success
    assert scrolled
    assert all(amount == 1 for amount in scrolled)
