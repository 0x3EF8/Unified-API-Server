"""Media Downloader — API documentation and examples.

Auto-loaded by the service loader for the tester Docs tab.
"""

NOTES = [
    "Returns the file directly as a binary download — save to disk",
    "Supports <strong>1000+</strong> sites including YouTube, Facebook, Instagram, TikTok, Twitter/X, Reddit, Vimeo, SoundCloud, Twitch, and more",
    "Use <code>extract_audio: true</code> to get audio-only output",
    "Quality options: <code>best</code>, <code>1080p</code>, <code>720p</code>, <code>480p</code>, <code>audio</code>",
    "The response includes a <code>Content-Disposition</code> header with the original filename",
]

EXAMPLES = [
    {
        "title": "YouTube Video (720p)",
        "description": "Download a YouTube video at 720p quality",
        "body": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "720p"},
    },
    {
        "title": "YouTube Video (Best Quality)",
        "description": "Download at the highest available quality",
        "body": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "best"},
    },
    {
        "title": "YouTube Audio Only (MP3)",
        "description": "Extract just the audio as MP3",
        "body": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "extract_audio": True, "audio_format": "mp3"},
    },
    {
        "title": "YouTube with Subtitles",
        "description": "Download with embedded English subtitles",
        "body": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "subtitles": True, "subtitle_langs": ["en"], "embed_subtitles": True},
    },
    {
        "title": "YouTube Playlist (First 5)",
        "description": "Download the first 5 videos from a playlist",
        "body": {"url": "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf", "playlist_start": 1, "playlist_end": 5},
    },
    {
        "title": "Facebook Video",
        "description": "Download a video from Facebook",
        "body": {"url": "https://www.facebook.com/watch/?v=1234567890", "quality": "720p"},
    },
    {
        "title": "Instagram Reel / Post",
        "description": "Download an Instagram reel or video post",
        "body": {"url": "https://www.instagram.com/reel/ABC123/", "quality": "best"},
    },
    {
        "title": "TikTok Video",
        "description": "Download a TikTok video without watermark",
        "body": {"url": "https://www.tiktok.com/@user/video/1234567890", "quality": "best"},
    },
    {
        "title": "Twitter / X Video",
        "description": "Download a video from a tweet",
        "body": {"url": "https://x.com/user/status/1234567890", "quality": "best"},
    },
    {
        "title": "Reddit Video",
        "description": "Download a video from Reddit",
        "body": {"url": "https://www.reddit.com/r/videos/comments/abc123/example/", "quality": "best"},
    },
    {
        "title": "SoundCloud Audio",
        "description": "Download audio from SoundCloud as MP3",
        "body": {"url": "https://soundcloud.com/artist/track-name", "extract_audio": True, "audio_format": "mp3"},
    },
    {
        "title": "Vimeo Video",
        "description": "Download a Vimeo video",
        "body": {"url": "https://vimeo.com/123456789", "quality": "1080p"},
    },
    {
        "title": "Twitch Clip",
        "description": "Download a Twitch clip",
        "body": {"url": "https://clips.twitch.tv/ClipName", "quality": "best"},
    },
    {
        "title": "Audio Only (M4A Best)",
        "description": "Extract audio in M4A format at best quality",
        "body": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "extract_audio": True, "audio_format": "m4a"},
    },
    {
        "title": "With Metadata & Thumbnail",
        "description": "Download with embedded metadata and thumbnail",
        "body": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "add_metadata": True, "embed_thumbnail": True},
    },
]
