from PIL import Image, ImageDraw, ImageFont

from novachrono.design.theme import (
    CONTENT_LEFT,
    CONTENT_RIGHT,
    FRAME_ACCENT_COLOR,
    FRAME_LINE_COLOR,
    HEADER_DIVIDER_Y,
    HEADER_TOP,
    PANEL_COLOR,
    PANEL_SIZE,
    SUBTLE_TEXT_COLOR,
    TEXT_COLOR,
)


def create_panel() -> Image.Image:
    """Create an empty Novachrono panel with the current HUD frame style."""

    image = Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
        color=PANEL_COLOR,
    )

    draw = ImageDraw.Draw(image)
    _draw_hud_frame(draw)

    return image


def _draw_hud_frame(draw: ImageDraw.ImageDraw) -> None:
    """Draw the shared cyan HUD frame."""

    outer_points = [
        (16, 8),
        (112, 8),
        (120, 16),
        (120, 112),
        (112, 120),
        (16, 120),
        (8, 112),
        (8, 16),
    ]

    draw.line(
        [*outer_points, outer_points[0]],
        fill=FRAME_LINE_COLOR,
        width=1,
    )

    inner_points = [
        (20, 12),
        (108, 12),
        (116, 20),
        (116, 108),
        (108, 116),
        (20, 116),
        (12, 108),
        (12, 20),
    ]

    draw.line(
        [*inner_points, inner_points[0]],
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.line(
        (46, 10, 82, 10),
        fill=FRAME_ACCENT_COLOR,
        width=2,
    )

    draw.line(
        (53, 118, 75, 118),
        fill=FRAME_ACCENT_COLOR,
        width=2,
    )

    draw.line(
        (17, 17, 30, 17),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.line(
        (98, 17, 111, 17),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.line(
        (17, 111, 30, 111),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.line(
        (98, 111, 111, 111),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )


def draw_widget_header(
    draw: ImageDraw.ImageDraw,
    *,
    title: str,
    accent_color: str,
    title_x: int | None = None,
) -> None:
    """Draw a small widget title with subtle divider lines."""

    title_font = ImageFont.load_default(size=12)

    if title_x is None:
        bounding_box = draw.textbbox(
            (0, 0),
            title,
            font=title_font,
        )
        title_width = bounding_box[2] - bounding_box[0]
        x = (PANEL_SIZE - title_width) // 2
    else:
        x = title_x

    draw.text(
        (x, HEADER_TOP),
        title,
        font=title_font,
        fill=TEXT_COLOR,
    )

    draw.line(
        (
            CONTENT_LEFT,
            HEADER_DIVIDER_Y,
            42,
            HEADER_DIVIDER_Y,
        ),
        fill=accent_color,
        width=1,
    )

    draw.line(
        (
            86,
            HEADER_DIVIDER_Y,
            CONTENT_RIGHT,
            HEADER_DIVIDER_Y,
        ),
        fill=accent_color,
        width=1,
    )


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
) -> None:
    """Draw text horizontally centered on a panel."""

    bounding_box = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    text_width = bounding_box[2] - bounding_box[0]
    x = (PANEL_SIZE - text_width) // 2 - bounding_box[0]

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


def draw_placeholder_header(
    draw: ImageDraw.ImageDraw,
    *,
    accent_color: str,
) -> None:
    """Draw a minimal placeholder indicator."""

    draw.line(
        (18, 26, 39, 26),
        fill=accent_color,
        width=2,
    )

    draw.line(
        (55, 118, 73, 118),
        fill=accent_color,
        width=2,
    )

    draw.line(
        (61, 64, 67, 64),
        fill=SUBTLE_TEXT_COLOR,
        width=1,
    )

    draw.line(
        (64, 61, 64, 67),
        fill=SUBTLE_TEXT_COLOR,
        width=1,
    )
