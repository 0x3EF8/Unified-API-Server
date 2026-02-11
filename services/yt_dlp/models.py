"""YouTube download models."""

from typing import Optional, List
from pydantic import BaseModel, HttpUrl, field_validator
from enum import Enum


class VideoQuality(str, Enum):
    VIDEO_1080P = "1080p"
    VIDEO_720P = "720p"
    VIDEO_480P = "480p"
    AUDIO_ONLY = "audio"
    BEST = "best"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    M4A = "m4a"
    OPUS = "opus"
    VORBIS = "vorbis"
    WAV = "wav"
    BEST = "best"


class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"
    BEST = "best"


class DownloadRequest(BaseModel):
    """YouTube download request with full yt-dlp configuration."""
    # Required
    url: HttpUrl

    # Basic quality settings
    quality: Optional[VideoQuality] = VideoQuality.VIDEO_720P
    format: Optional[str] = None

    # Audio settings
    audio_format: Optional[AudioFormat] = None
    audio_quality: Optional[str] = None
    extract_audio: bool = False

    # Video settings
    video_codec: Optional[VideoCodec] = None

    # Subtitle settings
    subtitles: bool = False
    subtitle_langs: Optional[List[str]] = None
    embed_subtitles: bool = False

    # Post-processing
    embed_thumbnail: bool = False
    add_metadata: bool = True
    keep_video: bool = False
    write_description: bool = False
    write_info_json: bool = False
    write_thumbnail: bool = False

    # Output template
    output_template: Optional[str] = None

    # Playlist settings
    playlist_start: Optional[int] = 1
    playlist_end: Optional[int] = None
    playlist_items: Optional[str] = None
    max_downloads: Optional[int] = None

    # Download limits
    rate_limit: Optional[str] = None
    max_filesize: Optional[str] = None
    min_filesize: Optional[str] = None

    # Network settings
    proxy: Optional[str] = None

    # Authentication
    username: Optional[str] = None
    password: Optional[str] = None
    cookies_from_browser: Optional[str] = None

    # Advanced
    prefer_free_formats: bool = True
    live_from_start: bool = False
    wait_for_video: Optional[int] = None

    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v):
        from .utils import validate_youtube_url
        if not validate_youtube_url(str(v)):
            raise ValueError("Only YouTube URLs are supported")
        return v
