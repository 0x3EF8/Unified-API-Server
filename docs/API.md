# Unified API Server — API Documentation

Complete reference for every endpoint, parameter, response format, and header.

**Base URL:** `http://localhost:8000`

---

## Table of Contents

- [Overview](#overview)
- [Root & Health](#root--health)
  - [GET /](#get-)
  - [GET /health](#get-health)
- [Text-to-Speech](#text-to-speech---post-tts)
  - [Generate Audio](#generate-audio)
  - [List Voices](#list-voices)
- [QR Code Generator](#qr-code-generator---post-qr)
  - [Standard QR Code](#standard-qr-code)
  - [WiFi QR Code](#wifi-qr-code)
- [Universal Download](#universal-download---post-unidl)
- [Error Handling](#error-handling)
- [Response Headers](#response-headers)
- [Environment Variables](#environment-variables)

---

## Overview

| Service | Endpoint | Method | Description |
|---------|----------|--------|-------------|
| Root | `/` | GET | Server info + loaded services |
| Health | `/health` | GET | Health check with uptime and connectivity |
| TTS | `/tts` | POST | Text-to-speech audio generation |
| QR | `/qr` | POST | QR code generation (standard + WiFi) |
| Download | `/unidl` | POST | Universal video/audio download |

All endpoints accept and return JSON unless returning binary files. Send requests with `Content-Type: application/json`.

---

## Root & Health

### GET /

Returns server status and loaded services.

**Request:**
```bash
curl http://localhost:8000/
```

**Response `200`:**
```json
{
  "name": "Unified API Server",
  "version": "1.0.0",
  "status": "operational",
  "services": {
    "edge_tts": { "prefix": "/tts", "routes": 1 },
    "qr": { "prefix": "/qr", "routes": 1 },
    "yt_dlp": { "prefix": "/unidl", "routes": 1 }
  }
}
```

---

### GET /health

Returns health status, uptime, internet connectivity, and service states.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response `200`:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3456.78,
  "internet": true,
  "services_loaded": 3,
  "services_failed": 0,
  "services": {
    "edge_tts": "operational",
    "qr": "operational",
    "yt_dlp": "operational"
  }
}
```

| Field | Values |
|-------|--------|
| `status` | `"healthy"` (internet OK) or `"degraded"` (no internet) |
| `uptime` | Seconds since server start |

---

## Text-to-Speech — `POST /tts`

Generates speech audio from text using Microsoft Edge Neural TTS, or lists all available voices.

### Generate Audio

Send `text` to generate an MP3 file. Optionally control voice, speed, pitch, and volume.

**All Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `text` | string | **Yes** | — | Text to speak (max 5000 characters) |
| `voice` | string | No | `en-US-AnaNeural` | Voice name (use `list_voices` to see all) |
| `rate` | string | No | `+0%` | Speech speed from `"-50%"` to `"+100%"` |
| `pitch` | string | No | `+0Hz` | Voice pitch from `"-20Hz"` to `"+20Hz"` |
| `volume` | string | No | `+0%` | Loudness from `"-50%"` to `"+100%"` |

**Examples:**

Basic:
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!"}' \
  --output speech.mp3
```

Custom voice + speed:
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a British accent speaking quickly.",
    "voice": "en-GB-RyanNeural",
    "rate": "+30%"
  }' \
  --output british_fast.mp3
```

Full config:
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Every setting configured!",
    "voice": "en-AU-NatashaNeural",
    "rate": "+20%",
    "pitch": "+5Hz",
    "volume": "+30%"
  }' \
  --output full_config.mp3
```

**Python:**
```python
import requests

response = requests.post("http://localhost:8000/tts", json={
    "text": "Hello from Python!",
    "voice": "en-US-JennyNeural",
    "rate": "+10%"
})

with open("speech.mp3", "wb") as f:
    f.write(response.content)

print(f"Voice: {response.headers['X-TTS-Voice']}")
print(f"Size: {response.headers['X-Audio-Size']} bytes")
```

**JavaScript (fetch):**
```javascript
const response = await fetch("http://localhost:8000/tts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: "Hello from JavaScript!",
    voice: "en-US-GuyNeural"
  })
});

const blob = await response.blob();
const url = URL.createObjectURL(blob);
// Play it or download it
```

**Response:** Binary `audio/mpeg` (MP3 file)

**Response Headers:**

| Header | Example | Description |
|--------|---------|-------------|
| `X-TTS-Voice` | `en-US-JennyNeural` | Voice used |
| `X-TTS-Rate` | `+20%` | Rate applied |
| `X-TTS-Pitch` | `+5Hz` | Pitch applied |
| `X-TTS-Volume` | `+30%` | Volume applied |
| `X-Audio-Size` | `28656` | Audio size in bytes |
| `X-Text-Length` | `11` | Input text length |
| `X-Generated-At` | `2026-02-13T10:30:00Z` | UTC timestamp |

**Errors:**

| Status | When |
|--------|------|
| `400` | Missing `text` (and `list_voices` is false) |
| `422` | Empty text string `""` |
| `500` | TTS engine failure |

---

### List Voices

Returns all 400+ available neural voices grouped by locale.

**Request:**
```bash
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"list_voices": true}'
```

**Response `200`:**
```json
{
  "total": 413,
  "default": "en-US-AnaNeural",
  "voices": {
    "en-US": [
      {
        "name": "en-US-JennyNeural",
        "gender": "Female",
        "display": "Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)"
      },
      {
        "name": "en-US-GuyNeural",
        "gender": "Male",
        "display": "Microsoft Server Speech Text to Speech Voice (en-US, GuyNeural)"
      }
    ],
    "en-GB": [
      {
        "name": "en-GB-RyanNeural",
        "gender": "Male",
        "display": "..."
      }
    ]
  }
}
```

**Popular Voices:**

| Voice | Language | Gender |
|-------|----------|--------|
| `en-US-JennyNeural` | English (US) | Female |
| `en-US-GuyNeural` | English (US) | Male |
| `en-US-AnaNeural` | English (US) | Female |
| `en-GB-RyanNeural` | English (UK) | Male |
| `en-GB-SoniaNeural` | English (UK) | Female |
| `en-AU-NatashaNeural` | English (AU) | Female |
| `ja-JP-NanamiNeural` | Japanese | Female |
| `ko-KR-SunHiNeural` | Korean | Female |
| `zh-CN-XiaoxiaoNeural` | Chinese | Female |
| `es-ES-ElviraNeural` | Spanish | Female |
| `fr-FR-DeniseNeural` | French | Female |
| `de-DE-KatjaNeural` | German | Female |

---

## QR Code Generator — `POST /qr`

Generates QR codes in 5 output formats with full color, size, and error correction control. Supports both standard data QR codes and WiFi network QR codes.

### Standard QR Code

**All Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `data` | string | **Yes** | — | Content to encode (max 4296 chars) |
| `format` | string | No | `"png"` | Output format: `"png"`, `"svg"`, `"pdf"`, `"eps"`, `"txt"` |
| `scale` | integer | No | `10` | Module size in pixels (1–100) |
| `border` | integer | No | `4` | Quiet zone width in modules (0+) |
| `dark` | string | No | `"black"` | Dark module color (hex `"#FF0000"` or CSS name `"red"`) |
| `light` | string | No | `"white"` | Light module color (hex, CSS name, or `"transparent"`) |
| `error_correction` | string | No | `"M"` | Error correction level: `"L"` (7%), `"M"` (15%), `"Q"` (25%), `"H"` (30%) |
| `micro` | boolean | No | `null` | `true` = force Micro QR, `false` = force normal, `null` = auto |
| `boost_error` | boolean | No | `true` | Auto-upgrade error correction if data fits |

**Examples:**

Basic PNG:
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{"data": "https://github.com"}' \
  --output qr.png
```

SVG with custom colors:
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://github.com",
    "format": "svg",
    "dark": "#FF0000",
    "light": "transparent"
  }' \
  --output qr.svg
```

Large PDF with high error correction:
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://example.com/very-long-url",
    "format": "pdf",
    "scale": 20,
    "border": 8,
    "error_correction": "H"
  }' \
  --output qr.pdf
```

All 5 formats:
```bash
# PNG (raster image)
curl -X POST http://localhost:8000/qr -H "Content-Type: application/json" \
  -d '{"data": "hello", "format": "png"}' --output qr.png

# SVG (vector, scalable)
curl -X POST http://localhost:8000/qr -H "Content-Type: application/json" \
  -d '{"data": "hello", "format": "svg"}' --output qr.svg

# PDF (print-ready)
curl -X POST http://localhost:8000/qr -H "Content-Type: application/json" \
  -d '{"data": "hello", "format": "pdf"}' --output qr.pdf

# EPS (vector, Adobe)
curl -X POST http://localhost:8000/qr -H "Content-Type: application/json" \
  -d '{"data": "hello", "format": "eps"}' --output qr.eps

# TXT (ASCII art)
curl -X POST http://localhost:8000/qr -H "Content-Type: application/json" \
  -d '{"data": "hello", "format": "txt"}' --output qr.txt
```

Micro QR (smaller, for short data):
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{"data": "Hi", "micro": true}' \
  --output micro.png
```

Full config:
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{
    "data": "Full config example",
    "format": "png",
    "scale": 15,
    "border": 2,
    "dark": "#1a1a2e",
    "light": "#e0e0e0",
    "error_correction": "Q",
    "micro": false,
    "boost_error": false
  }' \
  --output full_config.png
```

**Python:**
```python
import requests

response = requests.post("http://localhost:8000/qr", json={
    "data": "https://github.com",
    "format": "svg",
    "dark": "#0066FF",
    "scale": 15
})

with open("qr.svg", "wb") as f:
    f.write(response.content)

print(f"Version: {response.headers['X-QR-Version']}")
print(f"Size: {response.headers['X-QR-Size']}")
```

**JavaScript (fetch):**
```javascript
const response = await fetch("http://localhost:8000/qr", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    data: "https://github.com",
    format: "png",
    dark: "#FF0000",
    scale: 20
  })
});

const blob = await response.blob();
const url = URL.createObjectURL(blob);
document.getElementById("qr-img").src = url;
```

**Response:** Binary file in the requested format

| Format | Content-Type |
|--------|-------------|
| `png` | `image/png` |
| `svg` | `image/svg+xml` |
| `pdf` | `application/pdf` |
| `eps` | `application/postscript` |
| `txt` | `text/plain` |

**Response Headers:**

| Header | Example | Description |
|--------|---------|-------------|
| `X-QR-Version` | `2` | QR code version (1–40) |
| `X-QR-Error-Correction` | `M` | Error correction level used |
| `X-QR-Mode` | `byte` | Data encoding mode |
| `X-QR-Is-Micro` | `False` | Whether Micro QR was used |
| `X-QR-Modules-Count` | `25` | Matrix size (modules per side) |
| `X-QR-Size` | `250x250` | Image dimensions |
| `X-QR-Data-Length` | `19` | Input data length |
| `X-Generated-At` | `2026-02-13T10:30:00Z` | UTC timestamp |

---

### WiFi QR Code

Generates a QR code that connects devices to a WiFi network when scanned.

**All Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ssid` | string | **Yes** | — | Network name |
| `password` | string | No | — | Network password (not needed for open networks) |
| `security` | string | No | `"WPA"` | Security type: `"WPA"`, `"WEP"`, or `"nopass"` |
| `hidden` | boolean | No | `false` | Whether the network is hidden |
| `format` | string | No | `"png"` | Output format (same options as standard QR) |
| `scale` | integer | No | `10` | Module size (1–100) |
| `border` | integer | No | `4` | Quiet zone width |
| `dark` | string | No | `"black"` | Dark module color |
| `light` | string | No | `"white"` | Light module color |
| `error_correction` | string | No | `"M"` | Error correction: `"L"`, `"M"`, `"Q"`, `"H"` |
| `micro` | boolean | No | `null` | Force Micro QR (true/false/null) |
| `boost_error` | boolean | No | `true` | Auto-upgrade error correction |

**Examples:**

WPA network:
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "MyHomeNetwork",
    "password": "SuperSecret123",
    "security": "WPA"
  }' \
  --output wifi.png
```

Open network (no password):
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "CoffeeShop-Free",
    "security": "nopass"
  }' \
  --output wifi_open.png
```

Hidden network with custom styling:
```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "SecretNetwork",
    "password": "MyPassword!",
    "security": "WPA",
    "hidden": true,
    "format": "svg",
    "dark": "#FF6600",
    "light": "#FFFFFF",
    "scale": 15
  }' \
  --output wifi_styled.svg
```

**WiFi Response Headers:**

| Header | Example | Description |
|--------|---------|-------------|
| `X-QR-Version` | `4` | QR code version |
| `X-QR-Type` | `WiFi` | Always `"WiFi"` |
| `X-WiFi-SSID` | `MyHomeNetwork` | Network name |
| `X-WiFi-Security` | `WPA` | Security type |
| `X-QR-Size` | `330x330` | Image dimensions |
| `X-Generated-At` | `2026-02-13T10:30:00Z` | UTC timestamp |

**Errors:**

| Status | When |
|--------|------|
| `400` | Neither `data` nor `ssid` provided |
| `422` | Empty `data` or `ssid` string |
| `500` | QR generation failure |

---

## Universal Download — `POST /unidl`

Downloads video or audio from **YouTube, Twitter/X, Reddit, Instagram, TikTok, SoundCloud, Vimeo, Dailymotion, and 1000+ other sites** via yt-dlp. Returns the file directly.

### All Parameters

**Basic:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | **Yes** | — | Any valid HTTP/HTTPS media URL |
| `quality` | string | No | `"720p"` | `"1080p"`, `"720p"`, `"480p"`, `"audio"`, `"best"` |
| `format` | string | No | `null` | Raw yt-dlp format string (advanced override) |

**Audio:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `extract_audio` | boolean | `false` | Extract audio only from video |
| `audio_format` | string | `null` | `"mp3"`, `"m4a"`, `"opus"`, `"vorbis"`, `"wav"`, `"best"` |
| `audio_quality` | string | `null` | Bitrate, e.g. `"192"` (kbps) |

**Video:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_codec` | string | `null` | `"h264"`, `"h265"`, `"vp9"`, `"av1"`, `"best"` |

**Subtitles:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subtitles` | boolean | `false` | Download subtitles (returned as separate files) |
| `subtitle_langs` | array | `null` | Language codes, e.g. `["en", "es"]` |

**Post-processing:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `embed_thumbnail` | boolean | `false` | Embed thumbnail in file |
| `add_metadata` | boolean | `true` | Add metadata tags |
| `keep_video` | boolean | `false` | Keep video file when extracting audio |
| `write_description` | boolean | `false` | Save `.description` file |
| `write_info_json` | boolean | `false` | Save `.info.json` file |
| `write_thumbnail` | boolean | `false` | Save thumbnail image separately |

**Output:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_template` | string | `null` | Custom yt-dlp output template |

**Playlist:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `playlist_start` | integer | `1` | Start from this item number |
| `playlist_end` | integer | `null` | Stop at this item number |
| `playlist_items` | string | `null` | Specific items, e.g. `"1,3,5-7"` |
| `max_downloads` | integer | `null` | Maximum items to download |

**Limits:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate_limit` | string | `null` | Speed limit, e.g. `"1M"` (1 MB/s) |
| `max_filesize` | string | `null` | Max file size, e.g. `"100M"` |
| `min_filesize` | string | `null` | Min file size, e.g. `"1M"` |

**Network:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `proxy` | string | `null` | Proxy URL |

**Advanced:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefer_free_formats` | boolean | `true` | Prefer free/open codecs |
| `live_from_start` | boolean | `false` | Start livestreams from beginning |
| `wait_for_video` | integer | `null` | Seconds to wait for scheduled livestream |

### Examples

**YouTube video (720p default):**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  --output video.mp4
```

**YouTube at 1080p:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "1080p"
  }' \
  --output video_1080.mp4
```

**Extract audio as MP3:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "extract_audio": true,
    "audio_format": "mp3"
  }' \
  --output audio.mp3
```

**Audio-only quality preset:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "audio"
  }' \
  --output audio.mp3
```

**SoundCloud track:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://soundcloud.com/artist/track-name",
    "quality": "audio"
  }' \
  --output track.mp3
```

**Twitter/X video:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://twitter.com/user/status/123456789",
    "quality": "best"
  }' \
  --output tweet.mp4
```

**Instagram reel:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reel/ABC123/",
    "quality": "best"
  }' \
  --output reel.mp4
```

**Reddit video:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.reddit.com/r/sub/comments/abc123/title/",
    "quality": "720p"
  }' \
  --output reddit.mp4
```

**TikTok video:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.tiktok.com/@user/video/123456",
    "quality": "best"
  }' \
  --output tiktok.mp4
```

**Video with embedded subtitles + thumbnail:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "1080p",
    "subtitles": true,
    "subtitle_langs": ["en"],
    "embed_thumbnail": true,
    "add_metadata": true
  }' \
  --output video_with_subs.mp4
```

**Rate-limited download with proxy:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "480p",
    "rate_limit": "2M",
    "proxy": "http://proxy.example.com:8080"
  }' \
  --output video.mp4
```

**Full config:**
```bash
curl -X POST http://localhost:8000/unidl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "1080p",
    "video_codec": "h264",
    "subtitles": true,
    "subtitle_langs": ["en", "es"],
    "embed_thumbnail": true,
    "add_metadata": true,
    "prefer_free_formats": false,
    "rate_limit": "5M"
  }' \
  --output full_config.mp4
```

**Python:**
```python
import requests

response = requests.post("http://localhost:8000/unidl", json={
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "quality": "720p"
})

# Get filename from Content-Disposition header
filename = response.headers.get("Content-Disposition", "video.mp4")
# Parse actual filename
if "filename=" in filename:
    filename = filename.split("filename=")[1].strip('"').split(";")[0]

with open(filename, "wb") as f:
    f.write(response.content)

print(f"Downloaded: {filename} ({len(response.content)} bytes)")
```

**JavaScript (Node.js):**
```javascript
const fs = require("fs");

const response = await fetch("http://localhost:8000/unidl", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    quality: "720p"
  })
});

const buffer = await response.arrayBuffer();
fs.writeFileSync("video.mp4", Buffer.from(buffer));
```

**Response:** Binary file as attachment (auto-deleted from server after send)

| File Type | Content-Type |
|-----------|-------------|
| `.mp4` | `video/mp4` |
| `.webm` | `video/webm` |
| `.mkv` | `video/x-matroska` |
| `.mp3` | `audio/mpeg` |
| `.m4a` | `audio/mp4` |
| `.opus` | `audio/opus` |
| `.wav` | `audio/wav` |
| Other | `application/octet-stream` |

**Errors:**

| Status | When |
|--------|------|
| `400` | Missing `url`, or yt-dlp download error |
| `422` | Invalid URL format |
| `500` | Internal server error |
| `503` | No internet connection |

---

## Error Handling

All errors return JSON:

```json
{
  "success": false,
  "message": "Human-readable error description",
  "error": {
    "code": "ERROR_CODE",
    "message": "Technical details"
  }
}
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request (missing required fields, download error) |
| `422` | Validation error (empty strings, invalid URLs) |
| `500` | Internal server error |
| `503` | Service unavailable (no internet) |

---

## Response Headers

Every successful response includes:

| Header | Present On | Description |
|--------|-----------|-------------|
| `Content-Disposition` | All files | `inline` (TTS, QR) or `attachment` (Download) |
| `Cache-Control` | TTS, QR | `public, max-age=3600` |
| `X-Generated-At` | TTS, QR | UTC ISO timestamp |

---

## Environment Variables

Configure the server and services via environment variables:

**Server:**

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |
| `API_DEBUG` | `false` | Debug mode (enables auto-reload) |

**TTS Service:**

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_CACHE_ENABLED` | `true` | Cache generated audio |
| `TTS_CACHE_DIR` | `./cache/tts` | Cache directory path |
| `TTS_DEFAULT_VOICE` | `en-US-AnaNeural` | Default voice when none specified |
| `TTS_MAX_TEXT_LENGTH` | `5000` | Maximum text input length |

**Download Service:**

| Variable | Default | Description |
|----------|---------|-------------|
| `YTDLP_OUTPUT_DIR` | `./cache/yt_dlp` | Temp download directory |
| `YTDLP_RETRY_ATTEMPTS` | `3` | Number of retry attempts |
| `YTDLP_SOCKET_TIMEOUT` | `30` | Socket timeout in seconds |
| `YTDLP_CONCURRENT_FRAGMENTS` | `8` | Concurrent download fragments |

**Example:**
```bash
API_PORT=3000 TTS_DEFAULT_VOICE=en-GB-RyanNeural python main.py
```
