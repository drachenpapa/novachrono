from dataclasses import replace
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from novachrono.config import (
    AppConfig,
    TimesGateSettings,
    WeatherSettings,
)
from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoFeaturedPokemon,
    RaidBoss,
    RaidRoster,
)
from novachrono.units import TemperatureUnit


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(
        timezone=ZoneInfo("Europe/Berlin"),
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
        weather=WeatherSettings(
            latitude=53.04771,
            longitude=8.80169,
        ),
        times_gate=TimesGateSettings(
            host="192.168.178.50",
            local_token="secret",
        ),
    )


@pytest.fixture(autouse=True)
def state_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    paths = {
        "events": tmp_path / "events.state",
        "weather": tmp_path / "weather.state",
        "raids": tmp_path / "raids.state",
    }

    for module in (
        "novachrono.cli.widgets",
        "novachrono.cli.dashboard",
    ):
        monkeypatch.setattr(
            f"{module}.EVENT_STATE_PATH",
            paths["events"],
        )
        monkeypatch.setattr(
            f"{module}.WEATHER_STATE_PATH",
            paths["weather"],
        )
        monkeypatch.setattr(
            f"{module}.RAID_STATE_PATH",
            paths["raids"],
        )

    return paths


@pytest.fixture
def multi_raid_roster(
    raid_roster: RaidRoster,
) -> RaidRoster:
    """Two five-star bosses to trigger animation rendering."""

    second_five_star = RaidBoss(
        name="Zamazenta",
        can_be_shiny=True,
    )

    return RaidRoster(
        five_star=(
            *raid_roster.five_star,
            second_five_star,
        ),
        shadow_five_star=raid_roster.shadow_five_star,
        mega=raid_roster.mega,
    )


@pytest.fixture
def multi_event_schedule(
    event_schedule: EventSchedule,
) -> EventSchedule:
    """Two featured Pokémon to trigger event animation rendering."""

    assert event_schedule.spotlight_hour is not None

    return replace(
        event_schedule,
        spotlight_hour=replace(
            event_schedule.spotlight_hour,
            featured_pokemon=(
                *event_schedule.spotlight_hour.featured_pokemon,
                PokemonGoFeaturedPokemon(
                    name="Alolan Rattata",
                    can_be_shiny=True,
                ),
            ),
        ),
    )
