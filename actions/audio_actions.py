from __future__ import annotations

from assistant.models import ActionResult, Intent


class AudioActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def set_volume(self, intent: Intent) -> ActionResult:
        level = intent.parameters["level"]
        if self.dry_run:
            return ActionResult(True, f"Would set volume to {level} percent.")

        try:
            from ctypes import POINTER, cast

            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
        except Exception as exc:
            return ActionResult(False, f"Volume control failed: {exc}")
        return ActionResult(True, f"Volume set to {level} percent.")

    def adjust_volume(self, intent: Intent) -> ActionResult:
        delta = intent.parameters["delta"]
        if self.dry_run:
            return ActionResult(True, f"Would adjust volume by {delta} percent.")
        return ActionResult(False, "Volume adjustment needs pycaw readback support; use 'set volume to N percent' for now.")

    def mute(self, intent: Intent) -> ActionResult:
        if self.dry_run:
            return ActionResult(True, "Would mute audio.")

        try:
            from ctypes import POINTER, cast

            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(1, None)
        except Exception as exc:
            return ActionResult(False, f"Mute failed: {exc}")
        return ActionResult(True, "Audio muted.")
