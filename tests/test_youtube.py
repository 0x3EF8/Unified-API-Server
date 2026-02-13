"""Tests for download service."""

import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from services.yt_dlp import config as yt_config
from services.yt_dlp.utils import validate_download_url, check_ffmpeg


# ── YouTube Fixtures ──────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def temp_download_dir():
    """Isolate downloads to temp directory per test."""
    temp_dir = Path(tempfile.mkdtemp())
    original = yt_config.OUTPUT_DIR
    yt_config.OUTPUT_DIR = temp_dir
    yield temp_dir
    yt_config.OUTPUT_DIR = original
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_ytdlp(temp_download_dir):
    """Mock yt-dlp for testing without actual downloads."""

    def create_mock_class(opts):
        mock_instance = Mock()
        mock_instance.opts = opts
        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=None)

        def mock_extract_info(url, download=False):
            if download:
                out_tmpl = opts.get("outtmpl", "Test Video.mp4")
                out_path = out_tmpl.replace("%(title)s", "Test Video").replace("%(ext)s", "mp4")
                fake_file = Path(out_path)
                fake_file.parent.mkdir(parents=True, exist_ok=True)
                fake_file.write_bytes(b"fake video data for testing")
            return {
                "title": "Test Video",
                "id": "test123",
                "duration": 120,
                "thumbnail": "https://example.com/thumb.jpg"
            }

        mock_instance.extract_info = mock_extract_info
        mock_instance.download = Mock()
        return mock_instance

    with patch('yt_dlp.YoutubeDL', side_effect=create_mock_class) as mock:
        yield mock


@pytest.fixture
def sample_download_request():
    """Sample YouTube download request data."""
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "quality": "720p"
    }


# ── YouTube Endpoint Tests ───────────────────────────────────────────


@pytest.mark.unit
def test_youtube_download_returns_file(
    test_client: TestClient,
    sample_download_request,
    mock_internet_check,
    mock_ytdlp
):
    """Test successful download returns a file."""
    response = test_client.post("/unidl", json=sample_download_request)

    assert response.status_code == 200
    assert response.headers["content-type"] in ["video/mp4", "application/octet-stream"]
    assert len(response.content) > 0


@pytest.mark.unit
def test_youtube_download_invalid_url(test_client: TestClient, mock_internet_check):
    """Test download fails with invalid URL."""
    response = test_client.post("/unidl", json={
        "url": "ftp://invalid-scheme.com/video",
        "quality": "720p"
    })

    assert response.status_code == 422


@pytest.mark.unit
def test_youtube_download_no_internet(test_client: TestClient):
    """Test download fails when no internet connection."""
    with patch('services.yt_dlp.endpoints.check_internet', return_value=False):
        response = test_client.post("/unidl", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "quality": "720p"
        })

        assert response.status_code == 503


@pytest.mark.unit
def test_youtube_download_quality_options(
    test_client: TestClient,
    mock_internet_check,
    mock_ytdlp
):
    """Test download with different quality options."""
    qualities = ["1080p", "720p", "480p", "audio", "best"]

    for quality in qualities:
        response = test_client.post("/unidl", json={
            "url": "https://www.youtube.com/watch?v=test123",
            "quality": quality
        })

        assert response.status_code == 200
        assert len(response.content) > 0


@pytest.mark.unit
def test_youtube_download_audio_extract(
    test_client: TestClient,
    mock_internet_check,
    mock_ytdlp
):
    """Test download with audio extraction returns a file."""
    response = test_client.post("/unidl", json={
        "url": "https://www.youtube.com/watch?v=test123",
        "extract_audio": True,
        "audio_format": "mp3",
        "audio_quality": "320"
    })

    assert response.status_code == 200
    assert len(response.content) > 0


@pytest.mark.unit
def test_youtube_download_has_filename_header(
    test_client: TestClient,
    mock_internet_check,
    mock_ytdlp
):
    """Test download response includes content-disposition with filename."""
    response = test_client.post("/unidl", json={
        "url": "https://www.youtube.com/watch?v=test123",
        "quality": "720p"
    })

    assert response.status_code == 200
    assert "content-disposition" in response.headers
    assert "filename" in response.headers["content-disposition"]


# ── YouTube URL Validation Tests ─────────────────────────────────────


@pytest.mark.unit
def test_validate_download_url_valid():
    """Test validation accepts valid HTTP/HTTPS URLs."""
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://twitter.com/user/status/123",
        "https://www.reddit.com/r/test/comments/abc/test",
        "https://vimeo.com/123456",
        "https://www.instagram.com/p/abc123",
        "https://www.tiktok.com/@user/video/123",
        "https://soundcloud.com/artist/track",
        "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    for url in valid_urls:
        assert validate_download_url(url) is True, f"Failed for: {url}"


@pytest.mark.unit
def test_validate_download_url_invalid():
    """Test validation rejects invalid URLs."""
    invalid_urls = [
        "not a url",
        "",
        None,
        "ftp://youtube.com/watch?v=test",
        "youtube.com/watch?v=test",
        "just-text",
    ]
    for url in invalid_urls:
        assert validate_download_url(url) is False, f"Should fail for: {url}"


@pytest.mark.unit
def test_validate_download_url_edge_cases():
    """Test URL validation edge cases."""
    assert validate_download_url("") is False
    assert validate_download_url("   ") is False
    assert validate_download_url(12345) is False
    assert validate_download_url([]) is False
    assert validate_download_url({}) is False


@pytest.mark.unit
def test_validate_download_url_with_params():
    """Test validation works with URL parameters."""
    urls_with_params = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest",
        "https://youtu.be/dQw4w9WgXcQ?t=10",
        "https://twitter.com/user/status/123?s=20",
    ]
    for url in urls_with_params:
        assert validate_download_url(url) is True


@pytest.mark.unit
def test_validate_download_url_playlists():
    """Test validation accepts playlist URLs."""
    playlist_urls = [
        "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
        "https://youtube.com/playlist?list=PLtest123",
        "https://soundcloud.com/artist/sets/playlist-name",
    ]
    for url in playlist_urls:
        assert validate_download_url(url) is True


@pytest.mark.unit
def test_validate_download_url_malformed():
    """Test validation rejects malformed URLs."""
    malformed_urls = [
        "htp://youtube.com/watch?v=test",
        "https://noperiod",
        "https:/youtube.com/watch?v=test",
        "youtube.com/watch?v=test",
    ]
    for url in malformed_urls:
        assert validate_download_url(url) is False


# ── FFmpeg Check Tests ───────────────────────────────────────────────


@pytest.mark.unit
def test_check_ffmpeg_available():
    """Test FFmpeg check returns True when installed."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0)
        result = check_ffmpeg()
        assert result is True


@pytest.mark.unit
def test_check_ffmpeg_not_found():
    """Test FFmpeg check returns False when not installed."""
    with patch('subprocess.run', side_effect=FileNotFoundError):
        result = check_ffmpeg()
        assert result is False


@pytest.mark.unit
def test_check_ffmpeg_error():
    """Test FFmpeg check handles subprocess errors."""
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'ffmpeg')):
        result = check_ffmpeg()
        assert result is False
