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
        assistant_name=settings_data.get("assistant_name", "Nova"),
        wake_word=settings_data.get("wake_word", "hey nova"),
        log_file=log_file,
        default_browser=settings_data.get("default_browser"),
        speech_enabled=bool(settings_data.get("speech_enabled", False)),
    )
    return AppConfig(settings=settings, applications=applications, commands=commands)
