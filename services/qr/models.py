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
    """QR code generation request with full segno configuration."""
    data: str
    scale: Optional[int] = 10
    border: Optional[int] = 4
    dark: Optional[str] = "black"
    light: Optional[str] = "white"
    error_correction: Optional[QRErrorCorrection] = QRErrorCorrection.M
    format: Optional[QRFormat] = QRFormat.PNG
    micro: Optional[bool] = True
    boost_error: Optional[bool] = True

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        if not v or not v.strip():
            raise ValueError("Data is required")
        if len(v) > 4296:
            raise ValueError("Data too long. Maximum 4296 characters for QR codes")
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


class WiFiRequest(BaseModel):
    """WiFi QR code generation request."""
    ssid: str
    password: Optional[str] = None
    security: Optional[str] = "WPA"
    hidden: Optional[bool] = False
    scale: Optional[int] = 10
    border: Optional[int] = 4
    dark: Optional[str] = "black"
    light: Optional[str] = "white"
    format: Optional[QRFormat] = QRFormat.PNG

    @field_validator('ssid')
    @classmethod
    def validate_ssid(cls, v):
        if not v or not v.strip():
            raise ValueError("SSID is required")
        return v
