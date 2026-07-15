from __future__ import annotations

from pathlib import Path

import stop_ahmark


def test_identifies_project_wake_process() -> None:
    assert stop_ahmark.is_ahmark_wake_process(
        ["python.exe", str(Path(stop_ahmark.APP_PATH)), "--wake-word"]
    )


def test_rejects_non_wake_process() -> None:
    assert not stop_ahmark.is_ahmark_wake_process(["python.exe", str(Path(stop_ahmark.APP_PATH)), "--voice"])


def test_rejects_unrelated_wake_process() -> None:
    assert not stop_ahmark.is_ahmark_wake_process(["python.exe", "C:\\other\\app.py", "--wake-word"])
