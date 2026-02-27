import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler as HTTPHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from .helpers import translate_path, handle_path_redirects
from . import handlers as api_handlers


class RequestHandler(HTTPHandler):    
    # Reference to close attempt state manager
    close_attempt_info = {"data": None, "lock": None}
    
    # Reference to the global downloader instance
    downloader = None
    
    def log_message(self, format, *args):
        # Suppress default request logs
        pass

    def do_OPTIONS(self) -> None:
        # Handle OPTIONS requests for CORS
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        # Handle GET requests
        
        # API routes
        if self.path.startswith("/api/status"):
            api_handlers.handle_api_status(self)
        elif self.path.startswith("/api/close-attempt"):
            close_attempt = self.close_attempt_info.get("data")
            close_attempt_lock = self.close_attempt_info.get("lock")
            if close_attempt and close_attempt_lock:
                api_handlers.handle_api_close_attempt(self, close_attempt, close_attempt_lock)
        
        # Fusion API
        elif self.path.startswith("/api/fusion/zips"):
            api_handlers.handle_api_fusion_zips(self)
        elif self.path.startswith("/api/fusion/fused-files"):
            api_handlers.handle_api_fusion_fused_files(self)
        elif self.path.startswith("/api/fusion/status"):
            api_handlers.handle_api_fusion_status(self)
        
        # Translations
        elif self.path.startswith("/api/translations"):
            api_handlers.handle_api_get_translations(self)
        
        # Storage
        elif self.path.startswith("/api/storage-path"):
            api_handlers.handle_api_get_storage_path(self)
        elif self.path.startswith("/api/open-output-folder"):
            api_handlers.handle_api_open_output_folder(self)
        
        # Memories
        elif self.path.startswith("/api/memories/status"):
            api_handlers.handle_api_memories_status(self)
        
        # UI routes
        else:
            new_path, is_redirect = handle_path_redirects(self.path)
            
            if is_redirect:
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", new_path)
                self.end_headers()
                return
            
            self.path = new_path
            super().do_GET()

    def do_POST(self) -> None:
        # Handle POST requests
        
        # Memories API
        if self.path == "/api/memories/upload":
            api_handlers.handle_api_memories_upload(self)
        elif self.path == "/api/memories/auto-import":
            api_handlers.handle_api_memories_auto_import(self)
        elif self.path == "/api/import-new-memories":
            api_handlers.handle_api_import_new_memories(self)
        
        # Downloader API
        elif self.path == "/api/start":
            api_handlers.handle_api_start(self)
        elif self.path == "/api/stop":
            api_handlers.handle_api_stop(self)
        
        # Fusion API
        elif self.path == "/api/fusion/fuse":
            api_handlers.handle_api_fusion_fuse(self)
        elif self.path == "/api/fusion/stop":
            api_handlers.handle_api_fusion_stop(self)
        elif self.path == "/api/fusion/move":
            api_handlers.handle_api_fusion_move(self)
        
        # Translations
        elif self.path == "/api/translations":
            api_handlers.handle_api_set_translations(self)
        
        # Storage
        elif self.path == "/api/storage-path/change":
            api_handlers.handle_api_change_storage_path(self)
        elif self.path == "/api/storage-path/pick":
            api_handlers.handle_api_pick_storage_folder(self)
        
        # Settings
        elif self.path == "/api/reset-all":
            api_handlers.handle_api_reset_all(self)
        
        else:
            # Handle static files
            path, should_redirect = handle_path_redirects(self.path)
            
            if should_redirect:
                # HTTP redirect
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", path)
                self.end_headers()
                return
            
            # Serve static file
            full_path = translate_path(path)
            from pathlib import Path
            file_path = Path(full_path)
            
            if file_path.exists() and file_path.is_file():
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    
                    # Determine content type
                    content_type = "text/html; charset=utf-8"
                    if full_path.endswith(".css"):
                        content_type = "text/css"
                    elif full_path.endswith(".js"):
                        content_type = "text/javascript"
                    elif full_path.endswith(".png"):
                        content_type = "image/png"
                    elif full_path.endswith(".ico"):
                        content_type = "image/x-icon"
                    elif full_path.endswith(".jpg") or full_path.endswith(".jpeg"):
                        content_type = "image/jpeg"
                    elif full_path.endswith(".svg"):
                        content_type = "image/svg+xml"
                    elif full_path.endswith(".json"):
                        content_type = "application/json"
                    
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def translate_path(self, path: str) -> str:
        # Translate URL path to system path
        return translate_path(path)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    # Create and return HTTP server instance
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    return httpd


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    # Start HTTP server (blocking)
    try:
        httpd = create_server(host, port)
        httpd.serve_forever()
    finally:
        try:
            httpd.server_close()
        except:
            pass


def set_close_attempt_info(close_attempt: dict, close_attempt_lock) -> None:
    # Configure information for handling close attempts
    RequestHandler.close_attempt_info["data"] = close_attempt
    RequestHandler.close_attempt_info["lock"] = close_attempt_lock


def set_downloader(downloader) -> None:
    # Configure the global downloader instance for all handlers
    RequestHandler.downloader = downloader