import math
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_DIM_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    create_panel,
    draw_centered_text,
)

CLOCK_TITLE = "NOVACHRONO"

CLOCK_CENTER_X = PANEL_SIZE // 2
CLOCK_CENTER_Y = 65

CLOCK_OUTER_RADIUS = 32
CLOCK_MIDDLE_RADIUS = 28
CLOCK_INNER_RADIUS = 24


def render_clock_panel(
    now: datetime,
    *,
    locale: str = "de_DE",
) -> Image.Image:
    """Render the Novachrono clock panel."""

    del locale

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError(
            "Clock widget requires a timezone-aware datetime"
        )

    image = create_panel()
    draw = ImageDraw.Draw(image)

    _draw_title(draw)
    _draw_clock_ring(draw)

    time_font = ImageFont.load_default(size=32)
    date_font = ImageFont.load_default(size=11)

    draw_centered_text(
        draw,
        y=46,
        text=now.strftime("%H:%M"),
        font=time_font,
        fill=TEXT_COLOR,
    )

    draw_centered_text(
        draw,
        y=102,
        text=now.strftime("%d.%m.%Y"),
        font=date_font,
        fill=TEXT_COLOR,
    )

    return image


def _draw_title(
    draw: ImageDraw.ImageDraw,
) -> None:
    title_font = ImageFont.load_default(size=11)

    bounding_box = draw.textbbox(
        (0, 0),
        CLOCK_TITLE,
        font=title_font,
    )

    title_width = bounding_box[2] - bounding_box[0]
    title_x = (PANEL_SIZE - title_width) // 2 - bounding_box[0]

    draw.text(
        (title_x, 18),
        CLOCK_TITLE,
        font=title_font,
        fill=TEXT_COLOR,
    )

    divider_y = 30
    divider_gap = 4

    left_line_end = title_x - divider_gap
    right_line_start = title_x + title_width + divider_gap

    if left_line_end > 17:
        draw.line(
            (
                17,
                divider_y,
                left_line_end,
                divider_y,
            ),
            fill=FRAME_ACCENT_COLOR,
            width=1,
        )

    if right_line_start < PANEL_SIZE - 17:
        draw.line(
            (
                right_line_start,
                divider_y,
                PANEL_SIZE - 17,
                divider_y,
            ),
            fill=FRAME_ACCENT_COLOR,
            width=1,
        )


def _draw_clock_ring(
    draw: ImageDraw.ImageDraw,
) -> None:
    outer_box = _circle_box(CLOCK_OUTER_RADIUS)
    middle_box = _circle_box(CLOCK_MIDDLE_RADIUS)
    inner_box = _circle_box(CLOCK_INNER_RADIUS)

    draw.ellipse(
        outer_box,
        outline=FRAME_DIM_COLOR,
        width=1,
    )

    draw.ellipse(
        middle_box,
        outline=FRAME_DIM_COLOR,
        width=1,
    )

    draw.arc(
        outer_box,
        start=205,
        end=335,
        fill=FRAME_ACCENT_COLOR,
        width=2,
    )

    draw.arc(
        outer_box,
        start=25,
        end=155,
        fill=FRAME_ACCENT_COLOR,
        width=2,
    )

    draw.arc(
        inner_box,
        start=215,
        end=325,
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    draw.arc(
        inner_box,
        start=35,
        end=145,
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )

    for angle in range(0, 360, 20):
        _draw_tick(
            draw,
            angle_degrees=angle,
            major=angle % 60 == 0,
        )


def _circle_box(
    radius: int,
) -> tuple[int, int, int, int]:
    return (
        CLOCK_CENTER_X - radius,
        CLOCK_CENTER_Y - radius,
        CLOCK_CENTER_X + radius,
        CLOCK_CENTER_Y + radius,
    )


def _draw_tick(
    draw: ImageDraw.ImageDraw,
    *,
    angle_degrees: int,
    major: bool,
) -> None:
    angle_radians = math.radians(
        angle_degrees - 90
    )

    outer_radius = CLOCK_OUTER_RADIUS + 2
    tick_length = 5 if major else 3
    inner_radius = outer_radius - tick_length

    outer_x = round(
        CLOCK_CENTER_X
        + math.cos(angle_radians) * outer_radius
    )
    outer_y = round(
        CLOCK_CENTER_Y
        + math.sin(angle_radians) * outer_radius
    )

    inner_x = round(
        CLOCK_CENTER_X
        + math.cos(angle_radians) * inner_radius
    )
    inner_y = round(
        CLOCK_CENTER_Y
        + math.sin(angle_radians) * inner_radius
    )

    draw.line(
        (
            inner_x,
            inner_y,
            outer_x,
            outer_y,
        ),
        fill=(
            FRAME_ACCENT_COLOR
            if major
            else FRAME_DIM_COLOR
        ),
        width=1,
    )
