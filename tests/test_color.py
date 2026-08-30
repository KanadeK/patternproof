from __future__ import annotations

import pytest

from patternproof.color import delta_e76, parse_hex_color, rgb_to_lab


def test_parse_hex_color_accepts_six_digit_srgb() -> None:
    assert parse_hex_color("#0a80FF") == (10, 128, 255)


@pytest.mark.parametrize("value", ["0a80ff", "#fff", "#GG0000", 123])
def test_parse_hex_color_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError, match="six-digit"):
        parse_hex_color(value)


def test_delta_e_is_zero_for_identical_color_and_symmetric() -> None:
    red = rgb_to_lab((220, 40, 50))
    blue = rgb_to_lab((30, 80, 210))

    assert delta_e76(red, red) == pytest.approx(0.0)
    assert delta_e76(red, blue) == pytest.approx(delta_e76(blue, red))
    assert delta_e76(red, blue) > 50


def test_rgb_to_lab_uses_reference_white_scale() -> None:
    lightness, a_axis, b_axis = rgb_to_lab((255, 255, 255))

    assert lightness == pytest.approx(100.0, abs=0.001)
    assert a_axis == pytest.approx(0.0, abs=0.02)
    assert b_axis == pytest.approx(0.0, abs=0.02)
