"""YouTube service utilities — FFmpeg detection and URL validation."""

import os
import subprocess
import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and accessible."""
    ffmpeg_path = Path(__file__).parent / "bin" / "ffmpeg.exe"

    if ffmpeg_path.exists():
        bin_dir = str(ffmpeg_path.parent)
        if bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format (youtube.com and youtu.be)."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ["http", "https"]:
            return False
        if not parsed.netloc:
            return False
        if "youtube.com" not in parsed.netloc and "youtu.be" not in parsed.netloc:
            return False
        return True
    except Exception:
        return False


FFMPEG_AVAILABLE = check_ffmpeg()
