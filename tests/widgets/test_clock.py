from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from novachrono.design import PANEL_SIZE
from novachrono.widgets.clock import render_clock_panel

BERLIN = ZoneInfo("Europe/Berlin")


def test_render_clock_panel_returns_panel_image() -> None:
    panel = render_clock_panel(
        datetime(
            2026,
            9,
            15,
            20,
            16,
            tzinfo=BERLIN,
        )
    )

    assert panel.size == (PANEL_SIZE, PANEL_SIZE)


def test_render_clock_panel_is_deterministic() -> None:
    now = datetime(
        2026,
        9,
        15,
        20,
        16,
        tzinfo=BERLIN,
    )

    first = render_clock_panel(now)
    second = render_clock_panel(now)

    assert first.tobytes() == second.tobytes()


def test_render_clock_panel_changes_with_time() -> None:
    first = render_clock_panel(
        datetime(
            2026,
            9,
            15,
            20,
            16,
            tzinfo=BERLIN,
        )
    )
    second = render_clock_panel(
        datetime(
            2026,
            9,
            15,
            20,
            17,
            tzinfo=BERLIN,
        )
    )

    assert first.tobytes() != second.tobytes()


def test_render_clock_panel_changes_with_date() -> None:
    first = render_clock_panel(
        datetime(
            2026,
            9,
            15,
            20,
            16,
            tzinfo=BERLIN,
        )
    )
    second = render_clock_panel(
        datetime(
            2026,
            9,
            16,
            20,
            16,
            tzinfo=BERLIN,
        )
    )

    assert first.tobytes() != second.tobytes()


def test_render_clock_panel_requires_timezone_aware_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware datetime",
    ):
        render_clock_panel(
            datetime(
                2026,
                9,
                15,
                20,
                16,
            )
        )
