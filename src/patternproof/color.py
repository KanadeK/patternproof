"""Owned, transparent sRGB and CIELAB color math."""

from __future__ import annotations

import math
import re

from patternproof.model import Rgb

Lab = tuple[float, float, float]
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def parse_hex_color(value: object) -> Rgb:
    """Parse a strict six-digit hexadecimal sRGB color."""

    if not isinstance(value, str) or _HEX_COLOR.fullmatch(value) is None:
        raise ValueError("color must be a six-digit hexadecimal sRGB value such as '#1a2b3c'")
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


def _linear_channel(channel: int) -> float:
    normalized = channel / 255.0
    if normalized <= 0.04045:
        return normalized / 12.92
    return math.pow((normalized + 0.055) / 1.055, 2.4)


def _lab_axis(value: float) -> float:
    delta = 6 / 29
    if value > delta**3:
        return math.pow(value, 1 / 3)
    return value / (3 * delta**2) + 4 / 29


def rgb_to_lab(rgb: Rgb) -> Lab:
    """Convert an eight-bit sRGB triple to CIELAB using the D65 reference white."""

    red, green, blue = (_linear_channel(channel) for channel in rgb)

    x = red * 0.4124564 + green * 0.3575761 + blue * 0.1804375
    y = red * 0.2126729 + green * 0.7151522 + blue * 0.0721750
    z = red * 0.0193339 + green * 0.1191920 + blue * 0.9503041

    fx = _lab_axis(x / 0.95047)
    fy = _lab_axis(y)
    fz = _lab_axis(z / 1.08883)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e76(first: Lab, second: Lab) -> float:
    """Return the Euclidean CIE 1976 color difference."""

    return math.sqrt(sum((left - right) ** 2 for left, right in zip(first, second, strict=True)))
