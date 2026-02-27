import threading
from typing import Dict, Any

# Global merge state
fusion_state: Dict[str, Any] = {
    "running": False,
    "progress": {"current": 0, "total": 0, "current_file": ""},
    "stats": {"total": 0, "success": 0, "failed": 0},
}

fusion_lock = threading.Lock()
fusion_stop_event = threading.Event()


def reset_fusion_state() -> None:
    # Reset the merge state
    global fusion_state
    with fusion_lock:
        fusion_state = {
            "running": False,
            "progress": {"current": 0, "total": 0, "current_file": ""},
            "stats": {"total": 0, "success": 0, "failed": 0},
        }
    fusion_stop_event.clear()


def get_fusion_state() -> Dict[str, Any]:
    # Get a copy of the current state
    with fusion_lock:
        return fusion_state.copy()


def set_fusion_running(value: bool) -> None:
    # Set the merge running state
    with fusion_lock:
        fusion_state["running"] = value


def update_fusion_progress(current: int = None, total: int = None, current_file: str = None) -> None:
    # Update the merge progress
    with fusion_lock:
        if current is not None:
            fusion_state["progress"]["current"] = current
        if total is not None:
            fusion_state["progress"]["total"] = total
        if current_file is not None:
            fusion_state["progress"]["current_file"] = current_file


def update_fusion_stats(total: int = None, success: int = None, failed: int = None) -> None:
    # Update the merge statistics
    with fusion_lock:
        if total is not None:
            fusion_state["stats"]["total"] = total
        if success is not None:
            fusion_state["stats"]["success"] = success
        if failed is not None:
            fusion_state["stats"]["failed"] = failed


def request_fusion_stop() -> None:
    # Request the merge to stop
    fusion_stop_event.set()


def should_stop_fusion() -> bool:
    # Check if a stop has been requested
    return fusion_stop_event.is_set()


def clear_fusion_stop_request() -> None:
    # Clear the stop request
    fusion_stop_event.clear()