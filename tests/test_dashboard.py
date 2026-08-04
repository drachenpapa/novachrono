from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    render_dashboard,
    render_panel,
)
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


def test_dashboard_renders_clock_on_center_panel() -> None:
    now = datetime(
        2026,
        8,
        4,
        13,
        23,
        tzinfo=ZoneInfo("Europe/Berlin"),
    )

    panels = render_dashboard(now)

    clock_panel = panels[CLOCK_PANEL_INDEX]
    left_panel = panels[CLOCK_PANEL_INDEX - 1]
    right_panel = panels[CLOCK_PANEL_INDEX + 1]

    assert clock_panel.tobytes() != left_panel.tobytes()
    assert clock_panel.tobytes() != right_panel.tobytes()


def test_dashboard_is_deterministic_for_given_time() -> None:
    now = datetime(
        2026,
        8,
        4,
        13,
        23,
        tzinfo=ZoneInfo("Europe/Berlin"),
    )

    first_dashboard = render_dashboard(now)
    second_dashboard = render_dashboard(now)

    assert len(first_dashboard) == len(second_dashboard)

    for first_panel, second_panel in zip(
        first_dashboard,
        second_dashboard,
        strict=True,
    ):
        assert first_panel.tobytes() == second_panel.tobytes()
