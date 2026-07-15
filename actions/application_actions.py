from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from assistant.models import ActionResult, Intent


COMMON_APP_PATHS = {
    "chrome": [
        r"Google\Chrome\Application\chrome.exe",
    ],
    "msedge": [
        r"Microsoft\Edge\Application\msedge.exe",
    ],
    "telegram": [
        r"Telegram Desktop\Telegram.exe",
    ],
    "spotify": [
        r"Spotify\Spotify.exe",
    ],
    "code": [
        r"Microsoft VS Code\Code.exe",
    ],
}


class ApplicationActions:
    def __init__(self, applications: dict[str, str], dry_run: bool = False) -> None:
        self.applications = applications
        self.dry_run = dry_run

    def open_application(self, intent: Intent) -> ActionResult:
        target = (intent.target or "").strip().lower()
        executable = self.applications.get(target, target)
        if not executable:
            return ActionResult(False, "No application was specified.")

        if self.dry_run:
            return ActionResult(True, f"Would open {target or executable}.")

        try:
            resolved = self._resolve_executable(executable)
            if resolved:
                subprocess.Popen([resolved], shell=False)
            else:
                subprocess.Popen(["cmd", "/c", "start", "", executable], shell=False)
        except OSError as exc:
            return ActionResult(False, f"Could not open {target}: {exc}")
        return ActionResult(True, f"Opening {target}.")

    def _resolve_executable(self, executable: str) -> str | None:
        path_from_env = shutil.which(executable)
        if path_from_env:
            return path_from_env

        candidate = Path(executable)
        if candidate.exists():
            return str(candidate)

        app_key = candidate.stem.lower()
        base_dirs = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            os.environ.get("LOCALAPPDATA"),
            os.environ.get("APPDATA"),
        ]
        for relative_path in COMMON_APP_PATHS.get(app_key, []):
            for base_dir in base_dirs:
                if not base_dir:
                    continue
                full_path = Path(base_dir) / relative_path
                if full_path.exists():
                    return str(full_path)

        return None
