import time
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

from .metadata import DownloadItem, write_photo_metadata, write_video_metadata
from .zip_handler import ZipHandler
from .paths import MEMORIES_STORAGE_DIR
from .logging_manager import get_logger

# Logger initialization
logger = get_logger()

if TYPE_CHECKING:
    from .download_manager import DownloadManager

def get_output_dir() -> Path:
    # Get the output directory
    return MEMORIES_STORAGE_DIR


class DownloadWorker:
    # Manages individual file download with automatic retry
    
    def __init__(self, manager: "DownloadManager") -> None:
        self.manager = manager
        self._zip_handler = ZipHandler()

    def _is_zip_file(self, file_path: Path) -> bool:
        # Check if file is ZIP (magic bytes 'PK')
        with file_path.open("rb") as f:
            header = f.read(2)
        return header[:2] == b"PK"

    def _download_one_attempt(self, item: DownloadItem, attempt: int) -> int:
        # Attempt to download file once, returns bytes downloaded
        target_path = get_output_dir() / item.filename
        
        req = Request(item.url)
        req.add_header("User-Agent", "Mozilla/5.0")

        start_time = time.time()
        with urlopen(req, timeout=30) as resp, target_path.open("wb") as out_f:
            written = 0
            chunk = resp.read(8192)
            while chunk:
                out_f.write(chunk)
                written += len(chunk)
                chunk = resp.read(8192)

        download_duration = time.time() - start_time
        
        logger.log(f"DOWNLOAD: File downloaded successfully - {item.filename} ({written / 1024 / 1024:.2f}MB, {download_duration:.2f}s)")

        # ZIP detection
        is_zip = self._is_zip_file(target_path)

        if is_zip:
            logger.log(f"DOWNLOAD: ZIP file detected - {item.filename}, extracting...")
            self._zip_handler.handle_zip(target_path, item)
            return written

        # Metadata for normal files
        try:
            metadata_ok = False
            if item.media_type.lower() == "video":
                metadata_ok = write_video_metadata(target_path, item.date, item.location)
            else:
                metadata_ok = write_photo_metadata(target_path, item.date, item.location)
            
            if metadata_ok:
                logger.log(f"DOWNLOAD: Metadata added successfully - {item.filename}")
            else:
                logger.log(f"DOWNLOAD: Metadata skipped (ExifTool not available) - {item.filename}")
        except Exception as e:
            logger.log(f"DOWNLOAD: Failed to add metadata - {item.filename}: {str(e)}")

        return written

    def download_one(self, item: DownloadItem) -> None:
        # Download file with automatic retry until success
        # Marks as failed only if all attempts fail
        if self.manager.is_stopping():
            return

        target_path = get_output_dir() / item.filename
        self.manager.set_current_item(item)

        max_retries = 5
        retry_delays = [1, 2, 4, 8, 16]
        
        for attempt in range(1, max_retries + 1):
            try:
                bytes_downloaded = self._download_one_attempt(item, attempt)
                
                # Success!
                self.manager.update_stats_on_success(bytes_downloaded)
                self.manager.reset_consecutive_failures()
                self.manager.mark_success(item)

                return

            except (HTTPError, URLError) as exc:
                # Clean up partial file
                if target_path.exists():
                    target_path.unlink()

                error_msg = str(exc)
                error_type = type(exc).__name__
                
                if isinstance(exc, HTTPError):
                    error_msg = f"HTTP {exc.code}"
                    error_type = f"HTTP_{exc.code}"

                # Increment consecutive failures (global counter for dead links detection)
                consecutive_now = self.manager.increment_consecutive_failures()
                
                # Display counter capped at 5/5 (even if internal continues incrementing)
                display_counter = min(consecutive_now, 5)
                
                # Check if THIS worker triggers dead links threshold
                was_already_stopping = self.manager.should_fast_stop()
                should_trigger_now = consecutive_now >= 5 and not was_already_stopping
                
                # If this worker triggers the threshold
                if should_trigger_now:
                    self.manager.trigger_dead_links_stop()
                    self.manager.update_stats_on_failure()
                    self.manager.mark_failure(item)
                    return
                
                # Otherwise, check if dead links flag activated (by another worker)
                is_dead_links_mode = self.manager.should_fast_stop()
                
                if is_dead_links_mode:
                    # DEAD LINKS mode: immediate abandon
                    self.manager.update_stats_on_failure()
                    self.manager.mark_failure(item)
                    return
                else:
                    # Retry or mark as failed
                    if attempt < max_retries:
                        wait_time = retry_delays[attempt - 1]
                        time.sleep(wait_time)
                    else:
                        self.manager.update_stats_on_failure()
                        self.manager.mark_failure(item)
                        return
            
            except Exception as e:
                self.manager.update_stats_on_failure()
                self.manager.mark_failure(item)
                return