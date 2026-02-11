"""Shared test fixtures."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    with patch('utils.check_internet') as mock:
        mock.return_value = True
        yield mock
