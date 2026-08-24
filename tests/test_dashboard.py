from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from PIL import Image

from novachrono.dashboard import (
    CLOCK_PANEL_INDEX,
    POKEMON_GO_PANEL_INDEX,
    WEATHER_PANEL_INDEX,
    render_dashboard,
    render_panel,
)
from novachrono.design import PANEL_COUNT, PANEL_SIZE
from novachrono.pokemon_go import RaidRoster
from novachrono.units import TemperatureUnit
from novachrono.weather import CurrentWeather

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
    assert WEATHER_PANEL_INDEX == 1
    assert CLOCK_PANEL_INDEX == 2
    assert POKEMON_GO_PANEL_INDEX == 3


def test_render_dashboard_creates_expected_number_of_panels(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
    )

    assert len(panels) == PANEL_COUNT


def test_render_dashboard_returns_images(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
    )

    assert all(isinstance(panel, Image.Image) for panel in panels)


def test_each_panel_has_expected_size_and_mode(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
    )

    for panel in panels:
        assert panel.size == (PANEL_SIZE, PANEL_SIZE)
        assert panel.mode == "RGB"


@pytest.mark.parametrize(
    "index",
    [-1, PANEL_COUNT],
)
def test_render_panel_rejects_invalid_index(
    index: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Panel index must be between",
    ):
        render_panel(index)


def test_dashboard_renders_weather_on_configured_panel(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
    )

    assert panels[WEATHER_PANEL_INDEX].tobytes() != panels[0].tobytes()


def test_dashboard_renders_clock_on_center_panel(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    panels = render_dashboard(
        FIXED_TIME,
        weather=weather,
        raid_roster=raid_roster,
    )

    assert panels[CLOCK_PANEL_INDEX].tobytes() != panels[0].tobytes()


def test_dashboard_renders_pokemon_go_on_configured_panel(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    panels = render_dashboard(
        weather=weather,
        raid_roster=raid_roster,
    )

    assert panels[POKEMON_GO_PANEL_INDEX].tobytes() != panels[0].tobytes()


def test_dashboard_passes_artwork_to_pokemon_renderer(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
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
            raid_roster=raid_roster,
            raid_artwork=raid_artwork,
        )

    mocked_renderer.assert_called_once_with(
        raid_roster,
        artwork_by_url=raid_artwork,
    )


def test_dashboard_is_deterministic_for_given_input(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    first_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        raid_roster=raid_roster,
    )

    second_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
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
) -> None:
    celsius_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        raid_roster=raid_roster,
        temperature_unit=TemperatureUnit.CELSIUS,
    )

    fahrenheit_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        raid_roster=raid_roster,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )

    assert (
        celsius_dashboard[WEATHER_PANEL_INDEX].tobytes()
        != fahrenheit_dashboard[WEATHER_PANEL_INDEX].tobytes()
    )

    assert (
        celsius_dashboard[CLOCK_PANEL_INDEX].tobytes()
        == fahrenheit_dashboard[CLOCK_PANEL_INDEX].tobytes()
    )

    assert (
        celsius_dashboard[POKEMON_GO_PANEL_INDEX].tobytes()
        == fahrenheit_dashboard[POKEMON_GO_PANEL_INDEX].tobytes()
    )


def test_locale_changes_only_weather_panel(
    weather: CurrentWeather,
    raid_roster: RaidRoster,
) -> None:
    german_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        raid_roster=raid_roster,
        locale="de_DE",
    )

    english_dashboard = render_dashboard(
        FIXED_TIME,
        weather=weather,
        raid_roster=raid_roster,
        locale="en_US",
    )

    assert (
        german_dashboard[WEATHER_PANEL_INDEX].tobytes()
        != english_dashboard[WEATHER_PANEL_INDEX].tobytes()
    )

    assert (
        german_dashboard[CLOCK_PANEL_INDEX].tobytes()
        == english_dashboard[CLOCK_PANEL_INDEX].tobytes()
    )

    assert (
        german_dashboard[POKEMON_GO_PANEL_INDEX].tobytes()
        == english_dashboard[POKEMON_GO_PANEL_INDEX].tobytes()
    )
