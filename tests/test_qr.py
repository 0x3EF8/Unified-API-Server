"""Tests for QR code service."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_qr_generate_png(test_client: TestClient):
    """Test QR code generation in PNG format."""
    response = test_client.post("/qr", json={
        "data": "https://example.com",
        "format": "png",
        "micro": False
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0
    assert "X-QR-Version" in response.headers


@pytest.mark.unit
def test_qr_generate_svg(test_client: TestClient):
    """Test QR code generation in SVG format."""
    response = test_client.post("/qr", json={
        "data": "https://example.com",
        "format": "svg",
        "micro": False
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert len(response.content) > 0


@pytest.mark.unit
def test_qr_empty_data_validation(test_client: TestClient):
    """Test QR generation fails with empty data."""
    response = test_client.post("/qr", json={
        "data": ""
    })
    assert response.status_code == 422


@pytest.mark.unit
def test_qr_wifi(test_client: TestClient):
    """Test WiFi QR code generation."""
    response = test_client.post("/qr", json={
        "ssid": "TestNetwork",
        "password": "secret123",
        "security": "WPA"
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "X-WiFi-SSID" in response.headers
    assert response.headers["X-WiFi-SSID"] == "TestNetwork"


@pytest.mark.unit
def test_qr_custom_colors(test_client: TestClient):
    """Test QR code with custom colors."""
    response = test_client.post("/qr", json={
        "data": "colored",
        "dark": "#FF0000",
        "light": "#00FF00",
        "format": "png"
    })
    assert response.status_code == 200
    assert len(response.content) > 0


@pytest.mark.unit
def test_qr_metadata_headers(test_client: TestClient):
    """Test QR response includes metadata headers."""
    response = test_client.post("/qr", json={
        "data": "metadata test"
    })
    assert response.status_code == 200
    assert "X-QR-Version" in response.headers
    assert "X-QR-Error-Correction" in response.headers
    assert "X-QR-Size" in response.headers
    assert "X-QR-Data-Length" in response.headers
    assert "X-Generated-At" in response.headers
