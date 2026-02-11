"""Download status tracker."""

import threading
from datetime import datetime
from typing import Optional, Dict, List


class DownloadStatus:
    """Thread-safe download status tracker."""

    def __init__(self):
        self.downloads: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, download_id: str, url: str, quality: str) -> None:
        """Create new download entry."""
        with self._lock:
            self.downloads[download_id] = {
                "id": download_id,
                "url": url,
                "quality": quality,
                "status": "pending",
                "progress": 0,
                "speed": None,
                "eta": None,
                "file_path": None,
                "file_name": None,
                "file_size": None,
                "is_playlist": False,
                "playlist_count": 0,
                "error": None,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
            }

    def update(self, download_id: str, **kwargs) -> None:
        """Update download status."""
        with self._lock:
            if download_id in self.downloads:
                self.downloads[download_id].update(kwargs)
                if kwargs.get("status") == "completed":
                    self.downloads[download_id]["completed_at"] = datetime.now().isoformat()

    def get(self, download_id: str) -> Optional[dict]:
        """Get download status."""
        with self._lock:
            return self.downloads.get(download_id)

    def list_all(self) -> List[dict]:
        """List all downloads."""
        with self._lock:
            return list(self.downloads.values())

    def delete(self, download_id: str) -> bool:
        """Delete download entry."""
        with self._lock:
            if download_id in self.downloads:
                del self.downloads[download_id]
                return True
            return False


# Global status instance
status = DownloadStatus()
