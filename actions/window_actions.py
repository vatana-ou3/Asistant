from __future__ import annotations

from assistant.models import ActionResult, Intent


class WindowActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def maximize(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would maximize the active window.")
        return self._change_window("maximize", "Maximized the active window.")

    def restore(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would restore the active window.")
        return self._change_window("restore", "Restored the active window.")

    @staticmethod
    def _change_window(operation: str, success_message: str) -> ActionResult:
        try:
            import pygetwindow

            window = pygetwindow.getActiveWindow()
            if window is None:
                return ActionResult(False, "No active window was found.")
            getattr(window, operation)()
        except Exception as exc:
            return ActionResult(False, f"Window control failed: {exc}")
        return ActionResult(True, success_message)
