"""Shared utilities."""

import socket
import logging

logger = logging.getLogger(__name__)


def check_internet(timeout: int = 5) -> bool:
    """Check for active internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except (OSError, socket.timeout) as e:
        logger.debug(f"Internet check failed: {e}")
        return False
