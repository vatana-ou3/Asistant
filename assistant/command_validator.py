from __future__ import annotations

from assistant.models import Intent, ValidationResult


class CommandValidator:
    _allowed_actions = {
        "open_application",
        "open_website",
        "search_web",
        "keyboard_shortcut",
        "press_key",
        "scroll",
        "mouse_click",
        "mouse_double_click",
        "set_volume",
        "adjust_volume",
        "mute_volume",
        "set_brightness",
        "adjust_brightness",
        "lock_computer",
    }

    def validate(self, intent: Intent) -> ValidationResult:
        if intent.action == "unknown":
            return ValidationResult(False, "I did not understand that command.")

        if intent.action == "dangerous_system_action":
            return ValidationResult(False, "That action requires explicit confirmation and is disabled in this MVP.")

        if intent.action not in self._allowed_actions:
            return ValidationResult(False, f"Action '{intent.action}' is not allowed.")

        if intent.action in {"set_volume", "set_brightness"}:
            level = intent.parameters.get("level")
            if not isinstance(level, int) or level < 0 or level > 100:
                return ValidationResult(False, "The level must be between 0 and 100.")

        if intent.action in {"adjust_volume", "adjust_brightness"}:
            delta = intent.parameters.get("delta")
            if not isinstance(delta, int) or delta < -100 or delta > 100:
                return ValidationResult(False, "The adjustment must be between -100 and 100.")

        if intent.action == "search_web" and not intent.parameters.get("query"):
            return ValidationResult(False, "Search commands need a query.")

        return ValidationResult(True)
