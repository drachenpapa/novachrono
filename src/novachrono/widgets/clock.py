from datetime import datetime

from babel.dates import format_date
from PIL import Image, ImageDraw, ImageFont

from novachrono.design import (
    HEADER_ICON_SIZE,
    MUTED_TEXT_COLOR,
    TEXT_COLOR,
    create_panel,
    draw_centered_text,
    draw_widget_header,
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

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(
        draw,
        title="UHR",
        accent_color=CLOCK_ACCENT_COLOR,
        icon=_draw_clock_icon,
    )

    time_font = ImageFont.load_default(size=29)
    weekday_font = ImageFont.load_default(size=12)
    date_font = ImageFont.load_default(size=11)

    local_date = now.date()

    weekday_text = format_date(
        local_date,
        "EEEE",
        locale=locale,
    ).upper()

    date_text = format_date(
        local_date,
        "dd. MMM yyyy",
        locale=locale,
    ).upper()

    draw_centered_text(
        draw,
        y=48,
        text=now.strftime("%H:%M"),
        font=time_font,
        fill=TEXT_COLOR,
    )

    draw_centered_text(
        draw,
        y=82,
        text=weekday_text,
        font=weekday_font,
        fill=CLOCK_ACCENT_COLOR,
    )

    draw_centered_text(
        draw,
        y=103,
        text=date_text,
        font=date_font,
        fill=MUTED_TEXT_COLOR,
    )

    return image


def _draw_clock_icon(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    accent_color: str,
) -> None:
    left, top = origin
    radius = HEADER_ICON_SIZE // 2

    center_x = left + radius
    center_y = top + radius

    draw.ellipse(
        (
            left,
            top,
            left + HEADER_ICON_SIZE,
            top + HEADER_ICON_SIZE,
        ),
        outline=accent_color,
        width=2,
    )

    draw.line(
        (
            center_x,
            center_y,
            center_x,
            center_y - 5,
        ),
        fill=TEXT_COLOR,
        width=1,
    )

    draw.line(
        (
            center_x,
            center_y,
            center_x + 4,
            center_y + 2,
        ),
        fill=TEXT_COLOR,
        width=1,
    )
