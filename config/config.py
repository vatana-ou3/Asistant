from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    assistant_name: str
    wake_word: str
    log_file: Path
    default_browser: str | None = None
    speech_enabled: bool = False
    speech_rate: int = 185
    ollama_model: str = "frob/qwen3.5-instruct:4b"
    ollama_url: str = "http://127.0.0.1:11434"


@dataclass(frozen=True)
class AppConfig:
    settings: Settings
    applications: dict[str, str]
    commands: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_config() -> AppConfig:
    settings_data = _read_json(PROJECT_ROOT / "config" / "settings.json")
    applications = _read_json(PROJECT_ROOT / "config" / "applications.json")
    commands = _read_json(PROJECT_ROOT / "config" / "commands.json")

    log_file = PROJECT_ROOT / settings_data.get("log_file", "logs/assistant.log")
    settings = Settings(
        assistant_name=settings_data.get("assistant_name", "Ah Mark"),
        wake_word=settings_data.get("wake_word", "hey ah mark"),
        log_file=log_file,
        default_browser=settings_data.get("default_browser"),
        speech_enabled=bool(settings_data.get("speech_enabled", False)),
        speech_rate=int(settings_data.get("speech_rate", 185)),
        ollama_model=settings_data.get("ollama_model", "frob/qwen3.5-instruct:4b"),
        ollama_url=settings_data.get("ollama_url", "http://127.0.0.1:11434"),
    )
    return AppConfig(settings=settings, applications=applications, commands=commands)
