from __future__ import annotations

import app


class FakeConversation:
    def __init__(self) -> None:
        self.prompts = []

    def reply(self, text: str) -> str:
        self.prompts.append(text)
        return "Hello from Qwen."


def test_unknown_input_routes_to_conversation() -> None:
    conversation = FakeConversation()

    result = app.handle_command("How are you today?", dry_run=True, conversation=conversation)

    assert result == "Hello from Qwen."
    assert conversation.prompts == ["How are you today?"]


def test_dangerous_action_does_not_route_to_conversation() -> None:
    conversation = FakeConversation()

    result = app.handle_command("shutdown computer", dry_run=True, conversation=conversation)

    assert "disabled" in result
    assert conversation.prompts == []


def test_desktop_command_is_identified_for_follow_up_prompt() -> None:
    assert app.is_desktop_command("open chrome")
    assert app.is_desktop_command("team")
    assert not app.is_desktop_command("how are you")
