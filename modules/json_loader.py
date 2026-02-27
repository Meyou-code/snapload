import json
from pathlib import Path
from typing import List, Set

from .memories_selector import get_memories_file_path


class JsonLoader:
    # Loads JSON file and creates list of items to download
    
    def __init__(self) -> None:
        self._memories_file = None

    def load_items(self, success_ids: Set[int]) -> tuple[List, int, int]:
        # Load items from JSON, returns (items_to_download, total_count, skipped_count)
        # Args: success_ids - IDs already successfully downloaded (to skip)
        
        # Import lazy pour éviter circular import
        from .metadata import DownloadItem
        
        # Get memories file path (don't ask user - should be set via UI)
        if self._memories_file is None:
            self._memories_file = get_memories_file_path(ask_user=False)
        
        if self._memories_file is None or not self._memories_file.exists():
            raise FileNotFoundError(f"Memories file not accessible")
        
        try:
            with self._memories_file.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            raise

        saved_media = raw.get("Saved Media") or raw.get("SavedMedia") or []
        total_count = len(saved_media)

        items_to_download: List[DownloadItem] = []
        skipped_count = 0

        for idx, entry in enumerate(saved_media, start=1):
            # Skip if already downloaded
            if idx in success_ids:
                skipped_count += 1
                continue

            date = entry.get("Date", "")
            media_type = entry.get("Media Type", "")
            location = entry.get("Location", "")
            
            # ✅ FIX: Use ONLY "Media Download Url" - it's the only one that works with GET
            # "Download Link" returns HTTP 405 (Method Not Allowed) with GET requests
            url = entry.get("Media Download Url", "")

            # Skip entries without URL
            if not url:
                skipped_count += 1
                continue

            ext = "mp4" if media_type.lower() == "video" else "jpg"
            filename = f"{idx:05d}_{'video' if ext == 'mp4' else 'image'}.{ext}"
            
            items_to_download.append(
                DownloadItem(
                    index=idx,
                    date=date,
                    media_type=media_type,
                    location=location,
                    url=url,
                    filename=filename,
                )
            )
        
        return items_to_download, total_count, skipped_count