"""YouTube API endpoints."""

import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from utils import check_internet
from .models import DownloadRequest
from .downloader import download_youtube_video
from .status import status
from . import config

router = APIRouter(prefix="/unidl", tags=["YouTube"])
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
    """Delete download files and status entry after sending."""
    download_dir = config.OUTPUT_DIR / download_id
    if download_dir.exists():
        shutil.rmtree(download_dir, ignore_errors=True)
        logger.info(f"✓ Cleaned up: {download_id}")
    status.delete(download_id)


@router.post("/fetch")
async def youtube_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Download YouTube video/audio and return the file directly."""

    # Check internet
    if not check_internet():
        logger.error("✗ No internet connection")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "message": "No internet connection available",
                "error": {"code": "NO_INTERNET", "message": "Check your network connection"},
            },
        )

    # Generate download ID
    download_id = hashlib.md5(f"{request.url}{datetime.now()}".encode()).hexdigest()[:16]

    # Determine quality string for logging
    quality_str = request.quality.value if request.quality else "custom"
    if request.extract_audio:
        quality_str = "audio"
    elif request.format:
        quality_str = "custom format"

    # Create status tracking
    status.create(download_id, str(request.url), quality_str)

    logger.info(f"✓ Download started: {download_id} - {request.url} ({quality_str})")

    # Download and wait for completion
    file_path = await download_youtube_video(request, download_id)

    path = Path(file_path)
    filename = path.name
    media_type = MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    safe_ascii = filename.encode("ascii", errors="replace").decode()
    encoded = quote(filename)

    logger.info(f"✓ Sending file: {filename} ({media_type})")

    # Auto-delete files after response is sent
    background_tasks.add_task(_cleanup_download, download_id)

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{encoded}",
        },
    )

