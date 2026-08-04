import pytest
from PIL import Image

from novachrono.dashboard import render_dashboard
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.preview import create_preview


def test_create_preview_combines_all_panels() -> None:
    preview = create_preview(render_dashboard())

    assert preview.mode == "RGB"
    assert preview.width > PANEL_COUNT * PANEL_SIZE
    assert preview.height > PANEL_SIZE


def test_create_preview_rejects_wrong_panel_count() -> None:
    panels = render_dashboard()[:-1]

    with pytest.raises(ValueError):
        create_preview(panels)


def test_create_preview_rejects_wrong_panel_size() -> None:
    panels = list(render_dashboard())
    panels[2] = Image.new("RGB", (64, 64))

    with pytest.raises(ValueError):
        create_preview(panels)
