import json
import os
import re
import zipfile
import shutil
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Optional, Tuple

from .paths import USER_DATA_DIR, MEMORIES_HISTORY_FILE


# Validation and file selection

def is_valid_memories_file(file_path: Path) -> bool:
    # Validate if the file is a valid memories_history.json file
    if not file_path.exists():
        return False
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check if it has the expected structure
        return ("Saved Media" in data or "SavedMedia" in data)
    except Exception:
        return False


def select_memories_file() -> Optional[Path]:
    # Open a file dialog to select the memories_history.json file
    try:
        root = Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        # Get Downloads folder path
        downloads_path = Path.home() / "Downloads"
        
        # Open file dialog in Downloads folder
        file_path = filedialog.askopenfilename(
            title="Select memories_history.json file",
            initialdir=str(downloads_path),
            filetypes=[
                ("memories_history.json file", "memories_history.json"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        
        if not file_path:
            return None
        
        file_path = Path(file_path)
        
        # Check that the file is named exactly "memories_history.json"
        if file_path.name != "memories_history.json":
            return None
        
        # Validate file content
        if is_valid_memories_file(file_path):
            return file_path
        else:
            return None
            
    except Exception as e:
        return None


def get_memories_file_path(ask_user: bool = False) -> Optional[Path]:
    # Get the memories file path from fixed location (AppData/Roaming/Snapload)
    if is_valid_memories_file(MEMORIES_HISTORY_FILE):
        return MEMORIES_HISTORY_FILE
    
    # Ask user to select it only if ask_user=True
    if ask_user:
        selected_path = select_memories_file()
        if selected_path:
            return selected_path
    
    return None


def update_memories_file_path(file_path: Path) -> bool:
    # Validate that the file is a valid memories file
    return is_valid_memories_file(file_path)


# ZIP extraction utilities

# Constants
DEST_FOLDER = os.path.join("AppData", "Roaming", "Snapload")
JSON_PATH_IN_ZIP = "json/memories_history.json"
ZIP_PATTERN = re.compile(r"^mydata~\d+\.zip$")


def ensure_destination() -> str:
    # Ensure destination folder exists and return its path
    user_home = os.path.expanduser("~")
    dest = os.path.join(user_home, DEST_FOLDER)
    os.makedirs(dest, exist_ok=True)
    return dest


def extract_json_from_zip(zip_path: str, dest_dir: str) -> Optional[str]:
    # Extract memories_history.json from ZIP to dest_dir
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if JSON_PATH_IN_ZIP not in zip_ref.namelist():
                return None
            dest_file = os.path.join(dest_dir, "memories_history.json")
            with zip_ref.open(JSON_PATH_IN_ZIP) as src, open(dest_file, "wb") as tgt:
                shutil.copyfileobj(src, tgt)
            return dest_file
    except Exception:
        return None


def auto_choose_json() -> Tuple[bool, Optional[str]]:
    # Find latest memories_history.json or mydata~XXXX.zip in Downloads
    # Priority: Direct JSON files first, then ZIPs
    try:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            return False, None
        
        dest_dir = ensure_destination()
        
        # PRIORITY 1: Look for extracted memories_history.json files directly
        json_files = [
            os.path.join(downloads, f) 
            for f in os.listdir(downloads) 
            if f == "memories_history.json" and os.path.isfile(os.path.join(downloads, f))
        ]
        
        if json_files:
            # Get newest JSON file
            latest_json = max(json_files, key=os.path.getmtime)
            # Validate it
            if is_valid_memories_file(Path(latest_json)):
                # Copy to destination
                dest_file = os.path.join(dest_dir, "memories_history.json")
                shutil.copy2(latest_json, dest_file)
                return True, dest_file
        
        # PRIORITY 2: Look for mydata~XXXX.zip files
        zips = [
            os.path.join(downloads, f) 
            for f in os.listdir(downloads) 
            if ZIP_PATTERN.match(f) and os.path.isfile(os.path.join(downloads, f))
        ]
        
        if zips:
            # Get newest ZIP
            latest_zip = max(zips, key=os.path.getmtime)
            dest_file = extract_json_from_zip(latest_zip, dest_dir)
            if dest_file:
                return True, dest_file
        
        return False, None
    except Exception:
        return False, None


def extract_zip_memories(zip_file_path: str) -> Tuple[bool, Optional[str]]:
    # Extract JSON from a specified ZIP if it matches mydata~XXXX.zip pattern
    try:
        if not ZIP_PATTERN.match(os.path.basename(zip_file_path)):
            return False, None
        if not os.path.exists(zip_file_path):
            return False, None
        
        dest_dir = ensure_destination()
        dest_file = extract_json_from_zip(zip_file_path, dest_dir)
        if dest_file:
            return True, dest_file
        return False, None
    except Exception:
        return False, None