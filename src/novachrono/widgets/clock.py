from datetime import datetime

from babel.dates import format_datetime
from PIL import Image, ImageDraw, ImageFont

from novachrono.design import (
    BORDER_COLOR,
    CORNER_RADIUS,
    MUTED_TEXT_COLOR,
    OUTER_MARGIN,
    PANEL_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
)

CLOCK_ACCENT_COLOR = "#D36BFF"


def render_clock_panel(
    now: datetime,
    *,
    locale: str = "de_DE",
) -> Image.Image:
    """Render a clock panel for a timezone-aware datetime."""

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Clock widget requires a timezone-aware datetime")

    image = Image.new(
        mode="RGB",
        size=(PANEL_SIZE, PANEL_SIZE),
        color=PANEL_COLOR,
    )
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (
            OUTER_MARGIN,
            OUTER_MARGIN,
            PANEL_SIZE - OUTER_MARGIN - 1,
            PANEL_SIZE - OUTER_MARGIN - 1,
        ),
        radius=CORNER_RADIUS,
        outline=BORDER_COLOR,
        width=2,
    )

    _draw_header(draw)

    time_font = ImageFont.load_default(size=29)
    weekday_font = ImageFont.load_default(size=12)
    date_font = ImageFont.load_default(size=11)

    weekday_text = format_datetime(
        now,
        "EEEE",
        locale=locale,
    ).upper()

    date_text = format_datetime(
        now,
        "dd. MMM yyyy",
        locale=locale,
    ).upper()

    _draw_centered_text(
        draw,
        y=48,
        text=now.strftime("%H:%M"),
        font=time_font,
        fill=TEXT_COLOR,
    )

    _draw_centered_text(
        draw,
        y=82,
        text=weekday_text,
        font=weekday_font,
        fill=CLOCK_ACCENT_COLOR,
    )

    _draw_centered_text(
        draw,
        y=103,
        text=date_text,
        font=date_font,
        fill=MUTED_TEXT_COLOR,
    )

    return image


def _draw_header(draw: ImageDraw.ImageDraw) -> None:
    icon_center = (22, 24)
    icon_radius = 9

    draw.ellipse(
        (
            icon_center[0] - icon_radius,
            icon_center[1] - icon_radius,
            icon_center[0] + icon_radius,
            icon_center[1] + icon_radius,
        ),
        outline=CLOCK_ACCENT_COLOR,
        width=2,
    )

    draw.line(
        (
            icon_center[0],
            icon_center[1],
            icon_center[0],
            icon_center[1] - 5,
        ),
        fill=TEXT_COLOR,
        width=1,
    )

    draw.line(
        (
            icon_center[0],
            icon_center[1],
            icon_center[0] + 4,
            icon_center[1] + 2,
        ),
        fill=TEXT_COLOR,
        width=1,
    )

    title_font = ImageFont.load_default(size=12)

    draw.text(
        (38, 17),
        "UHR",
        font=title_font,
        fill=TEXT_COLOR,
    )

    draw.line(
        (16, 38, PANEL_SIZE - 16, 38),
        fill=CLOCK_ACCENT_COLOR,
        width=1,
    )


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
) -> None:
    bounding_box = draw.textbbox((0, 0), text, font=font)
    text_width = bounding_box[2] - bounding_box[0]
    x = (PANEL_SIZE - text_width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )
