"""Text-to-Speech service using Microsoft Edge Neural TTS."""


def setup():
    """Initialize TTS cache directories."""
    from .config import ensure_directories
    ensure_directories()
