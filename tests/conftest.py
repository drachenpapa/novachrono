import pytest

from novachrono.pokemon_go import (
    CombatPowerRange,
    PokemonType,
    RaidBoss,
    RaidRoster,
    RaidTier,
)
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
                tier=RaidTier.FIVE_STAR,
                can_be_shiny=True,
                types=(
                    PokemonType.FAIRY,
                    PokemonType.STEEL,
                ),
                normal_combat_power=CombatPowerRange(
                    minimum=2100,
                    maximum=2188,
                ),
                boosted_combat_power=CombatPowerRange(
                    minimum=2625,
                    maximum=2735,
                ),
            ),
        ),
        mega=(
            RaidBoss(
                name="Mega Gengar",
                tier=RaidTier.MEGA,
                can_be_shiny=True,
                types=(
                    PokemonType.GHOST,
                    PokemonType.POISON,
                ),
                normal_combat_power=CombatPowerRange(
                    minimum=1566,
                    maximum=1644,
                ),
                boosted_combat_power=CombatPowerRange(
                    minimum=1958,
                    maximum=2055,
                ),
            ),
        ),
    )
