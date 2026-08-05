from collections.abc import Callable

from PIL import Image, ImageDraw, ImageFont

from novachrono.design.theme import (
    BORDER_COLOR,
    CONTENT_LEFT,
    CONTENT_RIGHT,
    CORNER_RADIUS,
    HEADER_DIVIDER_Y,
    HEADER_ICON_LEFT,
    HEADER_ICON_TOP,
    HEADER_TITLE_X,
    HEADER_TITLE_Y,
    OUTER_MARGIN,
    PANEL_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
)

WidgetIconRenderer = Callable[
    [ImageDraw.ImageDraw, tuple[int, int], str],
    None,
]


def create_panel() -> Image.Image:
    """Create an empty Novachrono panel with its standard frame."""

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

    return image


def draw_widget_header(
    draw: ImageDraw.ImageDraw,
    *,
    title: str,
    accent_color: str,
    icon: WidgetIconRenderer,
) -> None:
    """Draw a standard widget header with an icon and divider."""

    icon(
        draw,
        (HEADER_ICON_LEFT, HEADER_ICON_TOP),
        accent_color,
    )

    title_font = ImageFont.load_default(size=12)

    draw.text(
        (HEADER_TITLE_X, HEADER_TITLE_Y),
        title,
        font=title_font,
        fill=TEXT_COLOR,
    )

    draw.line(
        (
            CONTENT_LEFT,
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
    x = (PANEL_SIZE - text_width) // 2

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
    """Draw the temporary accent bar used by placeholder panels."""

    draw.rounded_rectangle(
        (
            OUTER_MARGIN + 8,
            OUTER_MARGIN + 8,
            PANEL_SIZE - OUTER_MARGIN - 9,
            OUTER_MARGIN + 13,
        ),
        radius=2,
        fill=accent_color,
    )
