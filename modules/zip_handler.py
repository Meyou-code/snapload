import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from .metadata import write_photo_metadata, write_video_metadata
from .paths import ZIPS_DIR

if TYPE_CHECKING:
    from .metadata import DownloadItem

class ZipHandler:
    # Handles ZIP extraction and metadata addition to extracted files
    
    def __init__(self) -> None:
        ZIPS_DIR.mkdir(parents=True, exist_ok=True)

    def get_extract_dir(self, index: int) -> Path:
        # Returns extraction directory path for given index
        return ZIPS_DIR / f"{index:05d}_extracted"

    def handle_zip(self, zip_path: Path, item: "DownloadItem") -> None:
        # Extract ZIP and add metadata to extracted files
        extract_dir = self.get_extract_dir(item.index)
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract all files
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()
        
        # Find JPEG or MP4 (not PNG)
        jpeg_file = None
        mp4_file = None
        
        for filename in extracted_files:
            file_path = extract_dir / filename
            if not file_path.is_file():
                continue
            
            ext = file_path.suffix.lower()
            if ext in ['.jpg', '.jpeg']:
                jpeg_file = file_path
            elif ext == '.mp4':
                mp4_file = file_path
        
        # Add metadata to found file
        target_file = jpeg_file or mp4_file
        if target_file:
            if mp4_file:
                write_video_metadata(target_file, item.date, item.location)
            elif jpeg_file:
                write_photo_metadata(target_file, item.date, item.location)
        
        # Delete original ZIP
        zip_path.unlink()