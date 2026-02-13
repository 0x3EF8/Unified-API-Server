# Unified API Server

FastAPI server with auto-loading service architecture. Drop a folder into `services/` — zero configuration required.

## Services

| Service | Endpoint | Description |
|---------|----------|-------------|
| **TTS** | `POST /tts` | Text-to-speech via Microsoft Edge Neural TTS |
| **Download** | `POST /unidl` | Video/audio download via yt-dlp |
| **QR Code** | `POST /qr` | QR code generation (PNG/SVG/PDF/EPS/TXT) via segno |

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Server starts at `http://localhost:8000`. Override with `API_PORT=3000 python main.py`.

## Usage

### TTS — `POST /tts`

Generate audio:
```json
{"text": "Hello world", "voice": "en-US-JennyNeural", "rate": "+0%", "pitch": "+0Hz"}
```

List all available voices:
```json
{"list_voices": true}
```

### Download — `POST /unidl`

```json
{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "720p"}
```

Returns the file directly with auto-cleanup.

### QR Code — `POST /qr`

Standard QR:
```json
{"data": "https://example.com", "format": "png"}
```

WiFi QR:
```json
{"ssid": "MyNetwork", "password": "secret123", "security": "WPA"}
```

## Project Structure

```
├── main.py              # Entry point
├── config.py            # Server settings (host, port, debug)
├── utils.py             # Shared utilities (internet check)
├── cache/               # All service runtime data
│   ├── tts/             # TTS audio cache
│   └── yt_dlp/          # Download temp files
├── services/
│   ├── __init__.py      # Auto-loader (ServiceLoader)
│   ├── edge_tts/        # TTS service
│   │   ├── config.py    # TTS settings
│   │   ├── models.py    # Request models
│   │   ├── engine.py    # Generation engine
│   │   ├── cache.py     # Audio cache
│   │   └── endpoints.py # API route
│   ├── yt_dlp/          # Download service
│   │   ├── config.py    # Download settings
│   │   ├── models.py    # Request models
│   │   ├── utils.py     # FFmpeg check, URL validation
│   │   ├── dependencies.py # FFmpeg auto-download
│   │   ├── downloader.py   # Download engine with retry
│   │   ├── config_builder.py # yt-dlp options builder
│   │   ├── formats.py   # Quality presets
│   │   └── endpoints.py # API route
│   └── qr/              # QR service
│       ├── models.py    # Request models
│       ├── generator.py # QR engine
│       └── endpoints.py # API route
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
| `API_DEBUG` | `false` | Debug mode (auto-reload) |
| `TTS_CACHE_ENABLED` | `true` | Enable TTS audio caching |
| `TTS_DEFAULT_VOICE` | `en-US-AnaNeural` | Default TTS voice |
| `TTS_MAX_TEXT_LENGTH` | `5000` | Max text length for TTS |
| `YTDLP_RETRY_ATTEMPTS` | `3` | Download retry attempts |
| `YTDLP_SOCKET_TIMEOUT` | `30` | Download socket timeout (s) |

## Testing

```bash
pytest
```
