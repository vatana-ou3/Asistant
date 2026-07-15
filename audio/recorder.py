from __future__ import annotations

import math
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioRecording:
    samples: object
    sample_rate: int
    speech_detected: bool | None = None


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels

    def record_command(
        self,
        duration_seconds: float = 10.0,
        silence_seconds: float = 0.5,
        block_seconds: float = 0.05,
        start_timeout_seconds: float = 2.0,
        cancellation_event: threading.Event | None = None,
    ) -> AudioRecording:
        try:
            import sounddevice as sd
        except ModuleNotFoundError as exc:
            raise RuntimeError("Voice mode needs the 'sounddevice' package. Run: pip install -r requirements.txt") from exc

        try:
            import numpy as np
        except ModuleNotFoundError as exc:
            raise RuntimeError("Voice mode needs the 'numpy' package. Run: pip install -r requirements.txt") from exc

        block_frames = max(1, int(block_seconds * self.sample_rate))
        max_blocks = max(1, math.ceil(duration_seconds / block_seconds))
        silent_blocks_to_stop = max(1, math.ceil(silence_seconds / block_seconds))
        start_timeout_blocks = max(1, math.ceil(start_timeout_seconds / block_seconds))
        calibration_blocks = max(1, math.ceil(0.15 / block_seconds))
        blocks = []
        calibration_levels = []
        peak_level = 0.0
        speech_started = False
        silent_blocks = 0
        speech_threshold = 0.00015

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=block_frames,
        ) as stream:
            for _ in range(max_blocks):
                if cancellation_event is not None and not cancellation_event.is_set():
                    break
                block, _overflowed = stream.read(block_frames)
                block = block.copy()
                blocks.append(block)

                level = float(np.sqrt(np.mean(np.square(block))))
                if not speech_started:
                    if len(calibration_levels) < calibration_blocks:
                        calibration_levels.append(level)
                        continue

                    noise_floor = float(np.median(calibration_levels))
                    speech_threshold = max(0.00015, noise_floor * 2.5)
                    if level >= speech_threshold:
                        speech_started = True
                        peak_level = level
                    elif len(blocks) >= start_timeout_blocks:
                        break
                    continue

                peak_level = max(peak_level, level)
                silence_threshold = max(speech_threshold * 0.8, peak_level * 0.15)
                if level < silence_threshold:
                    silent_blocks += 1
                    if silent_blocks >= silent_blocks_to_stop:
                        break
                else:
                    silent_blocks = 0

        samples = (
            np.concatenate(blocks, axis=0)
            if blocks
            else np.empty((0, self.channels), dtype=np.float32)
        )
        return AudioRecording(samples=samples, sample_rate=self.sample_rate, speech_detected=speech_started)
