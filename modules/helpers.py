# UI management and path handling utilities

import sys
from pathlib import Path

from .paths import UI_DIR
from .memories_selector import get_memories_file_path


def get_ui_path() -> Path:
    # Get the UI folder path
    # If the application is packaged, use the bundled 'ui' folder
    # Otherwise, use the normal UI folder
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / 'ui'
    
    return UI_DIR


def translate_path(path: str) -> str:
    # Translate a URL path to a system path for the HTTP server
    ui_path = get_ui_path()
    
    if path.startswith("/ui/") or path in ("/ui",):
        rel = path.lstrip("/")
        return str(ui_path / rel.replace("ui/", "", 1))
    
    return str(ui_path.parent / path.lstrip("/"))


def handle_path_redirects(original_path: str) -> tuple[str, bool]:
    # Handle special path redirections
    # Returns (new_path, redirect_occurred)
    
    if original_path == "/memories-selector.html" or original_path.startswith("/memories-selector"):
        return ("/ui/pages/memories-selector.html", False)
    
    elif original_path in ("/", "/index.html"):
        memories_path = get_memories_file_path(ask_user=False)
        if memories_path is None or not memories_path.exists():
            return ("/memories-selector.html", True)  # Redirect needed
        return ("/ui/pages/index.html", False)
    
    elif original_path == "/settings.html" or original_path.startswith("/settings"):
        return ("/ui/pages/settings.html", False)
    
    elif original_path == "/modals.html" or original_path.startswith("/modals"):
        return ("/ui/pages/modals.html", False)
    
    elif original_path.startswith("/styles/") or original_path.startswith("/css/"):
        filename = (original_path.replace("/css/", "") 
                   if original_path.startswith("/css/") 
                   else original_path.replace("/styles/", ""))
        return (f"/ui/styles/{filename}", False)
    
    elif original_path.startswith("/scripts/") or original_path.startswith("/js/"):
        filename = (original_path.replace("/js/", "") 
                   if original_path.startswith("/js/") 
                   else original_path.replace("/scripts/", ""))
        return (f"/ui/scripts/{filename}", False)
    
    return (original_path, False)