"""Tests for TTS service."""

import tempfile
import shutil
from pathlib import Path

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from services.edge_tts import config as tts_config


# ── TTS Fixtures ──────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def temp_cache_dir():
    """Isolate TTS cache to temp directory per test."""
    temp_dir = Path(tempfile.mkdtemp())
    original = tts_config.CACHE_DIR
    tts_config.CACHE_DIR = temp_dir
    yield temp_dir
    tts_config.CACHE_DIR = original
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_edge_tts():
    """Mock Edge TTS for testing without actual generation."""
    with patch('edge_tts.Communicate') as mock:
        mock_instance = Mock()

        def fake_stream():
            async def _generator():
                yield {"type": "audio", "data": b"fake_audio_data"}
                yield {"type": "audio", "data": b"_more_data"}
            return _generator()

        mock_instance.stream = fake_stream
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def sample_tts_request():
    """Sample TTS request data."""
    return {
        "text": "Hello, this is a test.",
        "voice": "en-US-GuyNeural",
        "rate": "+0%",
        "pitch": "+0Hz"
    }


# ── TTS Tests ─────────────────────────────────────────────────────────


@pytest.mark.unit
def test_tts_generate_post_success(test_client: TestClient, sample_tts_request, mock_edge_tts):
    """Test successful TTS generation via POST."""
    response = test_client.post("/tts", json=sample_tts_request)

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert "X-TTS-Voice" in response.headers
    assert "X-Audio-Size" in response.headers
    assert "X-Text-Length" in response.headers
    assert len(response.content) > 0


@pytest.mark.unit
def test_tts_empty_text_validation(test_client: TestClient):
    """Test TTS generation fails with empty text."""
    response = test_client.post("/tts", json={
        "text": "",
        "voice": "en-US-GuyNeural"
    })

    assert response.status_code == 422


@pytest.mark.unit
def test_tts_text_too_long_validation(test_client: TestClient):
    """Test TTS generation fails with text exceeding max length."""
    long_text = "A" * 10000

    response = test_client.post("/tts", json={
        "text": long_text,
        "voice": "en-US-GuyNeural"
    })

    assert response.status_code == 422


@pytest.mark.unit
def test_tts_full_voice_id(test_client: TestClient, mock_edge_tts):
    """Test TTS generation with full voice ID."""
    response = test_client.post("/tts", json={
        "text": "Hello",
        "voice": "en-US-AnaNeural"
    })

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"


@pytest.mark.unit
def test_tts_default_voice(test_client: TestClient, mock_edge_tts):
    """Test TTS generation uses default voice when not specified."""
    response = test_client.post("/tts", json={
        "text": "Hello world"
    })

    assert response.status_code == 200
    assert "X-TTS-Voice" in response.headers


@pytest.mark.unit
def test_tts_rate_adjustment(test_client: TestClient, mock_edge_tts):
    """Test TTS generation with rate adjustment."""
    response = test_client.post("/tts", json={
        "text": "Hello world",
        "voice": "ana",
        "rate": "+20%"
    })

    assert response.status_code == 200
    assert response.headers["X-TTS-Rate"] == "+20%"


@pytest.mark.unit
def test_tts_pitch_adjustment(test_client: TestClient, mock_edge_tts):
    """Test TTS generation with pitch adjustment."""
    response = test_client.post("/tts", json={
        "text": "Hello world",
        "voice": "ana",
        "pitch": "+5Hz"
    })

    assert response.status_code == 200
    assert response.headers["X-TTS-Pitch"] == "+5Hz"


@pytest.mark.unit
def test_tts_metadata_headers(test_client: TestClient, mock_edge_tts):
    """Test TTS response includes all metadata headers."""
    response = test_client.post("/tts", json={
        "text": "Test message",
        "voice": "ana",
        "rate": "+10%",
        "pitch": "-2Hz"
    })

    assert response.status_code == 200

    assert "X-TTS-Voice" in response.headers
    assert "X-TTS-Rate" in response.headers
    assert "X-TTS-Pitch" in response.headers
    assert "X-Audio-Size" in response.headers
    assert "X-Text-Length" in response.headers
    assert "X-Generated-At" in response.headers

    assert response.headers["X-TTS-Rate"] == "+10%"
    assert response.headers["X-TTS-Pitch"] == "-2Hz"
    assert int(response.headers["X-Audio-Size"]) > 0
    assert response.headers["X-Text-Length"] == "12"


@pytest.mark.unit
def test_tts_cache_control_header(test_client: TestClient, mock_edge_tts):
    """Test TTS response includes cache control header."""
    response = test_client.post("/tts", json={
        "text": "Cached content",
        "voice": "ana"
    })

    assert response.status_code == 200
    assert "Cache-Control" in response.headers
    assert "public" in response.headers["Cache-Control"]


@pytest.mark.unit
def test_tts_invalid_json_post(test_client: TestClient):
    """Test POST endpoint handles invalid JSON."""
    response = test_client.post(
        "/tts",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


@pytest.mark.integration
def test_tts_concurrent_requests(test_client: TestClient, mock_edge_tts):
    """Test handling multiple concurrent TTS requests."""
    import concurrent.futures

    def make_request():
        return test_client.post("/tts", json={
            "text": "Concurrent test",
            "voice": "ana"
        })

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request) for _ in range(3)]
        responses = [f.result() for f in futures]

    for response in responses:
        assert response.status_code == 200
        assert len(response.content) > 0
