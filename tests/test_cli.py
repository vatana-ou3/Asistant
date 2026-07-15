from __future__ import annotations

from io import StringIO

from rich.console import Console

from interface.cli import AssistantCLI


def test_cli_renders_identity_user_and_markdown_response() -> None:
    output = StringIO()
    console = Console(file=output, color_system=None, width=60)
    cli = AssistantCLI("Ah Mark", "local-model", console=console)

    cli.show_header()
    cli.run_command(
        "What is Python?",
        lambda command: "Python is **readable**.",
        lambda command: False,
    )

    rendered = output.getvalue()
    assert "AH MARK" in rendered
    assert "What is Python?" in rendered
    assert "Python is readable." in rendered
