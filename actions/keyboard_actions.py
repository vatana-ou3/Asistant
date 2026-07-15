from __future__ import annotations

from assistant.models import ActionResult, Intent


class KeyboardActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def shortcut(self, intent: Intent) -> ActionResult:
        keys = intent.parameters.get("keys", [])
        if not keys:
            return ActionResult(False, "No keys were configured for that shortcut.")
        if self.dry_run:
            return ActionResult(True, f"Would press {'+'.join(keys)}.")

        try:
            import pyautogui

            pyautogui.hotkey(*keys)
        except Exception as exc:
            return ActionResult(False, f"Keyboard shortcut failed: {exc}")
        return ActionResult(True, f"Pressed {'+'.join(keys)}.")

    def press_key(self, intent: Intent) -> ActionResult:
        key = intent.target
        if not key:
            return ActionResult(False, "No key was specified.")
        if self.dry_run:
            return ActionResult(True, f"Would press {key}.")

        try:
            import pyautogui

            pyautogui.press(key)
        except Exception as exc:
            return ActionResult(False, f"Key press failed: {exc}")
        return ActionResult(True, f"Pressed {key}.")
