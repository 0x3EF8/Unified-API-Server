"""TTS engine - Text-to-speech generation using Microsoft Edge."""

import io
import re
import logging
from typing import Optional

import edge_tts

from . import config
from .cache import cache

logger = logging.getLogger(__name__)

# Patterns for rate/pitch/volume normalization
_RATE_RE = re.compile(r'^([+-]?\d+)\s*%%*$')      # "+10%%" or "+10%" → "+10%"
_PITCH_RE = re.compile(r'^([+-]?\d+)\s*(Hz)?$', re.IGNORECASE)  # "-2Hz" or "-2"
_VOL_RE = re.compile(r'^([+-]?\d+)\s*%%*$')


def _normalize_rate(val: str) -> str:
    """Normalize rate: '+10', '+10%', '+10%%' all become '+10%'."""
    val = val.strip()
    m = _RATE_RE.match(val)
    if m:
        return f"{m.group(1)}%"
    # bare number like "+10"
    if re.match(r'^[+-]?\d+$', val):
        return f"{val}%"
    return val


def _normalize_pitch(val: str) -> str:
    """Normalize pitch: '-2', '-2Hz', '-2hz' all become '-2Hz'."""
    val = val.strip()
    m = _PITCH_RE.match(val)
    if m:
        return f"{m.group(1)}Hz"
    return val


def _normalize_volume(val: str) -> str:
    """Normalize volume: '+20', '+20%', '+20%%' all become '+20%'."""
    val = val.strip()
    m = _VOL_RE.match(val)
    if m:
        return f"{m.group(1)}%"
    if re.match(r'^[+-]?\d+$', val):
        return f"{val}%"
    return val


async def generate_tts(
    text: str,
    voice: Optional[str] = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%"
) -> bytes:
    """Generate TTS audio. Checks cache first, generates new audio if not cached."""

    if voice is None:
        voice = config.DEFAULT_VOICE
    
    # Normalize rate/pitch/volume (handles CMD escaping like +10%% → +10%)
    rate = _normalize_rate(rate)
    pitch = _normalize_pitch(pitch)
    volume = _normalize_volume(volume)
    
    # Check cache first
    cached = cache.get(text, voice, rate, pitch, volume)
    if cached:
        return cached
    
    # Generate new audio
    logger.info(f"Generating TTS: voice={voice}, rate={rate}, pitch={pitch}, volume={volume}")
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
    
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    
    audio_data = audio_buffer.getvalue()
    
    if not audio_data:
        raise ValueError("No audio data generated")
    
    # Cache the result
    cache.set(text, voice, rate, pitch, volume, audio_data)
    
    logger.info(f"Generated {len(audio_data)} bytes of audio")
    return audio_data
