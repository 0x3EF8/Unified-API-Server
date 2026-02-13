"""TTS API endpoint — single unified endpoint."""

import logging
from datetime import datetime, timezone

import edge_tts
from fastapi import APIRouter, HTTPException, Response

from . import config
from .models import TTSRequest
from .engine import generate_tts

router = APIRouter(prefix="/tts", tags=["TTS"])
logger = logging.getLogger(__name__)


@router.post("")
async def tts(request: TTSRequest):
    """Unified TTS endpoint.

    - Send `{"list_voices": true}` to list all available voices.
    - Send `{"text": "...", ...}` to generate audio.
    """

    # ── Voice listing mode ──────────────────────────────────────────
    if request.list_voices:
        try:
            all_voices = await edge_tts.list_voices()
        except Exception as e:
            logger.error(f"✗ Failed to fetch voices: {e}")
            raise HTTPException(status_code=500, detail={"success": False, "message": str(e)})

        voices_by_locale = {}
        for v in all_voices:
            locale = v["Locale"]
            voices_by_locale.setdefault(locale, []).append({
                "name": v["ShortName"],
                "gender": v["Gender"],
                "display": v.get("FriendlyName", v["ShortName"]),
            })

        return {
            "total": len(all_voices),
            "default": config.DEFAULT_VOICE,
            "voices": voices_by_locale,
        }

    # ── Generation mode ─────────────────────────────────────────────
    if not request.text:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Provide 'text' to generate audio, or 'list_voices: true' to list voices"},
        )

    try:
        audio_data = await generate_tts(
            request.text,
            request.voice,
            request.rate,
            request.pitch,
            request.volume,
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
                "X-Generated-At": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
        )

    except ValueError as e:
        logger.warning(f"✗ TTS validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Invalid request parameters", "error": {"code": "VALIDATION_ERROR", "message": str(e)}},
        )
    except Exception as e:
        logger.error(f"✗ TTS generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": "TTS generation failed", "error": {"code": "GENERATION_ERROR", "message": str(e)}},
        )
