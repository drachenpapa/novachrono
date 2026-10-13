from datetime import datetime
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from novachrono.design import (
    CONTENT_LEFT,
    CONTENT_RIGHT,
    FRAME_DIM_COLOR,
    MUTED_TEXT_COLOR,
    TEXT_COLOR,
    create_panel,
    draw_centered_text,
    draw_widget_header,
)
from novachrono.i18n import DEFAULT_LOCALE

CLOCK_TITLE: Final = "NOVACHRONO"

TIME_TOP: Final = 40
TIME_FONT_SIZE: Final = 38

SEPARATOR_Y: Final = 82

DATE_TOP: Final = 89
DATE_FONT_SIZE: Final = 11

_DATE_FORMATS: Final = {
    "de_DE": "%d.%m.%Y",
    "en_US": "%m/%d/%Y",
}


def render_clock_panel(
    now: datetime,
    *,
    locale: str = DEFAULT_LOCALE,
) -> Image.Image:
    """Render the static Novachrono clock."""

    _validate_datetime(now)

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(draw, title=CLOCK_TITLE, font_size=11)

    time_font = ImageFont.load_default(size=TIME_FONT_SIZE)
    date_font = ImageFont.load_default(size=DATE_FONT_SIZE)

    draw_centered_text(
        draw,
        y=TIME_TOP,
        text=now.strftime("%H:%M"),
        font=time_font,
        fill=TEXT_COLOR,
    )

    draw.line(
        (
            CONTENT_LEFT,
            SEPARATOR_Y,
            CONTENT_RIGHT,
            SEPARATOR_Y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    date_format = _DATE_FORMATS.get(locale, _DATE_FORMATS[DEFAULT_LOCALE])

    draw_centered_text(
        draw,
        y=DATE_TOP,
        text=now.strftime(date_format),
        font=date_font,
        fill=MUTED_TEXT_COLOR,
    )

    return image


def _validate_datetime(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Clock widget requires a timezone-aware datetime")
