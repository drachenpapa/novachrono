from PIL import ImageColor

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_BRIGHT_COLOR,
    PANEL_SIZE,
    create_panel,
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
