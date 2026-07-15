from __future__ import annotations

import ctypes

from assistant.models import ActionResult, Intent


class SystemActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def lock_computer(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would lock the computer.")
        try:
            ctypes.windll.user32.LockWorkStation()
        except Exception as exc:
            return ActionResult(False, f"Could not lock the computer: {exc}")
        return ActionResult(True, "Computer locked.")
