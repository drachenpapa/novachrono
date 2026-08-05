from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from novachrono.design import (
    ACCENT_COLORS,
    PANEL_COUNT,
    create_panel,
    draw_placeholder_header,
)
from novachrono.widgets.clock import render_clock_panel

DEFAULT_TIMEZONE = ZoneInfo("Europe/Berlin")
CLOCK_PANEL_INDEX = 2


def render_panel(index: int) -> Image.Image:
    """Render one static placeholder panel."""

    if not 0 <= index < PANEL_COUNT:
        raise ValueError(f"Panel index must be between 0 and {PANEL_COUNT - 1}")

    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_placeholder_header(
        draw,
        accent_color=ACCENT_COLORS[index],
    )

    return image


def render_dashboard(
    now: datetime | None = None,
) -> Sequence[Image.Image]:
    """Render all Times Gate panels."""

    current_time = now or datetime.now(DEFAULT_TIMEZONE)

    panels = [render_panel(index) for index in range(PANEL_COUNT)]

    panels[CLOCK_PANEL_INDEX] = render_clock_panel(current_time)

    return tuple(panels)
