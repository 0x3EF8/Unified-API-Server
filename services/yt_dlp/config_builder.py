"""Converts DownloadRequest models into yt-dlp configuration dictionaries."""

import logging
from typing import Dict, Any
from pathlib import Path

from . import config
from .models import DownloadRequest, VideoQuality
from .utils import FFMPEG_AVAILABLE
from .formats import get_quality_format

logger = logging.getLogger(__name__)


def build_ydl_opts(
    request: DownloadRequest,
    output_dir: Path,
    progress_hook: callable,
) -> Dict[str, Any]:
    """Build yt-dlp options dictionary from DownloadRequest."""

    # Base options
    opts = {
        "quiet": True,
        "no_warnings": True,
        "retries": config.RETRY_ATTEMPTS,
        "socket_timeout": config.SOCKET_TIMEOUT,
        "concurrent_fragment_downloads": config.CONCURRENT_FRAGMENTS if FFMPEG_AVAILABLE else 4,
        "ignoreerrors": False,
        "no_color": True,
        "extractor_retries": 3,
        "fragment_retries": 10,
        "file_access_retries": 3,
        "nocheckcertificate": False,
        "progress_hooks": [progress_hook],
    }

    # Output template
    if request.output_template:
        opts["outtmpl"] = str(output_dir / request.output_template)
    else:
        opts["outtmpl"] = str(output_dir / "%(title)s.%(ext)s")

    # Format selection
    if request.format:
        opts["format"] = request.format
    elif request.extract_audio or request.quality == VideoQuality.AUDIO_ONLY:
        opts["format"] = "bestaudio/best"
        if request.audio_format:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": request.audio_format.value,
                    "preferredquality": request.audio_quality if request.audio_quality else "192",
                }
            ]
    else:
        quality_opts = get_quality_format(request.quality or VideoQuality.VIDEO_720P)
        opts.update(quality_opts)

        if request.video_codec:
            if request.video_codec.value != "best":
                opts["format"] = f"bestvideo[vcodec*={request.video_codec.value}]+bestaudio/best"

    # Audio format/quality (for video downloads with audio)
    if request.audio_format and not request.extract_audio:
        opts["postprocessors"] = opts.get("postprocessors", [])
        opts["postprocessors"].append(
            {
                "key": "FFmpegAudioConvertor",
                "preferredcodec": request.audio_format.value,
            }
        )

    # Subtitles
    if request.subtitles:
        opts["writesubtitles"] = True
        if request.subtitle_langs:
            opts["subtitleslangs"] = request.subtitle_langs
        else:
            opts["subtitleslangs"] = ["en"]

        if request.embed_subtitles and FFMPEG_AVAILABLE:
            opts["postprocessors"] = opts.get("postprocessors", [])
            opts["postprocessors"].append({"key": "FFmpegEmbedSubtitle"})

    # Metadata & Thumbnails
    if request.embed_thumbnail and FFMPEG_AVAILABLE:
        opts["writethumbnail"] = True
        opts["postprocessors"] = opts.get("postprocessors", [])
        opts["postprocessors"].append({"key": "FFmpegThumbnailsConvertor"})
        opts["postprocessors"].append({"key": "EmbedThumbnail"})

    if request.add_metadata:
        opts["postprocessors"] = opts.get("postprocessors", [])
        opts["postprocessors"].append({"key": "FFmpegMetadata"})

    if request.write_thumbnail:
        opts["writethumbnail"] = True

    if request.write_description:
        opts["writedescription"] = True

    if request.write_info_json:
        opts["writeinfojson"] = True

    # Post-processing options
    if request.keep_video:
        opts["keepvideo"] = True

    # Playlist options
    if request.playlist_start:
        opts["playliststart"] = request.playlist_start

    if request.playlist_end:
        opts["playlistend"] = request.playlist_end

    if request.playlist_items:
        opts["playlist_items"] = request.playlist_items

    if request.max_downloads:
        opts["max_downloads"] = request.max_downloads

    # Download limits
    if request.rate_limit:
        opts["ratelimit"] = _parse_size(request.rate_limit)

    if request.max_filesize:
        opts["max_filesize"] = _parse_size(request.max_filesize)

    if request.min_filesize:
        opts["min_filesize"] = _parse_size(request.min_filesize)

    # Network settings
    if request.proxy:
        opts["proxy"] = request.proxy

    # Authentication
    if request.username:
        opts["username"] = request.username

    if request.password:
        opts["password"] = request.password

    if request.cookies_from_browser:
        opts["cookiesfrombrowser"] = (request.cookies_from_browser,)

    # Advanced options
    if request.prefer_free_formats:
        opts["prefer_free_formats"] = True

    if request.live_from_start:
        opts["live_from_start"] = True

    if request.wait_for_video:
        opts["wait_for_video"] = request.wait_for_video

    logger.debug(f"Built ydl_opts with {len(opts)} configuration options")
    return opts


def _parse_size(size_str: str) -> int:
    """Parse size string (e.g., '1M', '500K', '1G') to bytes."""
    size_str = size_str.upper().strip()

    multipliers = {
        "K": 1024,
        "M": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            try:
                num = float(size_str[:-1])
                return int(num * multiplier)
            except ValueError:
                logger.warning(f"Invalid size format: {size_str}")
                return 0

    try:
        return int(size_str)
    except ValueError:
        logger.warning(f"Invalid size format: {size_str}")
        return 0
