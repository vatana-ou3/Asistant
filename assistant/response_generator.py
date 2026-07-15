from __future__ import annotations

from assistant.models import Intent


class ResponseGenerator:
    def success(self, intent: Intent, message: str) -> str:
        if message:
            return message
        if intent.target:
            return f"Done: {intent.action.replace('_', ' ')} {intent.target}."
        return f"Done: {intent.action.replace('_', ' ')}."

    def error(self, message: str) -> str:
        return message or "Something went wrong."
