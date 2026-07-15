from __future__ import annotations

import threading

from assistant.models import ActionResult, Intent


class ContinuousScroller:
    def __init__(self, interval_seconds: float = 0.04, scroll_step: int = 11) -> None:
        self.interval_seconds = interval_seconds
        self.scroll_step = scroll_step
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self, direction: str, pyautogui_module) -> None:
        self.stop()
        with self._lock:
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=self._run,
                args=(direction, pyautogui_module, self._stop_event),
                daemon=True,
                name="ahmark-continuous-scroll",
            )
            self._thread.start()

    def stop(self) -> bool:
        with self._lock:
            thread = self._thread
            if thread is None or not thread.is_alive():
                self._thread = None
                return False
            self._stop_event.set()
        thread.join(timeout=1)
        with self._lock:
            self._thread = None
        return True

    def _run(self, direction: str, pyautogui_module, stop_event: threading.Event) -> None:
        amount = -self.scroll_step if direction == "down" else self.scroll_step
        while not stop_event.is_set():
            pyautogui_module.scroll(amount)
            stop_event.wait(self.interval_seconds)


_SCROLLER = ContinuousScroller()


class MouseActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def scroll(self, intent: Intent) -> ActionResult:
        amount = intent.parameters.get("amount", 0)
        direction = intent.target or ("down" if amount < 0 else "up")
        if self.dry_run:
            return ActionResult(True, f"Would scroll {direction}.")

        try:
            import pyautogui

            _SCROLLER.start(direction, pyautogui)
        except Exception as exc:
            return ActionResult(False, f"Scroll failed: {exc}")
        return ActionResult(True, f"Scrolling {direction}.")

    def stop_scroll(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would stop scrolling.")
        if _SCROLLER.stop():
            return ActionResult(True, "Stopped scrolling.")
        return ActionResult(True, "Scrolling is already stopped.")

    def click(self, intent: Intent) -> ActionResult:
        button = intent.target or "left"
        if self.dry_run:
            return ActionResult(True, f"Would {button}-click.")

        try:
            import pyautogui

            pyautogui.click(button=button)
        except Exception as exc:
            return ActionResult(False, f"Click failed: {exc}")
        return ActionResult(True, f"{button.title()} click.")

    def double_click(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would double-click.")

        try:
            import pyautogui

            pyautogui.doubleClick()
        except Exception as exc:
            return ActionResult(False, f"Double-click failed: {exc}")
        return ActionResult(True, "Double-clicked.")
