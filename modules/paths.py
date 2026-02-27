from pathlib import Path
import sys

MAX_WORKERS = 10

# Detect if running in frozen mode (PyInstaller bundle)
IS_FROZEN = getattr(sys, 'frozen', False)

# Root folder of the project/bundle
if IS_FROZEN:
    # In frozen mode
    BUNDLE_ROOT = Path(sys._MEIPASS)
else:
    # In development: use the project root
    BUNDLE_ROOT = Path(__file__).parent.parent.resolve()


# UI folder
UI_DIR = BUNDLE_ROOT / "ui"
TRANSLATIONS_FILE = UI_DIR / "translations.json"

# Tools folder (ExifTool, FFmpeg)
TOOLS_DIR = BUNDLE_ROOT / "tools"
EXIFTOOL_PATH = TOOLS_DIR / "exiftool" / "exiftool.exe"
FFMPEG_PATH = TOOLS_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"
FFPROBE_PATH = TOOLS_DIR / "ffmpeg" / "bin" / "ffprobe.exe"

# User data folder (AppData/Roaming/Snapload)
USER_DATA_DIR = Path.home() / "AppData" / "Roaming" / "Snapload"

# Logs and state files in user data
DOWNLOAD_STATE_FILE = USER_DATA_DIR / "download_state.json"
MEMORIES_HISTORY_FILE = USER_DATA_DIR / "memories_history.json"

# Storage folders inside Downloads
DOWNLOADS_DIR = Path.home() / "Downloads"
MEMORIES_STORAGE_DIR = DOWNLOADS_DIR / "SnapLoad"
ZIPS_DIR = MEMORIES_STORAGE_DIR / "zips"


# UTILITY FUNCTIONS

def ensure_all_directories_exist():
    MEMORIES_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    ZIPS_DIR.mkdir(parents=True, exist_ok=True)
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

def ensure_user_data_dir_exists():
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def ensure_output_directories_exist():
    MEMORIES_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    ZIPS_DIR.mkdir(parents=True, exist_ok=True)