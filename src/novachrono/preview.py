from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from novachrono.design import BACKGROUND_COLOR, PANEL_COUNT, PANEL_SIZE

PREVIEW_GAP = 16
PREVIEW_MARGIN = 24


def create_preview(panels: Sequence[Image.Image]) -> Image.Image:
    """Combine all panel images into one dashboard preview."""

    if len(panels) != PANEL_COUNT:
        raise ValueError(f"Expected {PANEL_COUNT} panels, received {len(panels)}")

    width = PREVIEW_MARGIN * 2 + PANEL_COUNT * PANEL_SIZE + (PANEL_COUNT - 1) * PREVIEW_GAP
    height = PREVIEW_MARGIN * 2 + PANEL_SIZE

    preview = Image.new(
        mode="RGB",
        size=(width, height),
        color=BACKGROUND_COLOR,
    )

    for index, panel in enumerate(panels):
        expected_size = (PANEL_SIZE, PANEL_SIZE)

        if panel.size != expected_size:
            raise ValueError(f"Panel {index} has size {panel.size}; expected {expected_size}")

        x_position = PREVIEW_MARGIN + index * (PANEL_SIZE + PREVIEW_GAP)
        preview.paste(panel, (x_position, PREVIEW_MARGIN))

    return preview


def save_preview(preview: Image.Image, destination: Path) -> None:
    """Save a dashboard preview as a PNG file."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    preview.save(destination, format="PNG")
