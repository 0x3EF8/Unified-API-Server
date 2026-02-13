"""QR code models."""

from typing import Optional
from pydantic import BaseModel, field_validator
from enum import Enum


class QRErrorCorrection(str, Enum):
    L = "L"
    M = "M"
    Q = "Q"
    H = "H"


class QRFormat(str, Enum):
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    EPS = "eps"
    TXT = "txt"


class QRRequest(BaseModel):
    """Unified QR code request.

    - Set `data` to generate a standard QR code.
    - Set `ssid` to generate a WiFi QR code.
    """
    # Standard QR fields
    data: Optional[str] = None

    # WiFi QR fields
    ssid: Optional[str] = None
    password: Optional[str] = None
    security: Optional[str] = "WPA"
    hidden: Optional[bool] = False

    # Shared configuration
    scale: Optional[int] = 10
    border: Optional[int] = 4
    dark: Optional[str] = "black"
    light: Optional[str] = "white"
    error_correction: Optional[QRErrorCorrection] = QRErrorCorrection.M
    format: Optional[QRFormat] = QRFormat.PNG
    micro: Optional[bool] = None
    boost_error: Optional[bool] = True

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Data cannot be empty")
            if len(v) > 4296:
                raise ValueError("Data too long. Maximum 4296 characters for QR codes")
        return v

    @field_validator('ssid')
    @classmethod
    def validate_ssid(cls, v):
        if v is not None and not v.strip():
            raise ValueError("SSID cannot be empty")
        return v

    @field_validator('scale')
    @classmethod
    def validate_scale(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError("Scale must be between 1 and 100")
        return v

    @field_validator('border')
    @classmethod
    def validate_border(cls, v):
        if v is not None and v < 0:
            raise ValueError("Border cannot be negative")
        return v
