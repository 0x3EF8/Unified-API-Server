"""YouTube service configuration."""

import os
from pathlib import Path

OUTPUT_DIR = Path(os.getenv("YTDLP_OUTPUT_DIR", "./cache/yt_dlp"))
MAX_CONCURRENT = int(os.getenv("YTDLP_MAX_CONCURRENT", "3"))
CLEANUP_AFTER = int(os.getenv("YTDLP_CLEANUP_AFTER", "3600"))
RETRY_ATTEMPTS = int(os.getenv("YTDLP_RETRY_ATTEMPTS", "3"))
SOCKET_TIMEOUT = int(os.getenv("YTDLP_SOCKET_TIMEOUT", "30"))
CONCURRENT_FRAGMENTS = int(os.getenv("YTDLP_CONCURRENT_FRAGMENTS", "8"))


def ensure_directories():
    """Create yt_dlp cache directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
