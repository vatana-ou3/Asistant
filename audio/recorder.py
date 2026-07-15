from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioRecording:
    samples: object
    sample_rate: int


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels

    def record_command(
        self,
        duration_seconds: float = 5.0,
        silence_seconds: float = 0.75,
        block_seconds: float = 0.05,
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
        blocks = []
        peak_level = 0.0
        speech_started = False
        silent_blocks = 0

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=block_frames,
        ) as stream:
            for _ in range(max_blocks):
                block, _overflowed = stream.read(block_frames)
                block = block.copy()
                blocks.append(block)

                level = float(np.sqrt(np.mean(np.square(block))))
                peak_level = max(peak_level, level)
                silence_threshold = max(0.0001, peak_level * 0.2)
                if level >= silence_threshold:
                    speech_started = True
                    silent_blocks = 0
                elif speech_started:
                    silent_blocks += 1
                    if silent_blocks >= silent_blocks_to_stop:
                        break

        samples = np.concatenate(blocks, axis=0)
        return AudioRecording(samples=samples, sample_rate=self.sample_rate)
