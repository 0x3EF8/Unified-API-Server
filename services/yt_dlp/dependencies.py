"""YouTube service setup — FFmpeg & Deno auto-download."""

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


def download_deno() -> bool:
    """Download Deno to service bin directory (required by yt-dlp for YouTube)."""
    deno_exe = BIN_DIR / "deno.exe"

    if deno_exe.exists():
        logger.debug(f"Deno already exists at {deno_exe}")
        return True

    try:
        logger.info("Deno not found. Downloading (required for YouTube extraction)...")
        BIN_DIR.mkdir(parents=True, exist_ok=True)

        url = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"
        zip_path = BIN_DIR.parent / "deno_temp.zip"

        logger.info(f"Downloading Deno from GitHub releases...")
        urlretrieve(url, zip_path)
        logger.info("Download complete. Extracting...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extract("deno.exe", BIN_DIR)

        zip_path.unlink(missing_ok=True)
        logger.info(f"Deno installed to {BIN_DIR}")
        return True

    except Exception as e:
        logger.error(f"Failed to download Deno: {e}")
        logger.info("Deno is required for YouTube — install manually: https://deno.land")
        return False


def setup_dependencies():
    """Download FFmpeg and Deno, add bin/ to PATH."""
    download_ffmpeg()
    download_deno()

    bin_path = str(BIN_DIR.absolute())
    if bin_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{bin_path}{os.pathsep}{os.environ.get('PATH', '')}"
        logger.debug(f"Added {bin_path} to PATH")
