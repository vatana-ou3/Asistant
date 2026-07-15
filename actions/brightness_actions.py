from __future__ import annotations

from assistant.models import ActionResult, Intent


class BrightnessActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def set_brightness(self, intent: Intent) -> ActionResult:
        level = intent.parameters["level"]
        if self.dry_run:
            return ActionResult(True, f"Would set brightness to {level} percent.")

        try:
            import screen_brightness_control as sbc

            sbc.set_brightness(level)
        except Exception as exc:
            return ActionResult(False, f"Brightness control failed: {exc}")
        return ActionResult(True, f"Brightness set to {level} percent.")

    def adjust_brightness(self, intent: Intent) -> ActionResult:
        delta = intent.parameters["delta"]
        if self.dry_run:
            return ActionResult(True, f"Would adjust brightness by {delta} percent.")

        try:
            import screen_brightness_control as sbc

            current_values = sbc.get_brightness()
            current = current_values[0] if isinstance(current_values, list) else int(current_values)
            sbc.set_brightness(max(0, min(100, current + delta)))
        except Exception as exc:
            return ActionResult(False, f"Brightness adjustment failed: {exc}")
        return ActionResult(True, "Brightness adjusted.")
