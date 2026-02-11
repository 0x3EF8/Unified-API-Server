"""TTS engine - Text-to-speech generation using Microsoft Edge."""

import io
import logging
from typing import Optional

import edge_tts

from . import config
from .cache import cache
from .voices import resolve_voice

logger = logging.getLogger(__name__)


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
    
    voice = resolve_voice(voice)
    
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
