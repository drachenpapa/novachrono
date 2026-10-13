from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from novachrono.models.pokemon_go import (
    EventSchedule,
    PokemonGoEvent,
    PokemonGoEventType,
    PokemonGoFeaturedPokemon,
    RaidBoss,
    RaidRoster,
)
from novachrono.models.weather import CurrentWeather, WeatherCondition

BERLIN = ZoneInfo("Europe/Berlin")


@pytest.fixture
def weather() -> CurrentWeather:
    """Standard partly-cloudy test weather used across the suite."""

    return CurrentWeather(
        condition=WeatherCondition.PARTLY_CLOUDY,
        temperature=23,
        high_temperature=26,
        low_temperature=15,
        precipitation_probability=35,
        is_day=True,
    )


@pytest.fixture
def raid_roster() -> RaidRoster:
    """Standard single-boss raid roster used across the suite."""

    return RaidRoster(
        five_star=(
            RaidBoss(
                name="Zacian",
                can_be_shiny=True,
                artwork_url="https://example.com/zacian.png",
            ),
        ),
        mega=(
            RaidBoss(
                name="Mega Gengar",
                can_be_shiny=True,
                artwork_url="https://example.com/mega-gengar.png",
            ),
        ),
    )


@pytest.fixture
def event_schedule() -> EventSchedule:
    """Standard single-frame Pokémon GO event schedule."""

    return EventSchedule(
        spotlight_hour=PokemonGoEvent(
            event_type=PokemonGoEventType.SPOTLIGHT_HOUR,
            name="Rattata Spotlight Hour",
            start=datetime(
                2026,
                10,
                6,
                18,
                tzinfo=BERLIN,
            ),
            end=datetime(
                2026,
                10,
                6,
                19,
                tzinfo=BERLIN,
            ),
            featured_pokemon=(
                PokemonGoFeaturedPokemon(
                    name="Rattata",
                    can_be_shiny=True,
                    artwork_url="https://example.com/rattata.png",
                ),
            ),
            bonus="2\u00d7 Evolution XP",
        )
    )
