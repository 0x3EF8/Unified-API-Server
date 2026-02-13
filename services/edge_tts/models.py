"""TTS request models."""

from typing import Optional
from pydantic import BaseModel, field_validator

from . import config


class TTSRequest(BaseModel):
    """Unified TTS request.

    - Set `list_voices: true` to list available voices (no other fields needed).
    - Set `text` to generate audio with optional voice/rate/pitch/volume.
    """
    text: Optional[str] = None
    voice: Optional[str] = None
    rate: Optional[str] = "+0%"
    pitch: Optional[str] = "+0Hz"
    volume: Optional[str] = "+0%"
    list_voices: bool = False

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Text cannot be empty")
            if len(v) > config.MAX_TEXT_LENGTH:
                raise ValueError(f"Text too long. Maximum {config.MAX_TEXT_LENGTH} characters")
        return v
