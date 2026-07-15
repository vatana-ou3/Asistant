from __future__ import annotations

import threading


class TrayController:
    def __init__(self, assistant_name: str) -> None:
        self.assistant_name = assistant_name
        self.listening_enabled = threading.Event()
        self.listening_enabled.set()
        self._icon = None
        self._thread: threading.Thread | None = None
        self._status = "Listening"

    def start(self) -> None:
        try:
            import pystray
        except ModuleNotFoundError as exc:
            raise RuntimeError("Tray controls need pystray. Run: pip install -r requirements.txt") from exc

        menu = pystray.Menu(
            pystray.MenuItem(
                "Pause Listening",
                self._pause,
                enabled=lambda item: self.listening_enabled.is_set(),
            ),
            pystray.MenuItem(
                "Resume Listening",
                self._resume,
                enabled=lambda item: not self.listening_enabled.is_set(),
            ),
        )
        self._icon = pystray.Icon(
            "ahmark",
            self._create_icon(active=True),
            f"{self.assistant_name} - Listening",
            menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="ahmark-tray")
        self._thread.start()

    def stop(self) -> None:
        if self._icon is not None:
            self._icon.stop()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _pause(self, icon=None, item=None) -> None:
        self.listening_enabled.clear()
        self._set_status("Paused")

    def _resume(self, icon=None, item=None) -> None:
        self.listening_enabled.set()
        self._set_status("Listening")

    def _set_status(self, status: str) -> None:
        self._status = status
        if self._icon is None:
            return
        active = status == "Listening"
        self._icon.icon = self._create_icon(active=active)
        self._icon.title = f"{self.assistant_name} - {status}"
        self._icon.update_menu()

    @staticmethod
    def _create_icon(active: bool):
        try:
            from PIL import Image, ImageDraw
        except ModuleNotFoundError as exc:
            raise RuntimeError("Tray controls need Pillow. Run: pip install -r requirements.txt") from exc

        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        color = (20, 184, 166, 255) if active else (107, 114, 128, 255)
        draw.ellipse((3, 3, 61, 61), fill=color)
        draw.rounded_rectangle((24, 13, 40, 38), radius=8, fill="white")
        draw.arc((18, 21, 46, 47), start=0, end=180, fill="white", width=4)
        draw.line((32, 45, 32, 52), fill="white", width=4)
        draw.line((24, 52, 40, 52), fill="white", width=4)
        if not active:
            draw.line((15, 15, 49, 49), fill=(239, 68, 68, 255), width=6)
        return image
