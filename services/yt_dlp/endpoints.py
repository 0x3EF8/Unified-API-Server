"""Download API endpoint."""

import asyncio
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

import yt_dlp

from utils import check_internet
from .models import DownloadRequest
from .downloader import download_media
from . import config

router = APIRouter(prefix="/unidl", tags=["Download"])
logger = logging.getLogger(__name__)


MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".opus": "audio/opus",
    ".wav": "audio/wav",
}


def _cleanup_download(download_id: str):
    """Delete download files after sending."""
    download_dir = config.OUTPUT_DIR / download_id
    if download_dir.exists():
        shutil.rmtree(download_dir, ignore_errors=True)
        logger.info(f"✓ Cleaned up: {download_id}")


@router.post("", summary="Media Downloader")
async def unidl(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Download video or audio from any supported URL.

    Send `{"url": "..."}` with optional quality/format settings.
    Returns the file directly. Supports YouTube, Twitter/X, Reddit,
    Instagram, TikTok, SoundCloud, Vimeo, and 1000+ other sites.
    """

    if not request.url:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "Provide a 'url' to download"},
        )

    if not await asyncio.to_thread(check_internet):
        logger.error("✗ No internet connection")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "No internet connection available",
                "error": {"code": "NO_INTERNET", "message": "Check your network connection"},
            },
        )

    download_id = hashlib.md5(f"{request.url}{datetime.now()}{id(request)}".encode()).hexdigest()[:16]

    quality_str = request.quality.value if request.quality else "custom"
    if request.extract_audio:
        quality_str = "audio"
    elif request.format:
        quality_str = "custom format"

    logger.info(f"✓ Download started: {download_id} - {request.url} ({quality_str})")

    try:
        file_path = await download_media(request, download_id)
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail={"success": False, "message": f"Download error: {e}"})
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"success": False, "message": f"Download failed: {e}"})

    path = Path(file_path)
    filename = path.name
    media_type = MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    safe_ascii = filename.encode("ascii", errors="replace").decode()
    encoded = quote(filename)

    logger.info(f"✓ Sending file: {filename} ({media_type})")

    background_tasks.add_task(_cleanup_download, download_id)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{encoded}",
        },
    )

