"""YouTube downloader with retry logic."""

import asyncio
import logging
from pathlib import Path
from fastapi import HTTPException

import yt_dlp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from . import config
from .models import DownloadRequest
from .status import status
from .config_builder import build_ydl_opts
from utils import check_internet

logger = logging.getLogger(__name__)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(config.RETRY_ATTEMPTS),
    retry=retry_if_exception_type(yt_dlp.utils.DownloadError),
    reraise=True,
)
def _download_with_retry(ydl: yt_dlp.YoutubeDL, url: str) -> dict:
    """Download with automatic retry using exponential backoff."""
    return ydl.extract_info(url, download=True)


async def download_youtube_video(request: DownloadRequest, download_id: str) -> str:
    """Download YouTube video or audio with full configuration support."""

    url = str(request.url)

    # Check internet
    if not check_internet():
        error_msg = "No internet connection"
        logger.error(error_msg)
        status.update(download_id, status="failed", error=error_msg)
        raise HTTPException(status_code=503, detail=error_msg)

    output_dir = config.OUTPUT_DIR / download_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set User-Agent
    yt_dlp.utils.std_headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def progress_hook(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed")
            eta = d.get("eta")

            speed_str = f"{speed/1024/1024:.2f} MB/s" if speed else "N/A"
            eta_str = f"{eta}s" if eta else "N/A"

            if total > 0:
                progress = int((downloaded / total) * 100)
                status.update(
                    download_id,
                    progress=progress,
                    status="downloading",
                    speed=speed_str,
                    eta=eta_str,
                    file_size=total,
                )
        elif d.get("status") == "finished":
            status.update(download_id, status="processing", progress=95)

    # Build yt-dlp options from request
    ydl_opts = build_ydl_opts(request, output_dir, progress_hook)

    try:
        status.update(download_id, status="initializing")

        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                is_playlist = "entries" in info
                if is_playlist:
                    playlist_title = info.get("title", "playlist")
                    playlist_count = len(list(info.get("entries", [])))
                    status.update(
                        download_id,
                        is_playlist=True,
                        playlist_count=playlist_count,
                    )

                    playlist_folder = output_dir / playlist_title[:50]
                    playlist_folder.mkdir(parents=True, exist_ok=True)
                    ydl_opts["outtmpl"] = str(playlist_folder / "%(title)s.%(ext)s")

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_playlist:
                        _download_with_retry(ydl_playlist, url)

                    return str(playlist_folder)
                else:
                    _download_with_retry(ydl, url)
                    return str(output_dir)

        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(None, download)

        # Find downloaded files
        result_dir = Path(result_path)
        files = list(result_dir.glob("*"))

        media_files = [
            f
            for f in files
            if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".mp3", ".m4a", ".opus"]
        ]

        if not media_files:
            raise Exception("No media files downloaded")

        if len(media_files) == 1:
            actual_file = media_files[0]
            file_size = actual_file.stat().st_size
            status.update(
                download_id,
                status="completed",
                progress=100,
                file_path=str(actual_file),
                file_name=actual_file.name,
                file_size=file_size,
                speed=None,
                eta=None,
            )
            logger.info(
                f"Download completed: {download_id} -> {actual_file.name} ({file_size/1024/1024:.2f} MB)"
            )
            return str(actual_file)
        else:
            total_size = sum(f.stat().st_size for f in media_files)
            status.update(
                download_id,
                status="completed",
                progress=100,
                file_path=str(result_dir),
                file_name=f"Playlist ({len(media_files)} files)",
                file_size=total_size,
                speed=None,
                eta=None,
            )
            logger.info(
                f"Playlist completed: {download_id} -> {len(media_files)} files ({total_size/1024/1024:.2f} MB)"
            )
            return str(result_dir)

    except yt_dlp.utils.DownloadError as e:
        error_msg = f"YouTube download error: {str(e)}"
        logger.error(error_msg)
        status.update(download_id, status="failed", error=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        logger.error(error_msg)
        status.update(download_id, status="failed", error=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
