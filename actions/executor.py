from __future__ import annotations

from assistant.models import ActionResult, Intent
from config.config import AppConfig
from actions.application_actions import ApplicationActions
from actions.audio_actions import AudioActions
from actions.brightness_actions import BrightnessActions
from actions.browser_actions import BrowserActions
from actions.keyboard_actions import KeyboardActions
from actions.mouse_actions import MouseActions
from actions.system_actions import SystemActions
from actions.window_actions import WindowActions


class ActionExecutor:
    def __init__(self, config: AppConfig, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.applications = ApplicationActions(config.applications, dry_run=dry_run)
        self.browser = BrowserActions(dry_run=dry_run)
        self.keyboard = KeyboardActions(dry_run=dry_run)
        self.mouse = MouseActions(dry_run=dry_run)
        self.audio = AudioActions(dry_run=dry_run)
        self.brightness = BrightnessActions(dry_run=dry_run)
        self.system = SystemActions(dry_run=dry_run)
        self.window = WindowActions(dry_run=dry_run)

    def execute(self, intent: Intent) -> ActionResult:
        dispatch = {
            "open_application": self.applications.open_application,
            "open_website": self.browser.open_website,
            "search_web": self.browser.search_web,
            "keyboard_shortcut": self.keyboard.shortcut,
            "press_key": self.keyboard.press_key,
            "scroll": self.mouse.scroll,
            "stop_scroll": self.mouse.stop_scroll,
            "mouse_click": self.mouse.click,
            "mouse_double_click": self.mouse.double_click,
            "set_volume": self.audio.set_volume,
            "adjust_volume": self.audio.adjust_volume,
            "mute_volume": self.audio.mute,
            "set_brightness": self.brightness.set_brightness,
            "adjust_brightness": self.brightness.adjust_brightness,
            "lock_computer": self.system.lock_computer,
            "maximize_window": self.window.maximize,
            "restore_window": self.window.restore,
        }
        handler = dispatch.get(intent.action)
        if handler is None:
            return ActionResult(False, f"No executor is registered for {intent.action}.")
        return handler(intent)
