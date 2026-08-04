from collections.abc import Sequence

from PIL import Image, ImageDraw

from novachrono.design import (
    ACCENT_COLORS,
    BORDER_COLOR,
    CORNER_RADIUS,
    OUTER_MARGIN,
    PANEL_COLOR,
    PANEL_COUNT,
    PANEL_SIZE,
)


def render_panel(index: int) -> Image.Image:
    """Render one static placeholder panel."""

    if not 0 <= index < PANEL_COUNT:
        raise ValueError(f"Panel index must be between 0 and {PANEL_COUNT - 1}")

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

    accent_color = ACCENT_COLORS[index]

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

    return image


def render_dashboard() -> Sequence[Image.Image]:
    """Render all Times Gate panels."""

    return tuple(render_panel(index) for index in range(PANEL_COUNT))
