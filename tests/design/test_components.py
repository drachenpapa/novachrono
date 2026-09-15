from unittest.mock import MagicMock

from PIL import ImageColor

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_BRIGHT_COLOR,
    PANEL_SIZE,
    create_panel,
    draw_centered_text,
)


def test_create_panel_has_expected_size_and_mode() -> None:
    panel = create_panel()

    assert panel.size == (PANEL_SIZE, PANEL_SIZE)
    assert panel.mode == "RGB"


def test_left_mid_frame_segment_remains_visible() -> None:
    panel = create_panel()
    expected_color = ImageColor.getrgb(FRAME_ACCENT_COLOR)

    assert panel.getpixel((12, 60)) == expected_color


def test_top_center_bright_rail_is_visible() -> None:
    panel = create_panel()
    expected_color = ImageColor.getrgb(FRAME_BRIGHT_COLOR)

    assert panel.getpixel((64, 10)) == expected_color


def test_draw_centered_text_uses_text_bounding_box() -> None:
    draw = MagicMock()
    font = MagicMock()

    draw.textbbox.return_value = (1, 0, 11, 8)

    draw_centered_text(
        draw,
        y=42,
        text="TEST",
        font=font,
        fill="#FFFFFF",
    )

    draw.text.assert_called_once_with(
        (58, 42),
        "TEST",
        font=font,
        fill="#FFFFFF",
    )
