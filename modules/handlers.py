# Centralized manager for all API endpoints

import json
import cgi
import tempfile
import os
import zipfile
import subprocess
import platform
import threading
import locale
from http import HTTPStatus
from pathlib import Path
from typing import Optional, Tuple, Any

from .paths import (
    USER_DATA_DIR, MEMORIES_STORAGE_DIR, ZIPS_DIR,
    DOWNLOAD_STATE_FILE, FFMPEG_PATH, TRANSLATIONS_FILE, ensure_output_directories_exist
)
from .memories_selector import (
    get_memories_file_path, auto_choose_json, update_memories_file_path,
    is_valid_memories_file
)
from .downloader import MemoriesDownloader
from .fusion_manager import (
    get_fusion_state, set_fusion_running, update_fusion_progress,
    update_fusion_stats, should_stop_fusion, clear_fusion_stop_request,
    request_fusion_stop
)
from .fusion import find_overlay, find_main_asset, process_directory
from .metadata import write_video_metadata, write_photo_metadata
from .logging_manager import get_logger

# Logger initialization
logger = get_logger()

import tkinter as tk
from tkinter import filedialog


def get_system_language() -> str:
    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale and system_locale.startswith('fr'):
            return 'FR'
    except:
        pass
    return 'EN'


def send_json(handler, payload: Any, status: int = HTTPStatus.OK) -> None:
    # Send a JSON response
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(data)


# Downloader API

def handle_api_status(handler) -> None:
    # Get downloader status
    downloader = handler.downloader
    
    if not downloader:
        send_json(handler, {"status": {"running": False, "stopping": False, "total": 0, "completed": 0, "success": 0, "failed": 0, "current_filename": "", "files_per_second": 0, "mb_per_second": 0, "eta_seconds": None}})
        return
    
    send_json(handler, {"status": downloader.get_status()})


