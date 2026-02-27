import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .metadata import DownloadItem
from .download_worker import DownloadWorker
from .state import read_state_file, save_state_file
from .paths import MEMORIES_STORAGE_DIR, ZIPS_DIR, ensure_output_directories_exist
from .speed_tracker import SpeedTracker

def get_output_dir() -> Path:
    return MEMORIES_STORAGE_DIR


@dataclass
class DownloadStats:
    total: int = 0
    completed: int = 0
    success: int = 0
    failed: int = 0
    current_index: Optional[int] = None
    current_filename: str = ""
    start_time: Optional[float] = None
    last_update: float = field(default_factory=time.time)
    last_completed: int = 0


class DownloadManager:
    def __init__(self, max_workers: int) -> None:
        self.max_workers = max_workers
        self.items: List[DownloadItem] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._running = threading.Event()
        
        # Persistent state
        self._success_ids: Set[int] = set()
        self._failed_ids: Set[int] = set()
        self._total_from_state: int = 0
        
        # Speed tracker
        self._speed_tracker = SpeedTracker()
        
        # Dead links detection
        self._consecutive_failures: int = 0
        self._max_consecutive_failures: int = 5
        self._dead_links_detected: bool = False
        self._dead_links_fast_stop: bool = False

        self.stats = DownloadStats(
            total=self._total_from_state,
            completed=len(self._success_ids),
            success=len(self._success_ids),
            failed=len(self._failed_ids),
        )

    def _load_state_into_memory(self) -> None:
        # Load persistent state from download_state.json
        success_ids, failed_ids, total = read_state_file()
        self._success_ids = success_ids
        self._failed_ids = failed_ids
        self._total_from_state = total

    def _save_state_locked(self) -> None:
        # Save current state (must be called under self._lock)
        save_state_file(self.stats.total, self._success_ids, self._failed_ids)

    def mark_success(self, item: DownloadItem) -> None:
        # Mark download as successful
        with self._lock:
            self._success_ids.add(item.index)
            self._failed_ids.discard(item.index)
            self._save_state_locked()

    def mark_failure(self, item: DownloadItem) -> None:
        # Mark download as failed
        with self._lock:
            if item.index not in self._success_ids:
                self._failed_ids.add(item.index)
            self._save_state_locked()

    def increment_consecutive_failures(self) -> int:
        # Increment consecutive failures counter and return its value
        with self._lock:
            self._consecutive_failures += 1
            return self._consecutive_failures

    def reset_consecutive_failures(self) -> None:
        # Reset consecutive failures counter
        with self._lock:
            self._consecutive_failures = 0

    def trigger_dead_links_stop(self) -> None:
        # Trigger fast stop for dead links
        with self._lock:
            if not self._dead_links_fast_stop:
                self._dead_links_detected = True
                self._dead_links_fast_stop = True
                self._stop_event.set()

    def should_fast_stop(self) -> bool:
        # Returns True if fast stop was triggered
        return self._dead_links_fast_stop

    def is_stopping(self) -> bool:
        # Returns True if stop is in progress
        return self._stop_event.is_set()

    def update_stats_on_success(self, bytes_downloaded: int) -> None:
        # Update stats after successful download
        now = time.time()
        with self._lock:
            self.stats.completed += 1
            self.stats.success += 1
            self._speed_tracker.add_file_sample(now, self.stats.completed)
            self._speed_tracker.add_bytes_sample(now, self._speed_tracker.total_bytes + bytes_downloaded)

    def update_stats_on_failure(self) -> None:
        # Update stats after failure
        with self._lock:
            self.stats.completed += 1
            self.stats.failed += 1

    def set_current_item(self, item: Optional[DownloadItem]) -> None:
        # Set current item being processed
        with self._lock:
            if item:
                self.stats.current_index = item.index
                self.stats.current_filename = item.filename
            else:
                self.stats.current_index = None
                self.stats.current_filename = ""

    def get_status(self) -> Dict[str, Any]:
        # Return current download status
        with self._lock:
            # Calculate stats from actual data (IDs), not counters
            actual_completed = len(self._success_ids)  # Only successes (real progress)
            actual_success = len(self._success_ids)
            actual_failed = len(self._failed_ids)
            
            files_per_second, mb_per_second = self._speed_tracker.calculate_speed()
            
            remaining = self.stats.total - (actual_completed + actual_failed)
            eta = None
            if files_per_second > 0 and remaining > 0:
                eta = remaining / files_per_second

            running = self._running.is_set()
            stopping = self._stop_event.is_set()

            if not running and not stopping:
                files_per_second = 0.0
                mb_per_second = 0.0
                eta = None

            return {
                "running": running,
                "stopping": stopping,
                "total": self.stats.total,
                "completed": actual_completed,
                "success": actual_success,
                "failed": actual_failed,
                "failed_ids": sorted(self._failed_ids),
                "current_index": self.stats.current_index,
                "current_filename": self.stats.current_filename,
                "files_per_second": files_per_second,
                "mb_per_second": mb_per_second,
                "eta_seconds": eta,
                "dead_links_detected": self._dead_links_detected,
            }

    def start(self) -> None:
        # Start download
        if self._running.is_set():
            return
        
        # Create output directories when download starts
        ensure_output_directories_exist()
        
        self._stop_event.clear()
        self._running.set()
        self._dead_links_detected = False
        self._dead_links_fast_stop = False
        self._consecutive_failures = 0
        
        with self._lock:
            self.stats.start_time = time.time()
            self._speed_tracker.reset()
            self._speed_tracker.start_time = time.time()

    def stop(self) -> None:
        # Request download stop
        if not self._running.is_set():
            return
        self._stop_event.set()

    def is_running(self) -> bool:
        # Returns True if download is in progress
        return self._running.is_set()

    def run(self, items: List[DownloadItem]) -> None:
        # Launch download of all items with ThreadPoolExecutor
        self.items = items
        self.start()

        if not self.items:
            return
        
        # Create worker with access to manager
        worker = DownloadWorker(self)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(worker.download_one, item) for item in self.items]

            for future in as_completed(futures):
                if self._stop_event.is_set():
                    break
        
        self._finalize()

    def _finalize(self) -> None:
        # Finalize download and cleanup
        self._running.clear()
        self._stop_event.clear()
        self.set_current_item(None)