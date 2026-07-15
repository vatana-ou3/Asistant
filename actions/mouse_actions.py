from __future__ import annotations

from assistant.models import ActionResult, Intent


class MouseActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def scroll(self, intent: Intent) -> ActionResult:
        amount = intent.parameters.get("amount", 0)
        if self.dry_run:
            direction = "down" if amount < 0 else "up"
            return ActionResult(True, f"Would scroll {direction}.")

        try:
            import pyautogui

            pyautogui.scroll(amount)
        except Exception as exc:
            return ActionResult(False, f"Scroll failed: {exc}")
        return ActionResult(True, "Scrolled.")

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
