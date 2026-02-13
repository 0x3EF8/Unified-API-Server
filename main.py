"""Unified API Server - Auto-loading service architecture.

Drop service folders into services/ and they're auto-loaded.
"""

import asyncio
import json
import logging
from collections import deque
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

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

# ── Live Log Streaming ──
_log_clients: list[asyncio.Queue] = []
_log_buffer: deque = deque(maxlen=200)


class SSELogHandler(logging.Handler):
    """Broadcasts log records to SSE clients for live streaming."""

    def emit(self, record):
        try:
            entry = {
                "ts": datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3],
                "level": record.levelname,
                "name": record.name[:20],
                "msg": record.getMessage(),
            }
            _log_buffer.append(entry)
            for q in list(_log_clients):
                try:
                    q.put_nowait(entry)
                except Exception:
                    pass
        except Exception:
            pass


logging.getLogger().addHandler(SSELogHandler())


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


@app.get("/api")
async def api_info():
    """API info and loaded services."""
    service_info = get_loaded_services()
    services = {}
    for name, info in service_info["services"].items():
        router = info["router"]
        prefix = info["prefix"]
        endpoints = []
        for route in router.routes:
            if not getattr(route, "include_in_schema", True):
                continue
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
                # Attach auto-loaded docs (from service docs.py)
                svc_docs = info.get("docs")
                if svc_docs:
                    ep["use_cases"] = svc_docs.get("examples", [])
                    ep["notes"] = svc_docs.get("notes", [])
                    if svc_docs.get("code_examples"):
                        ep["code_examples"] = svc_docs["code_examples"]
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


@app.get("/")
async def api_tester():
    """Built-in API tester web UI."""
    return FileResponse(STATIC_DIR / "tester.html", media_type="text/html")


@app.get("/logs/stream")
async def log_stream():
    """SSE endpoint for live server log streaming."""
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    _log_clients.append(client_queue)

    async def generate():
        try:
            for entry in list(_log_buffer):
                yield f"data: {json.dumps(entry)}\n\n"
            while True:
                try:
                    entry = await asyncio.wait_for(client_queue.get(), timeout=30)
                    yield f"data: {json.dumps(entry)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if client_queue in _log_clients:
                _log_clients.remove(client_queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        reload_excludes=["cache/*", "downloads/*", "*.mp4", "*.webm", "*.mp3", "*.m4a", "*.opus", "*.wav", "*.part", "*.ytdl"] if Config.DEBUG else None,
        timeout_keep_alive=300,
    )
