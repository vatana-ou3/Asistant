from __future__ import annotations

from assistant.models import ActionResult


class WindowActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def minimize_active(self) -> ActionResult:
        return ActionResult(False, "Window management is planned for the next phase.")