def handle_api_start(handler) -> None:
    # Start download
    downloader = handler.downloader
    
    if not downloader:
        send_json(handler, {"ok": False, "error": "Downloader not initialized"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
        return
    
    if downloader.is_running():
        send_json(handler, {"ok": True, "message": "Already running."})
        return
    
    # Vérifier si les items sont chargés, sinon les charger
    if not downloader._manager.items or len(downloader._manager.items) == 0:
        try:
            downloader.load_items()
        except Exception as e:
            send_json(handler, {"ok": False, "error": f"Erreur lors du chargement des items: {str(e)}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
    
    def _worker():
        try:
            downloader.run()
        except Exception as e:
            pass

    threading.Thread(target=_worker, daemon=True).start()
    send_json(handler, {"ok": True})


def handle_api_stop(handler) -> None:
    # Stop download
    downloader = handler.downloader
    
    if downloader:
        downloader.stop()
    
    send_json(handler, {"ok": True})


# Fusion API

def get_available_zips() -> list:
    # Get list of available ZIP folders
    zips = []
    zips_dir = ZIPS_DIR
    if not zips_dir.exists():
        return zips
    
    for item in zips_dir.iterdir():
        if item.is_dir() and item.name.endswith('_extracted'):
            has_pairs = find_main_asset(str(item)) and find_overlay(str(item))
            zips.append({
                "name": item.name,
                "index": item.name.replace('_extracted', ''),
                "has_pairs": has_pairs,
                "is_fused": False,
            })
    
    return sorted(zips, key=lambda x: x["index"])


def handle_api_fusion_zips(handler) -> None:
    # Get list of available ZIPs
    send_json(handler, {"zips": get_available_zips()})


def handle_api_fusion_fused_files(handler) -> None:
    # Get list of fused files
    fused_dir = ZIPS_DIR / "fused"
    files = []
    
    if fused_dir.exists():
        for file in fused_dir.iterdir():
            if file.is_file():
                files.append({
                    "name": file.name,
                    "size": file.stat().st_size,
                })
    
    send_json(handler, {"files": sorted(files, key=lambda x: x["name"])})


def handle_api_fusion_status(handler) -> None:
    # Get current fusion status
    state = get_fusion_state()
    send_json(handler, {"status": state})


def handle_api_fusion_stop(handler) -> None:
    # Stop ongoing fusion
    state = get_fusion_state()
    if not state["running"]:
        send_json(handler, {"ok": False, "error": "No fusion in progress"}, status=HTTPStatus.BAD_REQUEST)
        return
    
    request_fusion_stop()
    send_json(handler, {"ok": True})


def handle_api_fusion_move(handler) -> None:
    # Move fused files to storage folder
    def _move_worker():
        fused_dir = ZIPS_DIR / "fused"
        if not fused_dir.exists():
            return
        
        for file in fused_dir.iterdir():
            if file.is_file():
                try:
                    file.rename(MEMORIES_STORAGE_DIR / file.name)
                except:
                    pass
    
    threading.Thread(target=_move_worker, daemon=True).start()
    send_json(handler, {"ok": True})


def handle_api_fusion_fuse(handler) -> None:
    # Start file fusion
    state = get_fusion_state()
    
    if state["running"]:
        send_json(handler, {"ok": False, "error": "Fusion already in progress"}, status=HTTPStatus.BAD_REQUEST)
        return
    
    set_fusion_running(True)
    update_fusion_progress(0, 0, "")
    update_fusion_stats(0, 0, 0)
    clear_fusion_stop_request()

    def _fusion_worker():
        # Create output directories when fusion starts
        ensure_output_directories_exist()
        
        output_dir = ZIPS_DIR / "fused"
        output_dir.mkdir(exist_ok=True)
        
        memories_data = {}
        try:
            memories_file = get_memories_file_path(ask_user=False)
            if memories_file:
                with open(memories_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    saved_media = raw.get("Saved Media") or raw.get("SavedMedia") or []
                    for idx, entry in enumerate(saved_media, start=1):
                        memories_data[idx] = {
                            "date": entry.get("Date", ""),
                            "location": entry.get("Location", ""),
                            "media_type": entry.get("Media Type", ""),
                        }
        except:
            pass
        
        try:
            extracted_dirs = [
                item for item in ZIPS_DIR.iterdir()
                if item.is_dir() and item.name.endswith('_extracted')
            ]
            
            update_fusion_stats(len(extracted_dirs), 0, 0)
            update_fusion_progress(0, len(extracted_dirs), "")
            
            success_count = 0
            fail_count = 0
            
            for idx, dir_path in enumerate(extracted_dirs):
                if should_stop_fusion():
                    break
                
                update_fusion_progress(
                    current_file=f"Processing {dir_path.name}..."
                )
                
                try:
                    dir_index = int(dir_path.name.split('_')[0])
                except ValueError:
                    dir_index = None
                
                metadata_info = memories_data.get(dir_index, {"date": "", "location": "", "media_type": ""})
                
                def metadata_callback(output_file: str):
                    if metadata_info["date"] and metadata_info["location"]:
                        if metadata_info["media_type"].lower() == "video":
                            write_video_metadata(Path(output_file), metadata_info["date"], metadata_info["location"])
                        else:
                            write_photo_metadata(Path(output_file), metadata_info["date"], metadata_info["location"])
                
                if process_directory(str(dir_path), str(output_dir), str(FFMPEG_PATH), 
                                   on_metadata=metadata_callback):
                    success_count += 1
                else:
                    fail_count += 1
                
                update_fusion_progress(idx + 1)
                update_fusion_stats(success=success_count, failed=fail_count)
        
        except:
            pass
        finally:
            set_fusion_running(False)
            update_fusion_progress(current_file="")

    threading.Thread(target=_fusion_worker, daemon=True).start()
    send_json(handler, {"ok": True})


# Utilities API

def handle_api_close_attempt(handler, close_attempt: dict, close_attempt_lock) -> None:
    # Get close attempt status
    with close_attempt_lock:
        triggered = close_attempt["triggered"]
        close_attempt["triggered"] = False
    send_json(handler, {"close_attempt": triggered})


def handle_api_get_translations(handler) -> None:
    try:
        if TRANSLATIONS_FILE.exists():
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                translations = json.load(f)
        else:
            translations = {"EN": {}, "FR": {}}
        
        translations["selectedLanguage"] = get_system_language()
        send_json(handler, translations)
    except Exception as exc:
        send_json(handler, {"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def handle_api_open_output_folder(handler) -> None:
    # Open output folder
    try:
        storage_path = MEMORIES_STORAGE_DIR
        storage_path.mkdir(parents=True, exist_ok=True)
        
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{storage_path}"')
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(storage_path)])
        else:
            subprocess.Popen(["xdg-open", str(storage_path)])
        
        send_json(handler, {"ok": True, "path": str(storage_path)})
    except Exception as exc:
        send_json(handler, {"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def handle_api_get_storage_path(handler) -> None:
    # Get storage path
    try:
        send_json(handler, {"path": str(MEMORIES_STORAGE_DIR)})
    except Exception as exc:
        send_json(handler, {"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def handle_api_change_storage_path(handler) -> None:
    # Storage path is fixed to default location (no-op)
    try:
        send_json(handler, {
            "success": True,
            "path": str(MEMORIES_STORAGE_DIR),
            "message": "Storage path is fixed to default location."
        })
    except Exception as exc:
        send_json(handler,
            {"error": str(exc)},
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )


def handle_api_pick_storage_folder(handler) -> None:
    # Storage path is fixed to default location (no-op)
    try:
        send_json(handler, {
            "success": True,
            "path": str(MEMORIES_STORAGE_DIR),
            "message": "Storage path is fixed to default location."
        })
    except Exception as exc:
        send_json(handler,
            {"error": str(exc)},
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )


def handle_api_reset_all(handler) -> None:
    # Reset all data: download state and memories history files (but NOT logs)
    try:
        from modules.state import reset_all_state
        from modules.paths import MEMORIES_HISTORY_FILE
        
        # Reset download state
        reset_all_state()
        logger.log("RESET: Download state cleared")
        
        # Reset memories history file if needed
        if MEMORIES_HISTORY_FILE.exists():
            MEMORIES_HISTORY_FILE.unlink()
            logger.log("RESET: Memories history file deleted")
        
        logger.log("RESET: All data has been reset (download state + memories, logs preserved)")
        
        send_json(handler, {
            "success": True,
            "message": "All downloads and memories have been reset"
        })
    except Exception as exc:
        logger.log(f"RESET: Error during reset - {str(exc)}")
        send_json(handler, {"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


# Memories file API

def handle_api_memories_status(handler) -> None:
    # Get memories file status
    try:
        memories_path = get_memories_file_path(ask_user=False)
        if memories_path and memories_path.exists():
            send_json(handler, {
                "exists": True,
                "path": str(memories_path),
                "name": memories_path.name
            })
        else:
            send_json(handler, {"exists": False})
    except Exception as e:
        send_json(handler, {"exists": False, "error": str(e)})


def _extract_memories_json_from_file(handler, file_item) -> Tuple[Optional[bytes], Optional[str]]:
    # Extract and validate memories_history.json file
    is_zip = file_item.filename.lower().endswith('.zip')
    
    file_content = file_item.file.read() if hasattr(file_item, "file") else \
                  (file_item.value.encode("utf-8") if isinstance(file_item.value, str) else file_item.value)
    
    if is_zip:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                tmp_zip.write(file_content)
                tmp_zip_path = tmp_zip.name
            
            try:
                with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                    target_path = "json/memories_history.json"
                    namelist = zip_ref.namelist()
                    
                    if target_path not in namelist:
                        send_json(handler, {
                            "ok": False, 
                            "error": f"memories_history.json file not found in ZIP"
                        }, status=HTTPStatus.BAD_REQUEST)
                        return None, None
                    
                    file_content = zip_ref.read(target_path)
            finally:
                try:
                    os.unlink(tmp_zip_path)
                except:
                    pass
        
        except zipfile.BadZipFile:
            send_json(handler, {"ok": False, "error": "ZIP file is corrupted or invalid"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return None, None
        except Exception as e:
            send_json(handler, {"ok": False, "error": f"Error extracting ZIP: {str(e)}"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return None, None
    else:
        if file_item.filename != "memories_history.json":
            send_json(handler, {
                "ok": False, 
                "error": f"File must be named 'memories_history.json' (found: '{file_item.filename}')"
            }, status=HTTPStatus.BAD_REQUEST)
            return None, None
    
    # Validate JSON
    try:
        json_data = json.loads(file_content.decode("utf-8"))
    except json.JSONDecodeError:
        send_json(handler, {"ok": False, "error": "File is not valid JSON"}, 
                  status=HTTPStatus.BAD_REQUEST)
        return None, None
    
    if "Saved Media" not in json_data and "SavedMedia" not in json_data:
        send_json(handler, {
            "ok": False, 
            "error": "File does not contain expected 'Saved Media' structure"
        }, status=HTTPStatus.BAD_REQUEST)
        return None, None
    
    return file_content, None


def handle_api_memories_upload(handler) -> None:
    # Handle memories file upload
    try:
        content_type = handler.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            send_json(handler, {"ok": False, "error": "Content-Type must be multipart/form-data"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        content_length = int(handler.headers.get("Content-Length", 0))
        if content_length == 0:
            send_json(handler, {"ok": False, "error": "No content"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(content_length),
        }
        
        form = cgi.FieldStorage(fp=handler.rfile, headers=handler.headers, environ=environ)
        
        if "file" not in form:
            send_json(handler, {"ok": False, "error": "No file provided"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        file_item = form["file"]
        if not file_item.filename:
            send_json(handler, {"ok": False, "error": "No file selected"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        file_content, error = _extract_memories_json_from_file(handler, file_item)
        if error or file_content is None:
            return
        
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        memories_file = USER_DATA_DIR / "memories_history.json"
        
        with open(memories_file, "wb") as f:
            f.write(file_content)
        
        if is_valid_memories_file(memories_file):
            update_memories_file_path(memories_file)
            
            # Reload items immediately (not in background)
            try:
                if handler.downloader is not None:
                    if hasattr(handler.downloader, '_json_loader') and handler.downloader._json_loader is not None:
                        handler.downloader._json_loader._memories_file = None
                    handler.downloader.load_items()
                    logger.log("UPLOAD: Memories file loaded and items refreshed")
            except Exception as e:
                logger.log(f"UPLOAD: Error loading items after upload - {str(e)}")
            
            send_json(handler, {"ok": True, "path": str(memories_file)})
        else:
            send_json(handler, {"ok": False, "error": "Invalid file"}, 
                      status=HTTPStatus.BAD_REQUEST)
    
    except Exception as e:
        send_json(handler, {"ok": False, "error": str(e)}, 
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)


def handle_api_memories_auto_import(handler) -> None:
    # Automatically import memories_history.json
    global _downloader
    
    try:
        success, result = auto_choose_json()
        
        if success and result:
            memories_file = Path(result)
            
            if is_valid_memories_file(memories_file):
                update_memories_file_path(memories_file)
                
                def load_items_background():
                    try:
                        if '_downloader' in globals():
                            _downloader._json_loader._memories_file = None
                            _downloader.load_items()
                    except:
                        pass
                
                threading.Thread(target=load_items_background, daemon=True).start()
                send_json(handler, {"ok": True, "path": str(memories_file)})
            else:
                send_json(handler, {"ok": False}, status=HTTPStatus.BAD_REQUEST)
        else:
            send_json(handler, {"ok": False}, status=HTTPStatus.NOT_FOUND)
    except Exception as e:
        send_json(handler, {"ok": False}, status=HTTPStatus.INTERNAL_SERVER_ERROR)


def handle_api_import_new_memories(handler) -> None:
    # Import new memories file and reset downloads
    try:
        content_type = handler.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            send_json(handler, {"error": "Content-Type must be multipart/form-data"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        content_length = int(handler.headers.get("Content-Length", 0))
        if content_length == 0:
            send_json(handler, {"error": "No content"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(content_length),
        }
        
        form = cgi.FieldStorage(fp=handler.rfile, headers=handler.headers, environ=environ)
        
        if "file" not in form:
            send_json(handler, {"error": "No file provided"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        file_item = form["file"]
        if not file_item.filename:
            send_json(handler, {"error": "No file selected"}, 
                      status=HTTPStatus.BAD_REQUEST)
            return
        
        file_content, error = _extract_memories_json_from_file(handler, file_item)
        if error or file_content is None:
            return
        
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        memories_file = USER_DATA_DIR / "memories_history.json"
        
        with open(memories_file, "wb") as f:
            f.write(file_content)
        
        if is_valid_memories_file(memories_file):
            update_memories_file_path(memories_file)
            
            # Reset download state
            try:
                DOWNLOAD_STATE_FILE.unlink(missing_ok=True)
                logger.log("IMPORT: Download state cleared for new import")
            except Exception as e:
                logger.log(f"IMPORT: Error clearing download state - {str(e)}")
            
            # Reload items immediately (not in background)
            try:
                if handler.downloader is not None:
                    handler.downloader._json_loader._memories_file = None
                    handler.downloader.load_items()
                    logger.log("IMPORT: New memories file loaded and items refreshed")
            except Exception as e:
                logger.log(f"IMPORT: Error loading items after import - {str(e)}")
            
            send_json(handler, {"ok": True, "path": str(memories_file)})
        else:
            send_json(handler, {"error": "Invalid file"}, 
                      status=HTTPStatus.BAD_REQUEST)
    
    except Exception as e:
        send_json(handler, {"error": str(e)}, 
                  status=HTTPStatus.INTERNAL_SERVER_ERROR)