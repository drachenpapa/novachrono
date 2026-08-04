from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from novachrono.design import PANEL_SIZE
from novachrono.widgets.clock import render_clock_panel

BERLIN = ZoneInfo("Europe/Berlin")


def test_render_clock_panel_has_expected_size_and_mode() -> None:
    now = datetime(2026, 8, 4, 13, 23, tzinfo=BERLIN)

    panel = render_clock_panel(now)

    assert panel.size == (PANEL_SIZE, PANEL_SIZE)
    assert panel.mode == "RGB"


def test_render_clock_panel_is_deterministic() -> None:
    now = datetime(2026, 8, 4, 13, 23, tzinfo=BERLIN)

    first_panel = render_clock_panel(now)
    second_panel = render_clock_panel(now)

    assert first_panel.tobytes() == second_panel.tobytes()


def test_render_clock_panel_changes_when_minute_changes() -> None:
    first_time = datetime(2026, 8, 4, 13, 23, tzinfo=BERLIN)
    second_time = datetime(2026, 8, 4, 13, 24, tzinfo=BERLIN)

    first_panel = render_clock_panel(first_time)
    second_panel = render_clock_panel(second_time)

    assert first_panel.tobytes() != second_panel.tobytes()


def test_render_clock_panel_rejects_naive_datetime() -> None:
    now = datetime(2026, 8, 4, 13, 23)

    with pytest.raises(
        ValueError,
        match="timezone-aware datetime",
    ):
        render_clock_panel(now)
