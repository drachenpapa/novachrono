from typing import Final

from PIL import ImageDraw

SHINY_COLOR: Final = "#FFD447"


def draw_sparkle(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    color: str,
    radius: int,
) -> None:
    """Draw a small four-direction sparkle."""

    center_x, center_y = origin

    draw.polygon(
        (
            (center_x, center_y - radius),
            (center_x + 1, center_y - 1),
            (center_x + radius, center_y),
            (center_x + 1, center_y + 1),
            (center_x, center_y + radius),
            (center_x - 1, center_y + 1),
            (center_x - radius, center_y),
            (center_x - 1, center_y - 1),
        ),
        fill=color,
    )
