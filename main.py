"""Unified API Server - Auto-loading service architecture.

Drop service folders into services/ and they're auto-loaded.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from config import Config
from utils import check_internet
from services import load_service_routers, get_loaded_services

logging.basicConfig(
    level=logging.DEBUG if Config.DEBUG else logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-15s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

startup_time = None


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup and shutdown."""
    global startup_time
    startup_time = datetime.now()

    logger.info("=" * 60)
    logger.info("  UNIFIED API SERVER v1.0")
    logger.info("=" * 60)
    logger.info(f"  Host:  {Config.HOST}:{Config.PORT}")
    logger.info(f"  Debug: {Config.DEBUG}")
    logger.info("=" * 60)

    yield

    logger.info("Server shutting down...")


app = FastAPI(
    title="Unified API Server",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-load all service routers
for router in load_service_routers():
    app.include_router(router)


def _extract_body_fields(route) -> dict:
    """Extract request body fields with defaults from a FastAPI route."""
    try:
        dependant = getattr(route, "dependant", None)
        if not dependant or not dependant.body_params:
            return None
        param = dependant.body_params[0]
        model_class = param.field_info.annotation
        if not hasattr(model_class, "model_fields"):
            return None
        fields = {}
        for field_name, field_info in model_class.model_fields.items():
            default = field_info.default
            if default is ...:
                fields[field_name] = None
            elif default is None:
                fields[field_name] = None
            elif isinstance(default, bool):
                fields[field_name] = default
            elif isinstance(default, (int, float)):
                fields[field_name] = default
            elif isinstance(default, str):
                fields[field_name] = default
            elif hasattr(default, "value"):
                fields[field_name] = default.value
            else:
                fields[field_name] = str(default)
        return fields
    except Exception:
        return None


def _extract_field_info(route) -> list:
    """Extract detailed field metadata for documentation."""
    try:
        dependant = getattr(route, "dependant", None)
        if not dependant or not dependant.body_params:
            return None
        param = dependant.body_params[0]
        model_class = param.field_info.annotation
        if not hasattr(model_class, "model_fields"):
            return None

        fields_info = []
        for field_name, field_info in model_class.model_fields.items():
            # Determine type string
            annotation = field_info.annotation
            type_str = "any"
            if annotation is not None:
                origin = getattr(annotation, "__origin__", None)
                if annotation is str or annotation is type(None):
                    type_str = "string"
                elif annotation is int:
                    type_str = "integer"
                elif annotation is float:
                    type_str = "number"
                elif annotation is bool:
                    type_str = "boolean"
                elif hasattr(annotation, "__members__"):
                    # Enum
                    type_str = "enum: " + ", ".join(f'"{v.value}"' for v in annotation)
                elif origin is not None:
                    args = getattr(annotation, "__args__", ())
                    # Handle Optional[X] = Union[X, None]
                    non_none = [a for a in args if a is not type(None)]
                    if non_none:
                        inner = non_none[0]
                        if inner is str:
                            type_str = "string"
                        elif inner is int:
                            type_str = "integer"
                        elif inner is float:
                            type_str = "number"
                        elif inner is bool:
                            type_str = "boolean"
                        elif hasattr(inner, "__members__"):
                            type_str = "enum: " + ", ".join(f'"{v.value}"' for v in inner)
                        elif hasattr(inner, "__origin__"):
                            # e.g. List[str]
                            type_str = "array"
                        elif hasattr(inner, "__name__") and inner.__name__ == "Url":
                            type_str = "string (URL)"
                        else:
                            type_str = getattr(inner, "__name__", str(inner))

            # Default value
            default = field_info.default
            if default is ...:
                default_val = None
            elif default is None:
                default_val = None
            elif isinstance(default, bool):
                default_val = default
            elif isinstance(default, (int, float)):
                default_val = default
            elif hasattr(default, "value"):
                default_val = default.value
            else:
                default_val = str(default)

            required = field_info.default is ...

            fields_info.append({
                "name": field_name,
                "type": type_str,
                "default": default_val,
                "required": required,
            })
        return fields_info
    except Exception:
        return None


@app.get("/")
async def root():
    """API info and loaded services."""
    service_info = get_loaded_services()
    services = {}

    # Use-case examples for each service endpoint
    use_cases = {
        "/tts": {
            "notes": [
                "Returns audio/mpeg binary — save the response as an .mp3 file",
                "Use <code>list_voices: true</code> to discover all available voices before generating",
                "Rate, pitch, and volume accept percentage strings like <code>\"+50%\"</code> or <code>\"-20%\"</code>",
            ],
            "examples": [
                {
                    "title": "Basic Text to Speech",
                    "description": "Convert text to speech using the default English voice",
                    "body": {"text": "Hello, welcome to the API!", "voice": "en-US-JennyNeural"},
                },
                {
                    "title": "Custom Voice & Speed",
                    "description": "Use a male voice with faster speed and higher pitch",
                    "body": {"text": "Breaking news: AI is amazing!", "voice": "en-US-GuyNeural", "rate": "+30%", "pitch": "+10Hz"},
                },
                {
                    "title": "Multilingual — Spanish",
                    "description": "Generate speech in Spanish",
                    "body": {"text": "Hola, bienvenido a nuestro servicio", "voice": "es-ES-ElviraNeural"},
                },
                {
                    "title": "Multilingual — Japanese",
                    "description": "Generate speech in Japanese with slow speed",
                    "body": {"text": "こんにちは、世界", "voice": "ja-JP-NanamiNeural", "rate": "-20%"},
                },
                {
                    "title": "Multilingual — French",
                    "description": "Generate speech in French with adjusted volume",
                    "body": {"text": "Bonjour le monde, bienvenue!", "voice": "fr-FR-DeniseNeural", "volume": "+20%"},
                },
                {
                    "title": "List All Voices",
                    "description": "Get a list of all available voices grouped by locale",
                    "body": {"list_voices": True},
                },
            ],
        },
        "/qr": {
            "notes": [
                "Returns the QR code image directly — <code>png</code>, <code>svg</code>, <code>pdf</code>, <code>eps</code>, or <code>txt</code>",
                "For WiFi QR codes, use <code>ssid</code> instead of <code>data</code>",
                "Custom colors accept CSS color names, hex (<code>#FF0000</code>), or RGB values",
                "Error correction levels: <strong>L</strong> (7%), <strong>M</strong> (15%), <strong>Q</strong> (25%), <strong>H</strong> (30%)",
            ],
            "examples": [
                {
                    "title": "Website URL",
                    "description": "QR code linking to a website — scan with any phone camera",
                    "body": {"data": "https://github.com"},
                },
                {
                    "title": "YouTube Video Link",
                    "description": "Share a YouTube video via QR code",
                    "body": {"data": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                },
                {
                    "title": "Facebook Profile / Page",
                    "description": "Link to a Facebook page or profile",
                    "body": {"data": "https://www.facebook.com/yourpage"},
                },
                {
                    "title": "Instagram Profile",
                    "description": "Generate a QR code for an Instagram profile",
                    "body": {"data": "https://www.instagram.com/yourprofile"},
                },
                {
                    "title": "TikTok Profile",
                    "description": "Share a TikTok profile via QR code",
                    "body": {"data": "https://www.tiktok.com/@yourusername"},
                },
                {
                    "title": "Twitter / X Profile",
                    "description": "Link to a Twitter/X profile",
                    "body": {"data": "https://x.com/yourusername"},
                },
                {
                    "title": "Email Address (Mailto)",
                    "description": "Opens the email app with a pre-filled recipient",
                    "body": {"data": "mailto:contact@example.com?subject=Hello"},
                },
                {
                    "title": "Phone Number",
                    "description": "Scan to call a phone number directly",
                    "body": {"data": "tel:+1234567890"},
                },
                {
                    "title": "SMS Message",
                    "description": "Opens SMS with a pre-filled message",
                    "body": {"data": "sms:+1234567890?body=Hello from QR!"},
                },
                {
                    "title": "Plain Text",
                    "description": "Encode any text content into a QR code",
                    "body": {"data": "Meeting at 3 PM in Conference Room B"},
                },
                {
                    "title": "vCard (Contact Card)",
                    "description": "Save a contact directly to phone — supports name, phone, email",
                    "body": {"data": "BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nTEL:+1234567890\nEMAIL:john@example.com\nEND:VCARD"},
                },
                {
                    "title": "WiFi Network",
                    "description": "Scan to auto-connect to a WiFi network — no typing passwords",
                    "body": {"ssid": "MyWiFi", "password": "supersecret123", "security": "WPA"},
                },
                {
                    "title": "WiFi (Hidden Network)",
                    "description": "Connect to a hidden WiFi network",
                    "body": {"ssid": "HiddenNet", "password": "secret", "security": "WPA", "hidden": True},
                },
                {
                    "title": "WiFi (Open / No Password)",
                    "description": "QR for an open WiFi network without a password",
                    "body": {"ssid": "CoffeeShop_Free", "security": "nopass"},
                },
                {
                    "title": "Custom Styled QR",
                    "description": "Custom colors, high error correction, SVG format",
                    "body": {"data": "https://example.com", "dark": "#1a1a2e", "light": "#e0e0e8", "error_correction": "H", "format": "svg", "scale": 15, "border": 2},
                },
                {
                    "title": "Calendar Event",
                    "description": "Add an event directly to calendar app",
                    "body": {"data": "BEGIN:VEVENT\nSUMMARY:Team Meeting\nDTSTART:20260301T140000\nDTEND:20260301T150000\nLOCATION:Room 101\nEND:VEVENT"},
                },
                {
                    "title": "Geo Location",
                    "description": "Open a location in maps — great for business addresses",
                    "body": {"data": "geo:40.7128,-74.0060?q=New+York+City"},
                },
            ],
        },
        "/unidl": {
            "notes": [
                "Returns the file directly as a binary download — save to disk",
                "Supports <strong>1000+</strong> sites via yt-dlp: YouTube, Facebook, Instagram, TikTok, Twitter/X, Reddit, Vimeo, SoundCloud, Twitch, and more",
                "Use <code>extract_audio: true</code> to get audio-only output",
                "Quality options: <code>best</code>, <code>1080p</code>, <code>720p</code>, <code>480p</code>, <code>audio</code>",
                "The response includes a <code>Content-Disposition</code> header with the original filename",
            ],
            "examples": [
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
            ],
        },
    }

    for name, info in service_info["services"].items():
        router = info["router"]
        prefix = info["prefix"]
        endpoints = []
        for route in router.routes:
            methods = sorted(route.methods - {"HEAD", "OPTIONS"}) if hasattr(route, "methods") else []
            if methods:
                body_fields = _extract_body_fields(route)
                fields_info = _extract_field_info(route)
                desc = route.description or ""
                # Clean up docstring: take just the first meaningful paragraph
                if desc:
                    desc = desc.strip().split("\n\n")[0].strip()
                ep = {
                    "path": route.path,
                    "methods": methods,
                    "summary": route.summary or route.name or "",
                    "description": desc,
                }
                if body_fields is not None:
                    ep["body_schema"] = body_fields
                if fields_info is not None:
                    ep["fields"] = fields_info
                # Attach use-case examples if available
                route_cases = use_cases.get(route.path)
                if route_cases:
                    ep["use_cases"] = route_cases.get("examples", [])
                    ep["notes"] = route_cases.get("notes", [])
                endpoints.append(ep)
        services[name] = {
            "prefix": prefix,
            "routes": len(endpoints),
            "endpoints": endpoints,
        }
    return {
        "name": "Unified API Server",
        "version": "1.0.0",
        "status": "operational",
        "services": services,
    }


@app.get("/health")
async def health():
    """Health check."""
    uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0
    internet_ok = await asyncio.to_thread(check_internet)
    service_info = get_loaded_services()
    return {
        "status": "healthy" if internet_ok else "degraded",
        "version": "1.0.0",
        "uptime": round(uptime, 2),
        "internet": internet_ok,
        "services_loaded": service_info["total_services"],
        "services_failed": service_info["failed_services"],
        "services": {name: "operational" for name in service_info["services"]},
    }


STATIC_DIR = Path(__file__).parent / "static"


@app.get("/tester")
async def api_tester():
    """Built-in API tester web UI."""
    return FileResponse(STATIC_DIR / "tester.html", media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
    )
