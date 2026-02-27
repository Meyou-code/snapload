import time
from collections import deque
from typing import Tuple

# Ty Chat GPT ❤️❤️

class SpeedTracker:
    def __init__(self, window_seconds: float = 30.0, max_samples: int = 30):
        self.window_seconds = window_seconds

        self.file_samples = deque(maxlen=max_samples)   # (timestamp, files_done)
        self.byte_samples = deque(maxlen=max_samples)   # (timestamp, bytes_done)

        self.start_time: float | None = None
        self.total_files = 0
        self.total_bytes = 0

    def add_file_sample(self, timestamp: float, files_done: int) -> None:
        self.file_samples.append((timestamp, files_done))
        self.total_files = files_done

    def add_bytes_sample(self, timestamp: float, bytes_done: int) -> None:
        self.byte_samples.append((timestamp, bytes_done))
        self.total_bytes = bytes_done

    def _cleanup_old_samples(self, samples: deque, now: float) -> None:
        while samples and now - samples[0][0] > self.window_seconds:
            samples.popleft()

    def _calculate_rate(self, samples: deque) -> float:
        if len(samples) < 2:
            return 0.0

        t0, v0 = samples[0]
        t1, v1 = samples[-1]
        dt = t1 - t0

        return (v1 - v0) / dt if dt > 0 else 0.0

    def calculate_speed(self) -> Tuple[float, float]:
        now = time.time()

        self._cleanup_old_samples(self.file_samples, now)
        self._cleanup_old_samples(self.byte_samples, now)

        files_per_sec = self._calculate_rate(self.file_samples)
        bytes_per_sec = self._calculate_rate(self.byte_samples)

        if self.start_time:
            elapsed = now - self.start_time
            if elapsed > 0:
                if files_per_sec == 0 and self.total_files > 0:
                    files_per_sec = self.total_files / elapsed
                if bytes_per_sec == 0 and self.total_bytes > 0:
                    bytes_per_sec = self.total_bytes / elapsed

        mb_per_sec = bytes_per_sec / (1024 * 1024)
        return files_per_sec, mb_per_sec

    def reset(self) -> None:
        self.file_samples.clear()
        self.byte_samples.clear()
        self.start_time = time.time()
        self.total_files = 0
        self.total_bytes = 0
