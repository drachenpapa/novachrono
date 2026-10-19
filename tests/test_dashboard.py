from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from PIL import Image

from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    EVENT_PANEL_INDEX,
    MATRIX_PANEL_INDEX,
    RAID_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
    render_dashboard,
)
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.models.pokemon_go import EventSchedule, RaidRoster
from novachrono.models.weather import CurrentWeather
from novachrono.units import TemperatureUnit
from novachrono.widgets.matrix import render_matrix_panel

BERLIN = ZoneInfo("Europe/Berlin")

FIXED_TIME = datetime(
    2026,
    8,
    6,
    12,
    54,
    tzinfo=BERLIN,
)


def test_current_widgets_have_expected_positions() -> None:
    assert MATRIX_PANEL_INDEX == 0
    assert WEATHER_PANEL_INDEX == 1
    assert CLOCK_PANEL_INDEX == 2
    assert RAID_PANEL_INDEX == 3
    assert EVENT_PANEL_INDEX == 4


def test_render_dashboard_returns_expected_panels(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    panels = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
    )

    assert isinstance(panels, tuple)
    assert len(panels) == PANEL_COUNT

    for panel in panels:
        assert isinstance(
            panel,
            Image.Image,
        )

        assert panel.size == (
            PANEL_SIZE,
            PANEL_SIZE,
        )

        assert panel.mode == "RGB"


def test_dashboard_renders_widgets_on_configured_panels(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    panels = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
    )

    matrix_panel = render_matrix_panel()

    assert panels[MATRIX_PANEL_INDEX].tobytes() == matrix_panel.tobytes()

    for panel_index in (
        WEATHER_PANEL_INDEX,
        CLOCK_PANEL_INDEX,
        RAID_PANEL_INDEX,
        EVENT_PANEL_INDEX,
    ):
        assert panels[panel_index].tobytes() != matrix_panel.tobytes()


def test_dashboard_passes_artwork_to_raid_renderer(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    raid_artwork = {
        "https://example.com/artwork.png": Image.new(
            mode="RGBA",
            size=(1, 1),
        ),
    }

    with patch("novachrono.dashboard.render_raid_panel") as mocked_renderer:
        mocked_renderer.return_value = Image.new(
            mode="RGB",
            size=(PANEL_SIZE, PANEL_SIZE),
        )

        render_dashboard(
            FIXED_TIME,
            weather=weather,
            event_schedule=event_schedule,
            raid_roster=raid_roster,
            raid_artwork=raid_artwork,
        )

    mocked_renderer.assert_called_once_with(
        raid_roster,
        artwork_by_url=raid_artwork,
    )


def test_dashboard_passes_artwork_to_event_renderer(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    event_artwork = {
        "https://example.com/artwork.png": Image.new(
            mode="RGBA",
            size=(1, 1),
        ),
    }

    with patch("novachrono.dashboard.render_event_panel") as mocked_renderer:
        mocked_renderer.return_value = Image.new(
            mode="RGB",
            size=(PANEL_SIZE, PANEL_SIZE),
        )

        render_dashboard(
            FIXED_TIME,
            weather=weather,
            event_schedule=event_schedule,
            raid_roster=raid_roster,
            event_artwork=event_artwork,
        )

    mocked_renderer.assert_called_once_with(
        event_schedule,
        locale="de_DE",
        artwork_by_url=event_artwork,
    )


def test_dashboard_is_deterministic_for_given_input(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    first_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
    )

    second_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
    )

    for first_panel, second_panel in zip(
        first_dashboard,
        second_dashboard,
        strict=True,
    ):
        assert first_panel.tobytes() == second_panel.tobytes()


def test_temperature_unit_changes_only_weather_panel(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    celsius_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        temperature_unit=TemperatureUnit.CELSIUS,
    )

    fahrenheit_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )

    assert (
        celsius_dashboard[WEATHER_PANEL_INDEX].tobytes()
        != fahrenheit_dashboard[WEATHER_PANEL_INDEX].tobytes()
    )

    for panel_index in (
        MATRIX_PANEL_INDEX,
        CLOCK_PANEL_INDEX,
        RAID_PANEL_INDEX,
        EVENT_PANEL_INDEX,
    ):
        assert (
            celsius_dashboard[panel_index].tobytes() == fahrenheit_dashboard[panel_index].tobytes()
        )


def test_locale_changes_localized_panels(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
    event_schedule: EventSchedule,
) -> None:
    german_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        locale="de_DE",
    )

    english_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        event_schedule=event_schedule,
        raid_roster=raid_roster,
        locale="en_US",
    )

    assert (
        german_dashboard[WEATHER_PANEL_INDEX].tobytes()
        != english_dashboard[WEATHER_PANEL_INDEX].tobytes()
    )

    assert (
        german_dashboard[EVENT_PANEL_INDEX].tobytes()
        != english_dashboard[EVENT_PANEL_INDEX].tobytes()
    )

    assert (
        german_dashboard[CLOCK_PANEL_INDEX].tobytes()
        != english_dashboard[CLOCK_PANEL_INDEX].tobytes()
    )

    assert (
        german_dashboard[RAID_PANEL_INDEX].tobytes()
        == english_dashboard[RAID_PANEL_INDEX].tobytes()
    )

    assert (
        german_dashboard[MATRIX_PANEL_INDEX].tobytes()
        == english_dashboard[MATRIX_PANEL_INDEX].tobytes()
    )
