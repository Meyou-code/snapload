import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder
from .paths import EXIFTOOL_PATH
from .logging_manager import get_logger

# Logger initialization
logger = get_logger()

@dataclass
class DownloadItem:
    # Represents a Snapchat media to download
    index: int
    date: str
    media_type: str
    location: str
    url: str
    filename: str


def _ensure_exiftool_exists() -> bool:
    # Check if ExifTool exists at expected location
    # Returns True if found, False otherwise
    if not EXIFTOOL_PATH.exists():
        logger.log(f"METADATA: ExifTool not found at {EXIFTOOL_PATH}")
        return False
    return True


def _parse_date_utc(date_str: str) -> datetime:
    # Convert date like '2025-12-13 13:49:04 UTC' to UTC datetime
    dt = datetime.strptime(date_str.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc)


@lru_cache(maxsize=1000)
def _parse_location(location_str: str) -> Optional[Tuple[float, float]]:
    # Parse location string like 'Latitude, Longitude: 43.345695, 3.2427309'
    # Cached to avoid parsing same location multiple times
    if not location_str or "Latitude" not in location_str or "Longitude" not in location_str:
        return None
    
    _, coords = location_str.split(":", 1)
    lat_str, lon_str = coords.split(",", 1)
    return float(lat_str.strip()), float(lon_str.strip())


def _gps_exif_args(lat: float, lon: float) -> list[str]:
    # Generate GPS EXIF arguments for ExifTool
    lat_ref = "N" if lat >= 0 else "S"
    lon_ref = "E" if lon >= 0 else "W"
    return [
        f"-GPSLatitude={abs(lat)}",
        f"-GPSLatitudeRef={lat_ref}",
        f"-GPSLongitude={abs(lon)}",
        f"-GPSLongitudeRef={lon_ref}",
    ]


def _localize_datetime(date_str: str, location_str: str) -> datetime:
    # Return local datetime at capture time using GPS coordinates to find timezone
    base_utc = _parse_date_utc(date_str)
    gps = _parse_location(location_str)

    if gps is not None:
        lat, lon = gps
        tz_name = TimezoneFinder().timezone_at(lat=lat, lng=lon)
        if tz_name:
            return base_utc.astimezone(ZoneInfo(tz_name))

    # Fallback to machine's local timezone
    local_tz = datetime.now().astimezone().tzinfo
    return base_utc.astimezone(local_tz)


def write_photo_metadata(file_path: Path, date_str: str, location_str: str) -> bool:
    # Write EXIF metadata to photo file
    # Returns True if successful, False if ExifTool not found or error
    if not _ensure_exiftool_exists():
        return False

    local_dt = _localize_datetime(date_str, location_str)
    exif_date = local_dt.strftime("%Y:%m:%d %H:%M:%S")
    
    gps = _parse_location(location_str)

    args: list[str] = [
        str(EXIFTOOL_PATH),
        "-overwrite_original",
        f"-DateTimeOriginal={exif_date}",
        f"-CreateDate={exif_date}",
        f"-ModifyDate={exif_date}",
    ]

    if gps is not None:
        lat, lon = gps
        args.extend(_gps_exif_args(lat, lon))

    args.append(str(file_path))

    # ✅ FIX: Hide console window on Windows (prevents CMD flashing during downloads)
    subprocess.run(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    return True


def write_video_metadata(file_path: Path, date_str: str, location_str: str) -> bool:
    # Write EXIF metadata to video file
    # Returns True if successful, False if ExifTool not found or error
    if not _ensure_exiftool_exists():
        return False

    local_dt = _localize_datetime(date_str, location_str)
    exif_date = local_dt.strftime("%Y:%m:%d %H:%M:%S")
    
    gps = _parse_location(location_str)

    args: list[str] = [
        str(EXIFTOOL_PATH),
        "-overwrite_original",
        # Main dates
        f"-CreateDate={exif_date}",
        f"-ModifyDate={exif_date}",
        # QuickTime track dates
        f"-TrackCreateDate={exif_date}",
        f"-TrackModifyDate={exif_date}",
        f"-MediaCreateDate={exif_date}",
        f"-MediaModifyDate={exif_date}",
        # XMP dates (Apple Photos friendly)
        f"-XMP:CreateDate={exif_date}",
        f"-XMP:ModifyDate={exif_date}",
    ]

    if gps is not None:
        lat, lon = gps
        args.extend([
            f"-XMP-exif:GPSLatitude={abs(lat)}",
            f"-XMP-exif:GPSLatitudeRef={'N' if lat >= 0 else 'S'}",
            f"-XMP-exif:GPSLongitude={abs(lon)}",
            f"-XMP-exif:GPSLongitudeRef={'E' if lon >= 0 else 'W'}",
        ])

    args.append(str(file_path))

    subprocess.run(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )
    return True