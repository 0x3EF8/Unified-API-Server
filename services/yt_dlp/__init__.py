"""YouTube download service using yt-dlp."""


def setup():
    """Initialize download directories and FFmpeg."""
    from .config import ensure_directories
    from .dependencies import setup_dependencies
    ensure_directories()
    setup_dependencies()
