"""Tests for server endpoints and shared utilities."""

import socket

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from utils import check_internet


# ── Server Endpoint Tests ──────────────────────────────────────────────


@pytest.mark.unit
def test_root_endpoint(test_client: TestClient):
    """Test root endpoint returns API information."""
    response = test_client.get("/api")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Unified API Server"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"
    assert "services" in data


@pytest.mark.unit
def test_health_endpoint_healthy(test_client: TestClient, mock_internet_check):
    """Test health endpoint returns healthy status."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "1.0.0"
    assert "uptime" in data
    assert data["uptime"] >= 0
    assert "services" in data


@pytest.mark.unit
def test_health_endpoint_system_info(test_client: TestClient, mock_internet_check):
    """Test health endpoint includes system information."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "internet" in data
    assert "services_loaded" in data
    assert "services_failed" in data
    assert isinstance(data["services_loaded"], int)
    assert isinstance(data["services_failed"], int)


@pytest.mark.unit
def test_health_endpoint_degraded_no_internet(test_client: TestClient):
    """Test health endpoint shows degraded when no internet."""
    with patch('main.check_internet', return_value=False):
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "degraded"
        assert data["internet"] is False


@pytest.mark.unit
def test_root_lists_services(test_client: TestClient):
    """Test root endpoint lists all loaded services."""
    response = test_client.get("/api")

    assert response.status_code == 200
    data = response.json()

    services = data.get("services", {})
    assert isinstance(services, dict)
    assert len(services) >= 2

    for service_name, service_info in services.items():
        assert "prefix" in service_info
        assert "routes" in service_info
        assert isinstance(service_info["routes"], int)
        assert service_info["routes"] > 0


@pytest.mark.integration
def test_health_check_accessibility(test_client: TestClient):
    """Test health check is accessible and returns valid JSON."""
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    data = response.json()
    assert data is not None
    assert isinstance(data, dict)


@pytest.mark.unit
def test_uptime_increases(test_client: TestClient):
    """Test that uptime value is reasonable."""
    import time

    response1 = test_client.get("/health")
    time.sleep(0.1)
    response2 = test_client.get("/health")

    uptime1 = response1.json()["uptime"]
    uptime2 = response2.json()["uptime"]

    assert uptime2 >= uptime1
    assert uptime1 >= 0


@pytest.mark.unit
def test_docs_disabled(test_client: TestClient):
    """Test that /docs and /redoc are disabled."""
    assert test_client.get("/docs").status_code == 404
    assert test_client.get("/redoc").status_code == 404


# ── Shared Utility Tests ──────────────────────────────────────────────


@pytest.mark.unit
def test_check_internet_success():
    """Test internet check returns True when connected."""
    mock_socket = Mock()
    with patch('socket.create_connection', return_value=mock_socket) as mock_conn:
        result = check_internet()
        assert result is True
        mock_conn.assert_called_once()
        mock_socket.close.assert_called_once()


@pytest.mark.unit
def test_check_internet_failure():
    """Test internet check returns False when not connected."""
    with patch('socket.create_connection', side_effect=OSError):
        result = check_internet()
        assert result is False


@pytest.mark.unit
def test_check_internet_timeout():
    """Test internet check handles timeout."""
    with patch('socket.create_connection', side_effect=socket.timeout):
        result = check_internet(timeout=1)
        assert result is False


@pytest.mark.unit
def test_check_internet_custom_timeout():
    """Test internet check uses custom timeout."""
    mock_socket = Mock()
    with patch('socket.create_connection', return_value=mock_socket) as mock_conn:
        check_internet(timeout=2)

        call_args = mock_conn.call_args
        assert call_args[1]['timeout'] == 2
        mock_socket.close.assert_called_once()
