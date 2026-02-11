"""QR Code API endpoints."""

from fastapi import APIRouter, HTTPException, Response
import logging
from datetime import datetime, timezone

from .models import QRRequest, WiFiRequest
from .generator import generate_qr_code, generate_wifi_qr

router = APIRouter(prefix="/qr", tags=["QR Code"])
logger = logging.getLogger(__name__)


@router.post("/generate")
async def qr_generate(request: QRRequest):
    """Generate QR code from data with full configuration."""
    try:
        image_bytes, metadata = generate_qr_code(request)

        ext = request.format.value
        filename = f"qrcode.{ext}"

        logger.info(f"QR generated: {metadata['version']}, {len(image_bytes)} bytes")

        return Response(
            content=image_bytes,
            media_type=metadata['content_type'],
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "public, max-age=3600",
                "X-QR-Version": metadata['version'],
                "X-QR-Error-Correction": metadata['error_correction'],
                "X-QR-Mode": metadata['mode'],
                "X-QR-Is-Micro": str(metadata['is_micro']),
                "X-QR-Modules-Count": str(metadata['modules_count']),
                "X-QR-Size": str(metadata['size']),
                "X-QR-Data-Length": str(metadata['data_length']),
                "X-Generated-At": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )

    except ValueError as e:
        logger.warning(f"QR validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(e)}
        )
    except Exception as e:
        logger.error(f"QR generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e)}
        )


@router.post("/wifi")
async def qr_wifi(request: WiFiRequest):
    """Generate WiFi QR code for network configuration."""
    try:
        image_bytes, metadata = generate_wifi_qr(
            ssid=request.ssid,
            password=request.password,
            security=request.security,
            hidden=request.hidden,
            scale=request.scale,
            border=request.border,
            dark=request.dark,
            light=request.light,
            output_format=request.format
        )

        ext = request.format.value
        filename = f"wifi-{request.ssid.replace(' ', '_')}.{ext}"

        logger.info(f"WiFi QR: {request.ssid}, {len(image_bytes)} bytes")

        return Response(
            content=image_bytes,
            media_type=metadata['content_type'],
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "public, max-age=3600",
                "X-QR-Version": metadata['version'],
                "X-QR-Type": "WiFi",
                "X-WiFi-SSID": metadata['wifi_ssid'],
                "X-WiFi-Security": metadata['wifi_security'],
                "X-QR-Size": str(metadata['size']),
                "X-Generated-At": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }
        )

    except ValueError as e:
        logger.warning(f"WiFi QR validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": str(e)}
        )
    except Exception as e:
        logger.error(f"WiFi QR generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e)}
        )
