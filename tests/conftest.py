"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_internet_check():
    """Mock internet connectivity to return True."""
    with patch('utils.check_internet', return_value=True) as mock, \
         patch('main.check_internet', return_value=True), \
         patch('services.yt_dlp.endpoints.check_internet', return_value=True):
        yield mock
