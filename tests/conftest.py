import pytest

from novachrono.pokemon_go import RaidBoss, RaidRoster
from novachrono.weather import CurrentWeather, WeatherCondition


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
