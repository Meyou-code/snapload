from __future__ import annotations

import threading
import sys
import time
import ctypes
import webview
from pathlib import Path
import socket

# Logger initialization
from modules.logging_manager import get_logger
logger = get_logger()

from modules.paths import (
    USER_DATA_DIR, MAX_WORKERS,
    DOWNLOAD_STATE_FILE, MEMORIES_HISTORY_FILE,
    IS_FROZEN, EXIFTOOL_PATH, FFMPEG_PATH, FFPROBE_PATH,
    BUNDLE_ROOT, TOOLS_DIR
)
from modules.server import create_server, set_close_attempt_info
from modules.downloader import MemoriesDownloader
from modules.fusion_manager import get_fusion_state

# Check if another instance is already running
def instance_running(host: str = "127.0.0.1", port: int = 8000) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def focus_existing_window() -> bool:
    try:
        # Find window by title
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Snapchat Memories Downloader")
        
        if hwnd:
            # Show and focus the window
            user32.ShowWindow(hwnd, 5)  # SW_SHOW
            user32.SetForegroundWindow(hwnd)
            return True
    except:
        pass
    return False

logger.log("=== SNAPLOAD STARTUP ===")
app_start = time.time()

# Log application mode
app_mode = "FROZEN" if IS_FROZEN else "DEV"
logger.log(f"Application mode: {app_mode}")

# Log bundle/project root
logger.log(f"Bundle root: {BUNDLE_ROOT} (exists: {BUNDLE_ROOT.exists()})")
logger.log(f"Tools folder: {TOOLS_DIR} (exists: {TOOLS_DIR.exists()})")

# Log external tools paths
logger.log(f"ExifTool: {EXIFTOOL_PATH} (exists: {EXIFTOOL_PATH.exists()})")
logger.log(f"FFmpeg: {FFMPEG_PATH} (exists: {FFMPEG_PATH.exists()})")
logger.log(f"FFprobe: {FFPROBE_PATH} (exists: {FFPROBE_PATH.exists()})")

# Check if it's the first launch
is_first_launch = not DOWNLOAD_STATE_FILE.exists() and not MEMORIES_HISTORY_FILE.exists()
if is_first_launch:
    logger.log("*** FIRST APPLICATION LAUNCH DETECTED ***")


# Global state
close_attempt = {"triggered": False}
close_attempt_lock = threading.Lock()


# Application handlers

def on_window_closing(downloader, fusion_running: bool) -> bool:
    """
    Window closing handler
    Returns False if an operation is in progress (prevents closing),
    True otherwise (allows closing)
    """
    if (downloader and downloader._manager and downloader._manager._running.is_set()) or fusion_running:
        with close_attempt_lock:
            close_attempt["triggered"] = True
        return False
    return True


def background_initialization(downloader):
    try:
        time.sleep(0.5)
        if downloader:
            downloader.load_items()
    except Exception as e:
        pass


# Entry point

if __name__ == "__main__":
    try:
        # Check if another instance is already running
        if instance_running():
            print("Instance already running. Bringing window to focus...\n")
            logger.log("Another instance detected, focusing existing window")
            focus_existing_window()
            sys.exit(0)
        
        print("Snapchat Memories Downloader - starting\n")

        httpd_instance = None
        server_ready = threading.Event()

        # Starting HTTP server
        print("[1/3] Starting HTTP server...")
        server_start = time.time()
        
        def run_server_wrapper(host: str = "127.0.0.1", port: int = 8000) -> None:
            global httpd_instance
            try:
                httpd_instance = create_server(host, port)
                server_ready.set()
                httpd_instance.serve_forever()
            except Exception as e:
                pass
            finally:
                if httpd_instance:
                    try:
                        httpd_instance.server_close()
                    except Exception:
                        pass

        server_thread = threading.Thread(target=run_server_wrapper, daemon=True)
        server_thread.start()

        if not server_ready.wait(timeout=2.0):
            raise TimeoutError("Server startup failed")

        server_time = time.time() - server_start
        print(f"[OK] HTTP server ready ({server_time:.2f}s)")
        logger.log(f"HTTP server started in {server_time:.2f}s")


        # Window configuration
        print("[2/3] Configuring window...")
        window_start = time.time()
        
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        window_width = max(int(screen_width * 0.80), 1000)
        window_height = max(int(screen_height * 0.80), 600)
        
        window_time = time.time() - window_start
        logger.log(f"Window configured in {window_time:.2f}s")

        print(f"[3/3] Initializing downloader...")
        init_start = time.time()
        
        # Downloader initialization
        downloader = None
        
        try:
            downloader = MemoriesDownloader(max_workers=MAX_WORKERS)
        except Exception as e:
            downloader = None
        
        init_time = time.time() - init_start
        logger.log(f"Downloader initialized in {init_time:.2f}s")

        # Configure close attempt info for API handlers
        set_close_attempt_info(close_attempt, close_attempt_lock)
        
        # Set the downloader instance for API handlers
        from modules.server import set_downloader
        if downloader:
            set_downloader(downloader)
        else:
            # Create a fallback downloader if initialization failed
            downloader = MemoriesDownloader(max_workers=MAX_WORKERS)
            set_downloader(downloader)
        
        # Load items initially so UI displays correct state on startup
        if downloader:
            try:
                downloader.load_items()
            except Exception as e:
                pass

        # Interface creation and startup
        print("\nOpening interface...\n")
        window = webview.create_window(
            "Snapchat Memories Downloader",
            "http://127.0.0.1:8000",
            width=window_width,
            height=window_height,
            resizable=True,
            min_size=(1000, 600),
        )
        
        total_startup = time.time() - app_start
        print(f"Application ready! (total startup: {total_startup:.2f}s)")
        print(f"Screen: {screen_width}x{screen_height} | Window: {window_width}x{window_height}\n")
        logger.log(f"Application ready. Total startup time: {total_startup:.2f}s")
        logger.log(f"Mode: {app_mode} | Tools: ExifTool={'OK' if EXIFTOOL_PATH.exists() else 'MISSING'}, FFmpeg={'OK' if FFMPEG_PATH.exists() else 'MISSING'}")

        # Closing handler
        def handle_closing():
            fusion_state = get_fusion_state()
            return on_window_closing(downloader, fusion_state.get("running", False))

        window.events.closing += handle_closing

        # Start interface
        webview.start(debug=False) # ! < CHANGE FOR BUILD ! 

        # Server shutdown
        if httpd_instance:
            try:
                print("\nStopping server...")
                httpd_instance.shutdown()
                print("[OK] Server stopped")
                logger.log("Server stopped")
            except Exception as e:
                pass

    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.log(f"FATAL ERROR: {e}")
        raise

    finally:
        print("\nClosing application...")
        logger.log("Application closed")
        sys.exit(0) 