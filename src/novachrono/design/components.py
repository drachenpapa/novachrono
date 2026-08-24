from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import BaseImageFont

from novachrono.design.theme import (
    CONTENT_LEFT,
    CONTENT_RIGHT,
    FRAME_ACCENT_COLOR,
    FRAME_BRIGHT_COLOR,
    FRAME_DEEP_COLOR,
    FRAME_LINE_COLOR,
    HEADER_DIVIDER_Y,
    HEADER_TOP,
    PANEL_COLOR,
    PANEL_SIZE,
    SUBTLE_TEXT_COLOR,
    TEXT_COLOR,
)


def create_panel() -> Image.Image:
    """Create an empty Novachrono panel with its shared HUD frame."""

    image = Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
        color=PANEL_COLOR,
    )

    draw = ImageDraw.Draw(image)
    _draw_hud_frame(draw)

    return image


def draw_widget_header(
    draw: ImageDraw.ImageDraw,
    *,
    title: str,
    accent_color: str = FRAME_ACCENT_COLOR,
    font_size: int = 10,
) -> None:
    """Draw a centered widget title with short surrounding lines."""

    title_font = ImageFont.load_default(size=font_size)
    bounding_box = draw.textbbox((0, 0), title, font=title_font)

    title_width = bounding_box[2] - bounding_box[0]
    title_x = (PANEL_SIZE - title_width) // 2 - bounding_box[0]

    draw.text(
        (title_x, HEADER_TOP),
        title,
        font=title_font,
        fill=TEXT_COLOR,
    )

    line_gap = 5
    left_line_end = title_x - line_gap
    right_line_start = title_x + title_width + line_gap

    draw.line(
        (
            CONTENT_LEFT,
            HEADER_DIVIDER_Y,
            max(CONTENT_LEFT, left_line_end),
            HEADER_DIVIDER_Y,
        ),
        fill=accent_color,
        width=1,
    )

    draw.line(
        (
            min(CONTENT_RIGHT, right_line_start),
            HEADER_DIVIDER_Y,
            CONTENT_RIGHT,
            HEADER_DIVIDER_Y,
        ),
        fill=accent_color,
        width=1,
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
        (61, 64, 67, 64),
        fill=SUBTLE_TEXT_COLOR,
        width=1,
    )

    draw.line(
        (64, 61, 64, 67),
        fill=SUBTLE_TEXT_COLOR,
        width=1,
    )


def find_font_that_fits(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    maximum_width: int,
    font_sizes: tuple[int, ...],
) -> BaseImageFont:
    """Return the largest requested font that fits the available width."""

    for font_size in font_sizes:
        font = ImageFont.load_default(size=font_size)

        if (
            text_width(
                draw,
                text=text,
                font=font,
            )
            <= maximum_width
        ):
            return font

    return ImageFont.load_default(size=font_sizes[-1])


def text_width(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    font: BaseImageFont,
) -> int:
    """Measure rendered text width."""

    bounding_box = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    return bounding_box[2] - bounding_box[0]


def _draw_hud_frame(draw: ImageDraw.ImageDraw) -> None:
    """Draw the shared layered cyan HUD frame."""

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

    depth_points = [
        (23, 15),
        (105, 15),
        (113, 23),
        (113, 105),
        (105, 113),
        (23, 113),
        (15, 105),
        (15, 23),
    ]

    draw.line(
        [*depth_points, depth_points[0]],
        fill=FRAME_DEEP_COLOR,
        width=1,
    )

    draw.line(
        (46, 10, 82, 10),
        fill=FRAME_BRIGHT_COLOR,
        width=2,
    )

    draw.line(
        (53, 118, 75, 118),
        fill=FRAME_ACCENT_COLOR,
        width=2,
    )

    for line in (
        (17, 17, 30, 17),
        (98, 17, 111, 17),
        (17, 111, 30, 111),
        (98, 111, 111, 111),
    ):
        draw.line(
            line,
            fill=FRAME_ACCENT_COLOR,
            width=1,
        )
