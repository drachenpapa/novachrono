from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from novachrono.design import PANEL_SIZE
from novachrono.widgets.clock import render_clock_panel

BERLIN = ZoneInfo("Europe/Berlin")

FIXED_TIME = datetime(
    2026,
    8,
    4,
    13,
    23,
    tzinfo=BERLIN,
)


def test_render_clock_panel_has_expected_size_and_mode() -> None:
    panel = render_clock_panel(FIXED_TIME)

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )
    assert panel.mode == "RGB"


def test_render_clock_panel_is_deterministic() -> None:
    first_panel = render_clock_panel(FIXED_TIME)
    second_panel = render_clock_panel(FIXED_TIME)

    assert first_panel.tobytes() == second_panel.tobytes()


def test_render_clock_panel_changes_when_minute_changes() -> None:
    first_panel = render_clock_panel(FIXED_TIME)
    second_panel = render_clock_panel(FIXED_TIME.replace(minute=24))

    assert first_panel.tobytes() != second_panel.tobytes()


def test_render_clock_panel_rejects_naive_datetime() -> None:
    naive_time = FIXED_TIME.replace(tzinfo=None)

    with pytest.raises(
        ValueError,
        match="timezone-aware datetime",
    ):
        render_clock_panel(naive_time)
