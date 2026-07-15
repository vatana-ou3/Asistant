from __future__ import annotations

import re
from typing import Any

from assistant.models import Intent
from assistant.command_parser import normalize_command


class IntentDetector:
    def __init__(self, command_config: dict[str, Any]) -> None:
        self.command_config = command_config

    def detect(self, text: str) -> Intent:
        raw_text = text.strip()
        command = normalize_command(raw_text)

        if not command:
            return Intent(action="unknown", raw_text=raw_text)

        level_intent = self._detect_level_command(command, raw_text)
        if level_intent:
            return level_intent

        search_intent = self._detect_search(command, raw_text)
        if search_intent:
            return search_intent

        for phrase, shortcut in self.command_config.get("keyboard_shortcuts", {}).items():
            if command == phrase or command.startswith(f"{phrase} "):
                return Intent(action="keyboard_shortcut", target=phrase, parameters={"keys": shortcut}, raw_text=raw_text)

        websites = self.command_config.get("websites", {})
        for site_name, url in websites.items():
            if re.search(rf"\b(open|go to|launch|start)\s+{re.escape(site_name)}\b", command):
                return Intent(action="open_website", target=site_name, parameters={"url": url}, raw_text=raw_text)

        if command in websites:
            return Intent(
                action="open_website",
                target=command,
                parameters={"url": websites[command]},
                raw_text=raw_text,
            )

        applications = self.command_config.get("applications", {})
        if command in applications:
            return Intent(action="open_application", target=command, raw_text=raw_text)

        screenshot_match = re.match(
            r"^(take|make|start)\s+(a\s+)?(screenshot|screen shot|snip|screen capture)$",
            command,
        )
        if screenshot_match:
            return Intent(action="open_application", target="snipping tool", raw_text=raw_text)

        app_match = re.match(r"^(open|launch|start|run)\s+(?P<target>.+)$", command)
        if app_match:
            return Intent(action="open_application", target=app_match.group("target"), raw_text=raw_text)

        if command in {"scroll down", "scrolling down", "go down", "page down"}:
            return Intent(action="scroll", target="down", parameters={"amount": -1}, raw_text=raw_text)
        if command in {"scroll up", "scrolling up", "go up", "page up"}:
            return Intent(action="scroll", target="up", parameters={"amount": 1}, raw_text=raw_text)
        if command in {"stop", "stop scroll", "stop scrolling"}:
            return Intent(action="stop_scroll", raw_text=raw_text)
        if command in {"click", "left click"}:
            return Intent(action="mouse_click", target="left", raw_text=raw_text)
        if command in {"double click", "double-click"}:
            return Intent(action="mouse_double_click", target="left", raw_text=raw_text)
        if command in {"right click", "right-click"}:
            return Intent(action="mouse_click", target="right", raw_text=raw_text)

        if command in {"press enter", "enter"}:
            return Intent(action="press_key", target="enter", raw_text=raw_text)
        if command in {"press escape", "escape", "esc"}:
            return Intent(action="press_key", target="esc", raw_text=raw_text)

        if command in {"fullscreen", "full screen", "maximize", "maximize window", "maximize the window"}:
            return Intent(action="maximize_window", raw_text=raw_text)
        if command in {"smallscreen", "small screen", "restore", "restore window", "restore the window"}:
            return Intent(action="restore_window", raw_text=raw_text)

        if command in {"mute", "mute audio", "mute volume"}:
            return Intent(action="mute_volume", raw_text=raw_text)
        if command in {"increase volume", "volume up"}:
            return Intent(action="adjust_volume", parameters={"delta": 10}, raw_text=raw_text)
        if command in {"decrease volume", "volume down"}:
            return Intent(action="adjust_volume", parameters={"delta": -10}, raw_text=raw_text)

        if command in {"increase brightness", "brightness up"}:
            return Intent(action="adjust_brightness", parameters={"delta": 10}, raw_text=raw_text)
        if command in {"decrease brightness", "brightness down"}:
            return Intent(action="adjust_brightness", parameters={"delta": -10}, raw_text=raw_text)

        if command in {"lock computer", "lock the computer", "lock windows"}:
            return Intent(action="lock_computer", raw_text=raw_text)

        if command in {"shutdown", "shut down", "shutdown computer", "restart", "restart computer"}:
            return Intent(action="dangerous_system_action", target=command, raw_text=raw_text, requires_confirmation=True)

        return Intent(action="unknown", raw_text=raw_text)

    def _detect_level_command(self, command: str, raw_text: str) -> Intent | None:
        volume_match = re.search(r"(set|change)\s+(the\s+)?volume\s+(to\s+)?(?P<level>\d{1,3})\s*(percent|%)?", command)
        if volume_match:
            return Intent(action="set_volume", parameters={"level": int(volume_match.group("level"))}, raw_text=raw_text)

        brightness_match = re.search(
            r"(set|change)\s+(the\s+)?brightness\s+(to\s+)?(?P<level>\d{1,3})\s*(percent|%)?",
            command,
        )
        if brightness_match:
            return Intent(action="set_brightness", parameters={"level": int(brightness_match.group("level"))}, raw_text=raw_text)

        return None

    def _detect_search(self, command: str, raw_text: str) -> Intent | None:
        youtube_match = re.search(r"search\s+youtube\s+(for\s+)?(?P<query>.+)$", command)
        if youtube_match:
            return Intent(action="search_web", target="youtube", parameters={"query": youtube_match.group("query")}, raw_text=raw_text)

        youtube_natural_match = re.search(
            r"(?:open\s+)?youtube(?:\s+for\s+me)?(?:\s+and)?\s+search\s+(?:for\s+)?(?P<query>.+)$",
            command,
        )
        if youtube_natural_match:
            return Intent(
                action="search_web",
                target="youtube",
                parameters={"query": youtube_natural_match.group("query")},
                raw_text=raw_text,
            )

        youtube_suffix_match = re.search(r"search\s+(?:for\s+)?(?P<query>.+)\s+on\s+youtube$", command)
        if youtube_suffix_match:
            return Intent(
                action="search_web",
                target="youtube",
                parameters={"query": youtube_suffix_match.group("query")},
                raw_text=raw_text,
            )

        google_match = re.search(r"search\s+(google\s+)?(for\s+)?(?P<query>.+)$", command)
        if google_match:
            return Intent(action="search_web", target="google", parameters={"query": google_match.group("query")}, raw_text=raw_text)

        return None
