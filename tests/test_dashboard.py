import pytest
from PIL import Image

from novachrono.dashboard import render_dashboard, render_panel
from novachrono.design import PANEL_COUNT, PANEL_SIZE


def test_render_dashboard_creates_expected_number_of_panels() -> None:
    panels = render_dashboard()

    assert len(panels) == PANEL_COUNT


def test_render_dashboard_returns_images() -> None:
    panels = render_dashboard()

    assert all(isinstance(panel, Image.Image) for panel in panels)


def test_each_panel_has_expected_size_and_mode() -> None:
    panels = render_dashboard()

    for panel in panels:
        assert panel.size == (PANEL_SIZE, PANEL_SIZE)
        assert panel.mode == "RGB"


@pytest.mark.parametrize("index", [-1, PANEL_COUNT])
def test_render_panel_rejects_invalid_index(index: int) -> None:
    with pytest.raises(
        ValueError,
        match="Panel index must be between",
    ):
        render_panel(index)
