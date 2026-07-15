from __future__ import annotations

from collections.abc import Callable
from contextlib import nullcontext

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text


class AssistantCLI:
    def __init__(self, assistant_name: str, model_name: str, console: Console | None = None) -> None:
        self.assistant_name = assistant_name
        self.model_name = model_name
        self.console = console or Console()

    def show_header(self) -> None:
        identity = Text()
        identity.append(self.assistant_name.upper(), style="bold cyan")
        identity.append("\nLocal desktop assistant", style="white")
        identity.append(f"  |  {self.model_name}", style="dim")
        self.console.print(Panel.fit(identity, border_style="cyan", padding=(0, 2)))

    def loading_status(self, message: str):
        if not self.console.is_terminal:
            return nullcontext()
        return self.console.status(f"[cyan]{message}[/cyan]", spinner="dots")

    def run_command(
        self,
        command: str,
        handler: Callable[[str], str],
        is_desktop_command: Callable[[str], bool],
        show_user: bool = True,
    ) -> str:
        if show_user:
            self.console.print()
            self.console.print(Text("You", style="bold green"))
            self.console.print(Text(command))

        status = "Working..." if is_desktop_command(command) else "Thinking..."
        with self.loading_status(status):
            response = handler(command)

        self.console.print()
        self.console.print(Rule(Text(self.assistant_name, style="bold cyan"), style="cyan"))
        self.console.print(Markdown(response))
        self.console.print()
        return response

    def interactive(
        self,
        handler: Callable[[str], str],
        is_desktop_command: Callable[[str], bool],
    ) -> int:
        self.console.print("[dim]Type a message. Use 'quit' to exit.[/dim]")
        while True:
            try:
                command = Prompt.ask("[bold green]You[/bold green]", console=self.console).strip()
            except (EOFError, KeyboardInterrupt):
                self.console.print()
                return 0

            if command.lower() in {"quit", "exit"}:
                return 0
            if not command:
                continue
            self.run_command(command, handler, is_desktop_command, show_user=False)
