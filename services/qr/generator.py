"""QR code generation engine using segno library."""

import io
import logging
from typing import Optional, Tuple

import segno

from .models import QRRequest, QRFormat, QRErrorCorrection

logger = logging.getLogger(__name__)


def generate_qr_code(request: QRRequest) -> Tuple[bytes, dict]:
    """Generate QR code from request parameters.

    Args:
        request: QR code generation request with configuration

    Returns:
        Tuple of (image_bytes, metadata_dict)
    """
    try:
        qr = segno.make(
            request.data,
            error=request.error_correction.value if request.error_correction else None,
            micro=request.micro,
            boost_error=request.boost_error
        )

        save_kwargs = {
            'scale': request.scale,
            'border': request.border,
        }

        if request.dark:
            save_kwargs['dark'] = request.dark
        if request.light:
            if request.light.lower() == 'transparent':
                save_kwargs['light'] = None
            else:
                save_kwargs['light'] = request.light

        buffer = io.BytesIO()

        if request.format == QRFormat.PNG:
            qr.save(buffer, kind='png', **save_kwargs)
            content_type = 'image/png'
        elif request.format == QRFormat.SVG:
            save_kwargs['xmldecl'] = False
            save_kwargs['svgns'] = True
            qr.save(buffer, kind='svg', **save_kwargs)
            content_type = 'image/svg+xml'
        elif request.format == QRFormat.PDF:
            qr.save(buffer, kind='pdf', **save_kwargs)
            content_type = 'application/pdf'
        elif request.format == QRFormat.EPS:
            str_buffer = io.StringIO()
            qr.save(str_buffer, kind='eps', **save_kwargs)
            buffer = io.BytesIO(str_buffer.getvalue().encode('utf-8'))
            content_type = 'application/postscript'
        elif request.format == QRFormat.TXT:
            txt_kwargs = {k: v for k, v in save_kwargs.items() if k in ('border',)}
            str_buffer = io.StringIO()
            qr.save(str_buffer, kind='txt', **txt_kwargs)
            buffer = io.BytesIO(str_buffer.getvalue().encode('utf-8'))
            content_type = 'text/plain'
        else:
            raise ValueError(f"Unsupported format: {request.format}")

        metadata = {
            'version': qr.designator,
            'error_correction': qr.error,
            'mode': qr.mode,
            'is_micro': qr.is_micro,
            'size': buffer.tell(),
            'format': request.format.value,
            'data_length': len(request.data),
            'content_type': content_type,
            'modules_count': len(qr.matrix[0]) if qr.matrix else 0
        }

        buffer.seek(0)
        image_bytes = buffer.read()

        logger.info(f"QR: {metadata['version']}, {len(image_bytes)} bytes, format={request.format.value}")

        return image_bytes, metadata

    except Exception as e:
        logger.error(f"QR generation failed: {e}", exc_info=True)
        raise


def generate_wifi_qr(
    ssid: str,
    password: Optional[str],
    security: str,
    hidden: bool,
    scale: int,
    border: int,
    dark: str,
    light: str,
    output_format: QRFormat,
    error_correction: Optional[QRErrorCorrection] = None,
    micro: Optional[bool] = None,
    boost_error: Optional[bool] = True,
) -> Tuple[bytes, dict]:
    """Generate WiFi QR code."""
    try:
        from segno import helpers

        wifi_data = helpers.make_wifi_data(
            ssid=ssid,
            password=password,
            security=security.upper() if security and security.lower() != 'nopass' else None,
            hidden=hidden
        )

        wifi = segno.make(
            wifi_data,
            error=error_correction.value if error_correction else None,
            micro=micro,
            boost_error=boost_error,
        )

        save_kwargs = {
            'scale': scale,
            'border': border,
            'dark': dark,
        }

        if light and light.lower() == 'transparent':
            save_kwargs['light'] = None
        elif light:
            save_kwargs['light'] = light

        buffer = io.BytesIO()

        if output_format == QRFormat.PNG:
            wifi.save(buffer, kind='png', **save_kwargs)
            content_type = 'image/png'
        elif output_format == QRFormat.SVG:
            save_kwargs['xmldecl'] = False
            save_kwargs['svgns'] = True
            wifi.save(buffer, kind='svg', **save_kwargs)
            content_type = 'image/svg+xml'
        elif output_format == QRFormat.PDF:
            wifi.save(buffer, kind='pdf', **save_kwargs)
            content_type = 'application/pdf'
        elif output_format == QRFormat.EPS:
            str_buffer = io.StringIO()
            wifi.save(str_buffer, kind='eps', **save_kwargs)
            buffer = io.BytesIO(str_buffer.getvalue().encode('utf-8'))
            content_type = 'application/postscript'
        elif output_format == QRFormat.TXT:
            txt_kwargs = {k: v for k, v in save_kwargs.items() if k in ('border',)}
            str_buffer = io.StringIO()
            wifi.save(str_buffer, kind='txt', **txt_kwargs)
            buffer = io.BytesIO(str_buffer.getvalue().encode('utf-8'))
            content_type = 'text/plain'
        else:
            wifi.save(buffer, kind='png', **save_kwargs)
            content_type = 'image/png'

        metadata = {
            'version': wifi.designator,
            'error_correction': wifi.error,
            'mode': wifi.mode,
            'is_micro': wifi.is_micro,
            'size': buffer.tell(),
            'format': output_format.value,
            'content_type': content_type,
            'wifi_ssid': ssid,
            'wifi_security': security
        }

        buffer.seek(0)
        image_bytes = buffer.read()

        logger.info(f"WiFi QR: {ssid}, {len(image_bytes)} bytes, format={output_format.value}")

        return image_bytes, metadata

    except Exception as e:
        logger.error(f"WiFi QR generation failed: {e}", exc_info=True)
        raise
