import json
from pathlib import Path
from typing import Set, Tuple

from .paths import DOWNLOAD_STATE_FILE


def read_state_file() -> Tuple[Set[int], Set[int], int]:
    # Read download_state.json and return (success_ids, failed_ids, total)
    if not DOWNLOAD_STATE_FILE.exists():
        return set(), set(), 0
    
    with DOWNLOAD_STATE_FILE.open("r", encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            return set(), set(), 0
        data = json.loads(text)
    
    success_ids = {int(i) for i in data.get("success", [])}
    failed_ids = {int(i) for i in data.get("failed", [])}
    total = int(data.get("total", 0))
    
    return success_ids, failed_ids, total


def save_state_file(total: int, success_ids: Set[int], failed_ids: Set[int]) -> None:
    # Save current state to download_state.json
    data = {
        "total": total,
        "success": sorted(success_ids),
        "failed": sorted(failed_ids),
    }
    try:
        with DOWNLOAD_STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        pass


def reset_all_state() -> None:
    """Reset all download state by deleting the state file."""
    if DOWNLOAD_STATE_FILE.exists():
        try:
            DOWNLOAD_STATE_FILE.unlink()
        except Exception as e:
            print(f"Error resetting state file: {e}")