from __future__ import annotations

from assistant.models import ActionResult, Intent


class AudioActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def set_volume(self, intent: Intent) -> ActionResult:
        level = intent.parameters["level"]
        if self.dry_run:
            return ActionResult(True, f"Would set volume to {level} percent.")

        pycaw_result = self._set_volume_with_pycaw(level)
        if pycaw_result.success:
            return pycaw_result

        fallback_result = self._set_volume_with_media_keys(level)
        if fallback_result.success:
            return fallback_result

        return ActionResult(
            False,
            f"{pycaw_result.message} Fallback volume keys also failed: {fallback_result.message}",
        )

    def adjust_volume(self, intent: Intent) -> ActionResult:
        delta = intent.parameters["delta"]
        if self.dry_run:
            return ActionResult(True, f"Would adjust volume by {delta} percent.")

        key = "volumeup" if delta > 0 else "volumedown"
        presses = max(1, round(abs(delta) / 2))
        try:
            import pyautogui

            pyautogui.press(key, presses=presses, interval=0.02)
        except Exception as exc:
            return ActionResult(False, f"Volume key adjustment failed: {exc}")
        return ActionResult(True, f"Adjusted volume by about {delta} percent.")

    def mute(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would mute audio.")

        pycaw_result = self._mute_with_pycaw()
        if pycaw_result.success:
            return pycaw_result

        try:
            import pyautogui

            pyautogui.press("volumemute")
        except Exception as exc:
            return ActionResult(False, f"{pycaw_result.message} Fallback mute key also failed: {exc}")
        return ActionResult(True, "Audio muted.")

    def _set_volume_with_pycaw(self, level: int) -> ActionResult:
        try:
            volume = self._get_endpoint_volume()
            volume.SetMasterVolumeLevelScalar(level / 100, None)
        except ModuleNotFoundError as exc:
            return ActionResult(False, f"Exact volume control needs missing package '{exc.name}'.")
        except Exception as exc:
            return ActionResult(False, f"Exact volume control failed: {exc}")
        return ActionResult(True, f"Volume set to {level} percent.")

    def _set_volume_with_media_keys(self, level: int) -> ActionResult:
        try:
            import pyautogui

            pyautogui.press("volumedown", presses=50, interval=0.01)
            if level > 0:
                pyautogui.press("volumeup", presses=round(level / 2), interval=0.01)
        except Exception as exc:
            return ActionResult(False, str(exc))
        return ActionResult(True, f"Volume set to about {level} percent using media keys.")

    def _mute_with_pycaw(self) -> ActionResult:
        try:
            volume = self._get_endpoint_volume()
            volume.SetMute(1, None)
        except ModuleNotFoundError as exc:
            return ActionResult(False, f"Exact mute control needs missing package '{exc.name}'.")
        except Exception as exc:
            return ActionResult(False, f"Exact mute failed: {exc}")
        return ActionResult(True, "Audio muted.")

    def _get_endpoint_volume(self):
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
