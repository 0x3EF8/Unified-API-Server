"""TTS API endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Response

from . import config
from .models import TTSRequest
from .engine import generate_tts

router = APIRouter(prefix="/tts", tags=["TTS"])
logger = logging.getLogger(__name__)


@router.post("/generate")
async def tts_generate(request: TTSRequest):
    """Generate TTS audio from text. Returns MP3 with metadata headers."""
    try:
        audio_data = await generate_tts(
            request.text,
            request.voice,
            request.rate,
            request.pitch,
            request.volume
        )
        
        voice_used = request.voice or config.DEFAULT_VOICE
        
        logger.info(f"✓ TTS: {len(audio_data)} bytes, voice={voice_used}, text_len={len(request.text)}")
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600",
                "X-TTS-Voice": voice_used,
                "X-TTS-Rate": request.rate or "+0%",
                "X-TTS-Pitch": request.pitch or "+0Hz",
                "X-TTS-Volume": request.volume or "+0%",
                "X-Audio-Size": str(len(audio_data)),
                "X-Text-Length": str(len(request.text)),
                "X-Generated-At": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )
    
    except ValueError as e:
        logger.warning(f"✗ TTS validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Invalid request parameters",
                "error": {"code": "VALIDATION_ERROR", "message": str(e)}
            }
        )
    except Exception as e:
        logger.error(f"✗ TTS generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "TTS generation failed",
                "error": {"code": "GENERATION_ERROR", "message": str(e)}
            }
        )
