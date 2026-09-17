from dataclasses import replace
from pathlib import Path

from novachrono.display_state import (
    raid_roster_fingerprint,
    read_fingerprint,
    weather_fingerprint,
    write_fingerprint,
)
from novachrono.models.pokemon_go import RaidBoss, RaidRoster
from novachrono.models.weather import CurrentWeather, WeatherCondition
from novachrono.units import TemperatureUnit


def test_weather_fingerprint_is_deterministic() -> None:
    weather = _create_weather()

    first = weather_fingerprint(
        weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
    )

    second = weather_fingerprint(
        weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
    )

    assert first == second


def test_weather_fingerprint_changes_when_weather_changes() -> None:
    weather = _create_weather()

    changed_weather = replace(
        weather,
        temperature=24,
    )

    assert weather_fingerprint(
        weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
    ) != weather_fingerprint(
        changed_weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
    )


def test_weather_fingerprint_changes_when_locale_changes() -> None:
    weather = _create_weather()

    assert weather_fingerprint(
        weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
    ) != weather_fingerprint(
        weather,
        locale="en_US",
        temperature_unit=TemperatureUnit.CELSIUS,
    )


def test_weather_fingerprint_changes_when_temperature_unit_changes() -> None:
    weather = _create_weather()

    assert weather_fingerprint(
        weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.CELSIUS,
    ) != weather_fingerprint(
        weather,
        locale="de_DE",
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )


def test_raid_roster_fingerprint_is_deterministic() -> None:
    roster = _create_raid_roster()

    first = raid_roster_fingerprint(
        roster,
        locale="de_DE",
    )

    second = raid_roster_fingerprint(
        roster,
        locale="de_DE",
    )

    assert first == second


def test_raid_roster_fingerprint_includes_shadow_raids() -> None:
    roster = _create_raid_roster()

    changed_roster = RaidRoster(
        five_star=roster.five_star,
        shadow_five_star=(
            RaidBoss(
                name="Giratina",
                can_be_shiny=False,
                artwork_url="https://example.com/other-giratina.png",
            ),
        ),
        mega=roster.mega,
    )

    assert raid_roster_fingerprint(
        roster,
        locale="de_DE",
    ) != raid_roster_fingerprint(
        changed_roster,
        locale="de_DE",
    )


def test_raid_roster_fingerprint_changes_when_locale_changes() -> None:
    roster = _create_raid_roster()

    assert raid_roster_fingerprint(
        roster,
        locale="de_DE",
    ) != raid_roster_fingerprint(
        roster,
        locale="en_US",
    )


def test_read_fingerprint_returns_none_for_missing_file(
    tmp_path: Path,
) -> None:
    assert read_fingerprint(tmp_path / "missing.state") is None


def test_read_fingerprint_returns_none_for_malformed_state(
    tmp_path: Path,
) -> None:
    path = tmp_path / "weather.state"
    path.write_text(
        "not-a-fingerprint",
        encoding="ascii",
    )

    assert read_fingerprint(path) is None


def test_write_and_read_fingerprint_roundtrip(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "weather.state"
    fingerprint = "a" * 64

    write_fingerprint(
        path,
        fingerprint,
    )

    assert read_fingerprint(path) == fingerprint


def _create_weather() -> CurrentWeather:
    return CurrentWeather(
        condition=WeatherCondition.PARTLY_CLOUDY,
        temperature=23,
        high_temperature=26,
        low_temperature=15,
        precipitation_probability=35,
        is_day=True,
    )


def _create_raid_roster() -> RaidRoster:
    return RaidRoster(
        five_star=(
            RaidBoss(
                name="Zacian",
                can_be_shiny=True,
                artwork_url="https://example.com/zacian.png",
            ),
        ),
        shadow_five_star=(
            RaidBoss(
                name="Giratina",
                can_be_shiny=True,
                artwork_url="https://example.com/giratina.png",
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
