"""Video quality format mappings for yt-dlp."""

from typing import Dict, Any

from .models import VideoQuality
from .utils import ffmpeg_available


def get_quality_format(quality: VideoQuality) -> Dict[str, Any]:
    """Get yt-dlp format options for specified quality."""
    formats = {
        VideoQuality.VIDEO_1080P: {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "merge_output_format": "mp4",
        },
        VideoQuality.VIDEO_720P: {
            "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4",
        },
        VideoQuality.VIDEO_480P: {
            "format": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
            "merge_output_format": "mp4",
        },
        VideoQuality.AUDIO_ONLY: {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
            if ffmpeg_available()
            else [],
        },
        VideoQuality.BEST: {
            "format": "best",
            "merge_output_format": "mp4",
        },
    }
    return formats.get(quality, formats[VideoQuality.BEST])
