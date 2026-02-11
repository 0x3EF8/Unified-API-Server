"""TTS cache manager."""

import hashlib
import logging
from typing import Optional

from . import config

logger = logging.getLogger(__name__)


class TTSCache:
    """Manages TTS audio caching."""

    def __init__(self):
        self.hits = 0
        self.misses = 0

        if config.CACHE_ENABLED:
            config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"TTS Cache enabled at: {config.CACHE_DIR}")

    def _get_cache_key(self, text: str, voice: str, rate: str, pitch: str, volume: str) -> str:
        """Generate unique cache key using MD5 hash."""
        content = f"{voice}:{rate}:{pitch}:{volume}:{text}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def get(self, text: str, voice: str, rate: str, pitch: str, volume: str) -> Optional[bytes]:
        """Get cached audio if exists."""
        if not config.CACHE_ENABLED:
            return None

        cache_key = self._get_cache_key(text, voice, rate, pitch, volume)
        cache_path = config.CACHE_DIR / f"{cache_key}.mp3"

        if cache_path.exists():
            self.hits += 1
            logger.debug(f"Cache HIT: {cache_key[:8]}...")
            return cache_path.read_bytes()

        self.misses += 1
        return None

    def set(self, text: str, voice: str, rate: str, pitch: str, volume: str, audio: bytes) -> None:
        """Cache audio data."""
        if not config.CACHE_ENABLED:
            return

        cache_key = self._get_cache_key(text, voice, rate, pitch, volume)
        cache_path = config.CACHE_DIR / f"{cache_key}.mp3"
        cache_path.write_bytes(audio)
        logger.debug(f"Cache SET: {cache_key[:8]}... ({len(audio)} bytes)")


# Global cache instance
cache = TTSCache()
