from pathlib import Path
from typing import Any, Dict, List

from .download_manager import DownloadManager, DownloadStats
from .state import read_state_file
from .json_loader import JsonLoader
from .paths import MEMORIES_STORAGE_DIR, ensure_user_data_dir_exists, ZIPS_DIR, DOWNLOAD_STATE_FILE, MEMORIES_HISTORY_FILE
from .logging_manager import get_logger

# Logger initialization
logger = get_logger()

def get_output_dir() -> Path:
    return MEMORIES_STORAGE_DIR

# Logical class to manage downloading Snapchat Memories

class MemoriesDownloader:
    def __init__(self, max_workers: int) -> None:
        self._manager = DownloadManager(max_workers)
        self._json_loader = JsonLoader()

        ensure_user_data_dir_exists()

    # Public API

    def load_items(self) -> None:
        success_ids, failed_ids, total_from_state = read_state_file()
        items, total_count, skipped = self._json_loader.load_items(success_ids)
        
        # Log download state status
        if not DOWNLOAD_STATE_FILE.exists():
            logger.log("STARTUP: No download state found")
        else:
            logger.log(f"STARTUP: Download state loaded - Total: {total_from_state}, Success: {len(success_ids)}, Failed: {len(failed_ids)}, Remaining: {total_from_state - len(success_ids) - len(failed_ids)}")
        
        # Log memories file status
        if not MEMORIES_HISTORY_FILE.exists():
            logger.log("STARTUP: No memories history file found")
        else:
            logger.log(f"STARTUP: Memories file loaded - Total items: {total_count}, Skipped (already downloaded): {skipped}")
        
        self._manager.items = items
        self._manager._success_ids = success_ids
        self._manager._failed_ids = failed_ids
        self._manager.stats = DownloadStats(
            total=total_count,
            completed=len(success_ids),
            success=len(success_ids),
            failed=len(failed_ids),
        )
        self._manager._save_state_locked()

    def get_status(self) -> Dict[str, Any]:
        return self._manager.get_status()

    def start(self) -> None:
        self._manager.start()

    def stop(self) -> None:
        self._manager.stop()

    def is_running(self) -> bool:
        return self._manager.is_running()

    def run(self) -> None:
        if not self._manager.items:
            return

        try:
            self._manager.run(self._manager.items)
        except Exception as e:
            raise