"""Server configuration."""

import os


class Config:
    """Server-level settings. Service settings live in each service's config.py."""

    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
