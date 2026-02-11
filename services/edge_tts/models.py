"""TTS request models."""

from typing import Optional
from pydantic import BaseModel, field_validator

from . import config


class TTSRequest(BaseModel):
    """TTS generation request with full edge-tts configuration."""
    text: str
    voice: Optional[str] = None
    rate: Optional[str] = "+0%"
    pitch: Optional[str] = "+0Hz"
    volume: Optional[str] = "+0%"

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text is required")
        if len(v) > config.MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long. Maximum {config.MAX_TEXT_LENGTH} characters")
        return v
