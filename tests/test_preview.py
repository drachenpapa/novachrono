from pathlib import Path

import pytest
from PIL import Image

from novachrono.dashboard import render_dashboard
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.preview import create_preview, save_preview


def test_create_preview_combines_all_panels() -> None:
    preview = create_preview(render_dashboard())

    assert preview.mode == "RGB"
    assert preview.width > PANEL_COUNT * PANEL_SIZE
    assert preview.height > PANEL_SIZE


def test_create_preview_rejects_wrong_panel_count() -> None:
    panels = render_dashboard()[:-1]

    with pytest.raises(
        ValueError,
        match=f"Expected {PANEL_COUNT} panels",
    ):
        create_preview(panels)


def test_create_preview_rejects_wrong_panel_size() -> None:
    panels = list(render_dashboard())
    panels[2] = Image.new("RGB", (64, 64))

    with pytest.raises(
        ValueError,
        match="Panel 2 has size",
    ):
        create_preview(panels)


def test_save_preview_creates_parent_directory_and_png(
    tmp_path: Path,
) -> None:
    preview = create_preview(render_dashboard())
    destination = tmp_path / "nested" / "dashboard-preview.png"

    save_preview(preview, destination)

    assert destination.is_file()

    with Image.open(destination) as saved_image:
        assert saved_image.format == "PNG"
        assert saved_image.size == preview.size
