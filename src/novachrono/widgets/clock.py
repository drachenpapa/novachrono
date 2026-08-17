from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import BaseImageFont

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_BRIGHT_COLOR,
    FRAME_DEEP_COLOR,
    FRAME_DIM_COLOR,
    MUTED_TEXT_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    create_panel,
    draw_widget_header,
)

CLOCK_TITLE = "NOVACHRONO"

TIME_TOP = 43
TIME_CENTER_Y = 62
DATE_TOP = 96
DATE_OFFSET_X = 1


def render_clock_panel(now: datetime) -> Image.Image:
    """Render the Novachrono HUD clock."""

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Clock widget requires a timezone-aware datetime")

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(
        draw,
        title=CLOCK_TITLE,
        font_size=11,
    )

    _draw_background_layers(draw)
    _draw_time_supports(draw)
    _draw_direction_markers(draw)
    _draw_date_console(draw)

    time_font = ImageFont.load_default(size=30)
    date_font = ImageFont.load_default(size=10)

    _draw_centered_text(
        draw,
        y=TIME_TOP,
        text=now.strftime("%H:%M"),
        font=time_font,
        fill=TEXT_COLOR,
    )

    _draw_centered_text(
        draw,
        y=DATE_TOP,
        text=now.strftime("%d.%m.%Y"),
        font=date_font,
        fill=MUTED_TEXT_COLOR,
        offset_x=DATE_OFFSET_X,
    )

    return image


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    text: str,
    font: BaseImageFont,
    fill: str,
    offset_x: int = 0,
) -> None:
    bounding_box = draw.textbbox((0, 0), text, font=font)
    text_width = bounding_box[2] - bounding_box[0]

    x = (PANEL_SIZE - text_width) // 2 - bounding_box[0] + offset_x

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


