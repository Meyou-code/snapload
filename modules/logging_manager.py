import time
from pathlib import Path

# Global logger instance
_logger_instance = None


class Logger:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(log_message + "\n")


def init_logger(log_file: Path) -> Logger:
    global _logger_instance
    _logger_instance = Logger(log_file)
    return _logger_instance


def get_logger() -> Logger:
    global _logger_instance
    if _logger_instance is None:
        from .paths import USER_DATA_DIR
        _logger_instance = Logger(USER_DATA_DIR / "snapload.log")
    return _logger_instance
