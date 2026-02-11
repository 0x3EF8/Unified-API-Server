"""TTS service configuration."""

import os
from pathlib import Path

CACHE_ENABLED = os.getenv("TTS_CACHE_ENABLED", "true").lower() == "true"
CACHE_DIR = Path(os.getenv("TTS_CACHE_DIR", "./cache/tts"))
DEFAULT_VOICE = os.getenv("TTS_DEFAULT_VOICE", "en-US-AnaNeural")
MAX_TEXT_LENGTH = int(os.getenv("TTS_MAX_TEXT_LENGTH", "5000"))


def ensure_directories():
    """Create TTS cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
