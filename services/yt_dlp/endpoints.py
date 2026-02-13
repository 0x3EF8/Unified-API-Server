"""Download API endpoint."""

import asyncio
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

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
    ".vtt": "text/vtt",
    ".srt": "application/x-subrip",
    ".ass": "text/x-ssa",
    ".ssa": "text/x-ssa",
}

# Track active playlist downloads for file serving
_active_downloads: dict[str, Path] = {}


def _cleanup_download(download_id: str):
    """Delete download files after sending."""
    _active_downloads.pop(download_id, None)
    download_dir = config.OUTPUT_DIR / download_id
    if download_dir.exists():
        shutil.rmtree(download_dir, ignore_errors=True)
        logger.info(f"✓ Cleaned up: {download_id}")


@router.get("/file/{download_id}/{filename}", summary="Download playlist file", include_in_schema=False)
async def download_file(download_id: str, filename: str, background_tasks: BackgroundTasks):
    """Serve an individual file from a playlist download."""
    base_dir = _active_downloads.get(download_id)
    if not base_dir:
        raise HTTPException(status_code=404, detail="Download expired or not found")

    # Find the file (search recursively in case of subfolder)
    matches = [f for f in base_dir.rglob(filename) if f.is_file()]
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = matches[0]
    # Security: ensure file is inside the download dir
    if not str(file_path.resolve()).startswith(str(base_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    media_type = MEDIA_TYPES.get(file_path.suffix.lower(), "application/octet-stream")
    safe_ascii = file_path.name.encode("ascii", errors="replace").decode()
    encoded = quote(file_path.name)

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{encoded}",
        },
    )


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

    # If result is a directory (playlist), return JSON with file list
    if path.is_dir():
        MEDIA_EXTS = {".mp4", ".webm", ".mkv", ".mp3", ".m4a", ".opus", ".wav", ".ogg", ".flac"}
        SKIP_EXTS = {".json", ".txt", ".description", ".jpg", ".jpeg", ".png", ".webp", ".part", ".ytdl"}

        files = sorted(
            [f for f in path.rglob("*") if f.is_file() and f.suffix.lower() not in SKIP_EXTS],
            key=lambda f: f.name,
        )

        if not files:
            raise HTTPException(status_code=500, detail={"success": False, "message": "No files downloaded"})

        # Store reference so the file endpoint can serve them
        _active_downloads[download_id] = config.OUTPUT_DIR / download_id

        file_list = []
        for f in files:
            file_size = f.stat().st_size
            ext = f.suffix.lower()
            file_list.append({
                "filename": f.name,
                "size": file_size,
                "size_formatted": f"{file_size / 1024 / 1024:.2f} MB" if file_size > 1024 * 1024 else f"{file_size / 1024:.1f} KB",
                "type": "audio" if ext in {".mp3", ".m4a", ".opus", ".wav", ".ogg", ".flac"} else "video",
                "media_type": MEDIA_TYPES.get(ext, "application/octet-stream"),
                "download_url": f"/unidl/file/{download_id}/{quote(f.name)}",
            })

        total_size = sum(f["size"] for f in file_list)
        logger.info(f"✓ Playlist ready: {download_id} -> {len(file_list)} files ({total_size / 1024 / 1024:.2f} MB)")

        # Schedule cleanup after 10 minutes (give user time to download files)
        async def delayed_cleanup():
            await asyncio.sleep(600)
            _cleanup_download(download_id)

        background_tasks.add_task(delayed_cleanup)

        return JSONResponse({
            "success": True,
            "playlist": True,
            "download_id": download_id,
            "total_files": len(file_list),
            "total_size": f"{total_size / 1024 / 1024:.2f} MB",
            "files": file_list,
        })

    filename = path.name
    media_type = MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    safe_ascii = filename.encode("ascii", errors="replace").decode()
    encoded = quote(filename)

    # Check for subtitle files alongside the video
    SUBTITLE_EXTS = {".vtt", ".srt", ".ass", ".ssa"}
    download_dir = config.OUTPUT_DIR / download_id
    subtitle_files = [
        f for f in download_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in SUBTITLE_EXTS
    ]

    if subtitle_files:
        # Return JSON with video + subtitle files for individual download
        _active_downloads[download_id] = download_dir

        file_list = []

        # Add the video/audio file
        file_size = path.stat().st_size
        ext = path.suffix.lower()
        file_list.append({
            "filename": path.name,
            "size": file_size,
            "size_formatted": f"{file_size / 1024 / 1024:.2f} MB" if file_size > 1024 * 1024 else f"{file_size / 1024:.1f} KB",
            "type": "audio" if ext in {".mp3", ".m4a", ".opus", ".wav", ".ogg", ".flac"} else "video",
            "media_type": MEDIA_TYPES.get(ext, "application/octet-stream"),
            "download_url": f"/unidl/file/{download_id}/{quote(path.name)}",
        })

        # Add subtitle files
        for sf in sorted(subtitle_files, key=lambda f: f.name):
            sf_size = sf.stat().st_size
            file_list.append({
                "filename": sf.name,
                "size": sf_size,
                "size_formatted": f"{sf_size / 1024:.1f} KB",
                "type": "subtitle",
                "media_type": MEDIA_TYPES.get(sf.suffix.lower(), "text/plain"),
                "download_url": f"/unidl/file/{download_id}/{quote(sf.name)}",
            })

        total_size = sum(f["size"] for f in file_list)
        logger.info(f"✓ Media + {len(subtitle_files)} subtitle(s) ready: {download_id}")

        async def delayed_cleanup():
            await asyncio.sleep(600)
            _cleanup_download(download_id)

        background_tasks.add_task(delayed_cleanup)

        return JSONResponse({
            "success": True,
            "playlist": False,
            "has_subtitles": True,
            "download_id": download_id,
            "total_files": len(file_list),
            "total_size": f"{total_size / 1024 / 1024:.2f} MB",
            "files": file_list,
        })

    logger.info(f"✓ Sending file: {filename} ({media_type})")

    background_tasks.add_task(_cleanup_download, download_id)

    return FileResponse(
        path=str(path),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_ascii}\"; filename*=UTF-8''{encoded}",
        },
    )