def _draw_background_layers(draw: ImageDraw.ImageDraw) -> None:
    """Draw subtle technical layers behind the clock."""

    draw.line((29, 39, 48, 39), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((80, 39, 99, 39), fill=FRAME_DEEP_COLOR, width=1)

    draw.line((34, 42, 52, 42), fill=FRAME_DIM_COLOR, width=1)
    draw.line((76, 42, 94, 42), fill=FRAME_DIM_COLOR, width=1)

    draw.line((29, 84, 47, 84), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((81, 84, 99, 84), fill=FRAME_DEEP_COLOR, width=1)

    draw.line((35, 81, 50, 81), fill=FRAME_DIM_COLOR, width=1)
    draw.line((78, 81, 93, 81), fill=FRAME_DIM_COLOR, width=1)

    draw.line((39, 46, 44, 46), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((84, 46, 89, 46), fill=FRAME_DEEP_COLOR, width=1)

    draw.line((39, 77, 44, 77), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((84, 77, 89, 77), fill=FRAME_DEEP_COLOR, width=1)


def _draw_time_supports(draw: ImageDraw.ImageDraw) -> None:
    """Draw open angular supports around the time."""

    _draw_top_left_support(draw)
    _draw_top_right_support(draw)
    _draw_bottom_left_support(draw)
    _draw_bottom_right_support(draw)

    draw.line((41, 43, 54, 43), fill=FRAME_ACCENT_COLOR, width=1)
    draw.line((74, 43, 87, 43), fill=FRAME_ACCENT_COLOR, width=1)
    draw.line((41, 81, 56, 81), fill=FRAME_ACCENT_COLOR, width=1)
    draw.line((72, 81, 87, 81), fill=FRAME_ACCENT_COLOR, width=1)

    draw.line((49, 40, 58, 40), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((70, 40, 79, 40), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((50, 84, 60, 84), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((68, 84, 78, 84), fill=FRAME_DEEP_COLOR, width=1)


def _draw_top_left_support(draw: ImageDraw.ImageDraw) -> None:
    draw.line((22, 51, 22, 45), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((22, 45, 29, 38), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((29, 38, 42, 38), fill=FRAME_BRIGHT_COLOR, width=2)

    draw.line((25, 51, 25, 47), fill=FRAME_DIM_COLOR, width=1)
    draw.line((25, 47, 31, 41), fill=FRAME_DIM_COLOR, width=1)


def _draw_top_right_support(draw: ImageDraw.ImageDraw) -> None:
    draw.line((106, 51, 106, 45), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((99, 38, 106, 45), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((86, 38, 99, 38), fill=FRAME_BRIGHT_COLOR, width=2)

    draw.line((103, 51, 103, 47), fill=FRAME_DIM_COLOR, width=1)
    draw.line((97, 41, 103, 47), fill=FRAME_DIM_COLOR, width=1)


def _draw_bottom_left_support(draw: ImageDraw.ImageDraw) -> None:
    draw.line((22, 73, 22, 79), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((22, 79, 29, 86), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((29, 86, 42, 86), fill=FRAME_BRIGHT_COLOR, width=2)

    draw.line((25, 73, 25, 77), fill=FRAME_DIM_COLOR, width=1)
    draw.line((25, 77, 31, 83), fill=FRAME_DIM_COLOR, width=1)


def _draw_bottom_right_support(draw: ImageDraw.ImageDraw) -> None:
    draw.line((106, 73, 106, 79), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((99, 86, 106, 79), fill=FRAME_ACCENT_COLOR, width=2)
    draw.line((86, 86, 99, 86), fill=FRAME_BRIGHT_COLOR, width=2)

    draw.line((103, 73, 103, 77), fill=FRAME_DIM_COLOR, width=1)
    draw.line((97, 83, 103, 77), fill=FRAME_DIM_COLOR, width=1)


def _draw_direction_markers(draw: ImageDraw.ImageDraw) -> None:
    """Draw compact D-pad-style direction markers."""

    _draw_top_marker(draw)
    _draw_left_marker(draw)
    _draw_right_marker(draw)


def _draw_top_marker(draw: ImageDraw.ImageDraw) -> None:
    draw.line(
        (
            59,
            36,
            64,
            31,
            69,
            36,
            59,
            36,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.point((64, 33), fill=FRAME_BRIGHT_COLOR)

    draw.line((48, 33, 56, 33), fill=FRAME_DEEP_COLOR, width=1)
    draw.line((72, 33, 80, 33), fill=FRAME_DEEP_COLOR, width=1)


def _draw_left_marker(draw: ImageDraw.ImageDraw) -> None:
    center_y = TIME_CENTER_Y

    draw.line(
        (
            19,
            center_y,
            24,
            center_y - 5,
            24,
            center_y + 5,
            19,
            center_y,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.point((22, center_y), fill=FRAME_BRIGHT_COLOR)


def _draw_right_marker(draw: ImageDraw.ImageDraw) -> None:
    center_y = TIME_CENTER_Y

    draw.line(
        (
            109,
            center_y,
            104,
            center_y - 5,
            104,
            center_y + 5,
            109,
            center_y,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.point((106, center_y), fill=FRAME_BRIGHT_COLOR)


def _draw_date_console(draw: ImageDraw.ImageDraw) -> None:
    """Draw a straight open HUD console around the date."""

    left = 35
    right = 93
    top = 91
    bottom = 110

    corner_gap = 5

    draw.line(
        (left + corner_gap, top, right - corner_gap, top),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (left + 11, top, right - 11, top),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.line(
        (left + corner_gap, bottom, right - corner_gap, bottom),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (left + 14, bottom, right - 14, bottom),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.line(
        (left, top + corner_gap, left, bottom - corner_gap),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (right, top + corner_gap, right, bottom - corner_gap),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (left, top + corner_gap, left + corner_gap, top),
        fill=FRAME_DEEP_COLOR,
        width=1,
    )

    draw.line(
        (right - corner_gap, top, right, top + corner_gap),
        fill=FRAME_DEEP_COLOR,
        width=1,
    )

    draw.line(
        (left, bottom - corner_gap, left + corner_gap, bottom),
        fill=FRAME_DEEP_COLOR,
        width=1,
    )

    draw.line(
        (right - corner_gap, bottom, right, bottom - corner_gap),
        fill=FRAME_DEEP_COLOR,
        width=1,
    )

    draw.line(
        (left - 6, 98, left - 2, 98),
        fill=FRAME_BRIGHT_COLOR,
        width=1,
    )

    draw.line(
        (right + 2, 98, right + 6, 98),
        fill=FRAME_BRIGHT_COLOR,
        width=1,
    )
