"""Media downloader with retry logic."""

import asyncio
import logging
from pathlib import Path

import yt_dlp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from . import config
from .models import DownloadRequest
from .config_builder import build_ydl_opts

logger = logging.getLogger(__name__)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(config.RETRY_ATTEMPTS),
    retry=retry_if_exception_type((yt_dlp.utils.DownloadError, AttributeError, TypeError)),
    reraise=True,
)
def _download_with_retry(url: str, ydl_opts: dict) -> dict:
    """Download with automatic retry using exponential backoff.

    Creates a fresh YoutubeDL instance per attempt to avoid stale state.
    Retries on DownloadError, AttributeError, and TypeError (yt-dlp internals).
    """
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)


async def download_media(request: DownloadRequest, download_id: str) -> str:
    """Download video or audio from any supported site via yt-dlp."""

    url = str(request.url)

    output_dir = config.OUTPUT_DIR / download_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set User-Agent
    yt_dlp.utils.std_headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Build yt-dlp options from request
    ydl_opts = build_ydl_opts(request, output_dir)

    try:
        def download():
            # Probe first (no download) to detect playlists
            with yt_dlp.YoutubeDL({**ydl_opts, "extract_flat": True}) as probe:
                info = probe.extract_info(url, download=False)

            is_playlist = info and "entries" in info
            if is_playlist:
                playlist_title = info.get("title", "playlist")

                playlist_folder = output_dir / playlist_title[:50]
                playlist_folder.mkdir(parents=True, exist_ok=True)
                ydl_opts["outtmpl"] = str(playlist_folder / "%(title)s.%(ext)s")

                _download_with_retry(url, ydl_opts)
                return str(playlist_folder)
            else:
                _download_with_retry(url, ydl_opts)
                return str(output_dir)

        loop = asyncio.get_running_loop()
        result_path = await loop.run_in_executor(None, download)

        # Find downloaded files
        result_dir = Path(result_path)
        files = list(result_dir.glob("*"))

        MEDIA_EXTS = {".mp4", ".webm", ".mkv", ".mp3", ".m4a", ".opus", ".wav", ".ogg", ".flac"}
        SKIP_EXTS = {".json", ".txt", ".description", ".jpg", ".jpeg", ".png", ".webp", ".part", ".ytdl"}

        media_files = [f for f in files if f.is_file() and f.suffix.lower() in MEDIA_EXTS]

        # Fallback: grab any non-metadata file if no known media extension matched
        if not media_files:
            media_files = [f for f in files if f.is_file() and f.suffix.lower() not in SKIP_EXTS]

        if not media_files:
            raise Exception("No media files downloaded")

        if len(media_files) == 1:
            actual_file = media_files[0]
            file_size = actual_file.stat().st_size
            logger.info(
                f"Download completed: {download_id} -> {actual_file.name} ({file_size/1024/1024:.2f} MB)"
            )
            return str(actual_file)
        else:
            total_size = sum(f.stat().st_size for f in media_files)
            logger.info(
                f"Playlist completed: {download_id} -> {len(media_files)} files ({total_size/1024/1024:.2f} MB)"
            )
            return str(result_dir)

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"YouTube download error: {e}")
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        raise
