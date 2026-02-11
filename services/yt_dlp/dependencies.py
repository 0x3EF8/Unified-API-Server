"""YouTube service setup — FFmpeg auto-download."""

import os
import zipfile
import logging
from pathlib import Path
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)

BIN_DIR = Path(__file__).parent / "bin"


def download_ffmpeg() -> bool:
    """Download and extract FFmpeg to service bin directory."""
    ffmpeg_exe = BIN_DIR / "ffmpeg.exe"

    if ffmpeg_exe.exists():
        logger.debug(f"FFmpeg already exists at {ffmpeg_exe}")
        return True

    try:
        logger.info("FFmpeg not found. Downloading...")
        BIN_DIR.mkdir(parents=True, exist_ok=True)

        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = BIN_DIR.parent / "ffmpeg_temp.zip"

        logger.info(f"Downloading from {url}")
        urlretrieve(url, zip_path)
        logger.info("Download complete. Extracting...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            bin_files = [f for f in zip_ref.namelist() if "/bin/" in f and f.endswith(".exe")]
            if not bin_files:
                logger.error("No FFmpeg executables found in archive")
                zip_path.unlink(missing_ok=True)
                return False

            for file in bin_files:
                filename = Path(file).name
                with zip_ref.open(file) as source:
                    target_file = BIN_DIR / filename
                    with open(target_file, "wb") as target:
                        target.write(source.read())
                logger.debug(f"Extracted {filename}")

        zip_path.unlink(missing_ok=True)
        logger.info(f"FFmpeg installed to {BIN_DIR}")
        return True

    except Exception as e:
        logger.error(f"Failed to download FFmpeg: {e}")
        logger.info("FFmpeg is optional — install manually: https://ffmpeg.org/download.html")
        return False


def setup_dependencies():
    """Download FFmpeg and add to PATH."""
    ffmpeg_available = download_ffmpeg()

    if ffmpeg_available:
        ffmpeg_bin = str(BIN_DIR.absolute())
        if ffmpeg_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{ffmpeg_bin}{os.pathsep}{os.environ.get('PATH', '')}"
            logger.debug(f"Added {ffmpeg_bin} to PATH")

    return ffmpeg_available
