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


@app.get("/")
async def root():
    """API info and loaded services."""
    service_info = get_loaded_services()
    services = {}
    for name, info in service_info["services"].items():
        router = info["router"]
        prefix = info["prefix"]
        endpoints = []
        for route in router.routes:
            methods = sorted(route.methods - {"HEAD", "OPTIONS"}) if hasattr(route, "methods") else []
            if methods:
                endpoints.append({
                    "path": route.path,
                    "methods": methods,
                    "summary": route.summary or route.name or "",
                })
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
