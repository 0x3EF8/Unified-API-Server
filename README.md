# Unified API Server

FastAPI server with auto-loading service architecture. Drop a folder into `services/` — zero configuration required.

## Services

| Service | Endpoint | Description |
|---------|----------|-------------|
| **TTS** | `POST /tts/generate` | Text-to-speech via Microsoft Edge Neural TTS |
| **YouTube** | `POST /unidl/fetch` | Video/audio download via yt-dlp |
| **QR Code** | `POST /qr/generate` | QR code generation (PNG/SVG/PDF) via segno |
| | `POST /qr/wifi` | WiFi network QR codes |

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Server starts at `http://localhost:8000`. Override with `API_PORT=3000 python main.py`.

## Project Structure

```
├── main.py              # Entry point
├── config.py            # Server settings (host, port, debug)
├── utils.py             # Shared utilities (internet check)
├── cache/               # All service runtime data
│   ├── tts/             # TTS audio cache
│   └── yt_dlp/          # YouTube downloads
├── services/
│   ├── __init__.py      # Auto-loader (ServiceLoader)
│   ├── edge_tts/        # TTS service (self-contained)
│   │   ├── config.py    # TTS settings
│   │   ├── models.py    # Request models
│   │   ├── engine.py    # Generation engine
│   │   ├── cache.py     # Audio cache
│   │   ├── voices.py    # Voice shortcuts
│   │   └── endpoints.py # API routes
│   ├── yt_dlp/          # YouTube service (self-contained)
│   │   ├── config.py    # Download settings
│   │   ├── models.py    # Request models
│   │   ├── utils.py     # FFmpeg check, URL validation
│   │   ├── setup.py     # FFmpeg auto-download
│   │   ├── downloader.py
│   │   ├── config_builder.py
│   │   ├── formats.py   # Quality presets
│   │   ├── status.py    # Progress tracker
│   │   └── endpoints.py # API routes
│   └── qr/              # QR service (self-contained)
│       ├── models.py    # Request models
│       ├── generator.py # QR engine
│       └── endpoints.py # API routes
└── tests/               # pytest suite
```

## Adding a Service

Create `services/myservice/endpoints.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/myservice", tags=["MyService"])

@router.get("/hello")
async def hello():
    return {"message": "Hello!"}
```

Restart the server. Done.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server host |
| `API_PORT` | `8000` | Server port |
| `API_DEBUG` | `true` | Debug mode (auto-reload) |
| `TTS_CACHE_ENABLED` | `true` | Enable TTS audio caching |
| `TTS_DEFAULT_VOICE` | `en-US-AnaNeural` | Default TTS voice |
| `TTS_MAX_TEXT_LENGTH` | `5000` | Max text length for TTS |
| `YTDLP_MAX_CONCURRENT` | `3` | Max concurrent downloads |

## Testing

```bash
pytest
```
