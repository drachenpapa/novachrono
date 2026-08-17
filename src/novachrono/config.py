import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import dotenv_values

from novachrono.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES
from novachrono.units import TemperatureUnit

DEFAULT_ENV_FILENAME: Final = ".env"
DEFAULT_TIMEZONE_NAME: Final = "Europe/Berlin"

TIMEZONE_VARIABLE: Final = "NOVACHRONO_TIMEZONE"
LOCALE_VARIABLE: Final = "NOVACHRONO_LOCALE"
TEMPERATURE_UNIT_VARIABLE: Final = "NOVACHRONO_TEMPERATURE_UNIT"

WEATHER_LATITUDE_VARIABLE: Final = "NOVACHRONO_WEATHER_LATITUDE"
WEATHER_LONGITUDE_VARIABLE: Final = "NOVACHRONO_WEATHER_LONGITUDE"

TIMES_GATE_HOST_VARIABLE: Final = "NOVACHRONO_TIMES_GATE_HOST"
TIMES_GATE_TOKEN_VARIABLE: Final = "NOVACHRONO_TIMES_GATE_TOKEN"


class ConfigError(ValueError):
    """Raised when Novachrono configuration is invalid."""


@dataclass(frozen=True)
class WeatherSettings:
    """Configured weather location."""

    latitude: float | None
    longitude: float | None


@dataclass(frozen=True)
class TimesGateSettings:
    """Configured Times Gate connection values."""

    host: str | None
    local_token: str | None


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for Novachrono."""

    timezone: ZoneInfo
    locale: str
    temperature_unit: TemperatureUnit
    weather: WeatherSettings
    times_gate: TimesGateSettings


def load_config(env_file: Path | None = None) -> AppConfig:
    """Load Novachrono configuration from .env and the environment."""

    dotenv_path = env_file if env_file is not None else Path.cwd() / DEFAULT_ENV_FILENAME

    file_values: dict[str, str | None] = {}

    if dotenv_path.is_file():
        file_values = dict(dotenv_values(dotenv_path))

    values: dict[str, str | None] = {**file_values, **os.environ}

    timezone_name = _read_optional_value(values, TIMEZONE_VARIABLE) or DEFAULT_TIMEZONE_NAME

    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise ConfigError(f"Unknown timezone: {timezone_name}") from error

    locale = _read_optional_value(values, LOCALE_VARIABLE) or DEFAULT_LOCALE

    if locale not in SUPPORTED_LOCALES:
        supported = ", ".join(SUPPORTED_LOCALES)
        raise ConfigError(f"Unsupported locale: {locale}. Supported locales: {supported}")

    temperature_unit = _parse_temperature_unit(
        _read_optional_value(values, TEMPERATURE_UNIT_VARIABLE)
    )

    weather = _read_weather_settings(values)

    times_gate = TimesGateSettings(
        host=_read_optional_value(values, TIMES_GATE_HOST_VARIABLE),
        local_token=_read_optional_value(values, TIMES_GATE_TOKEN_VARIABLE),
    )

    return AppConfig(
        timezone=timezone,
        locale=locale,
        temperature_unit=temperature_unit,
        weather=weather,
        times_gate=times_gate,
    )


def _read_weather_settings(values: Mapping[str, str | None]) -> WeatherSettings:
    latitude = _parse_optional_float(values, WEATHER_LATITUDE_VARIABLE)
    longitude = _parse_optional_float(values, WEATHER_LONGITUDE_VARIABLE)

    if (latitude is None) != (longitude is None):
        raise ConfigError("Weather latitude and longitude must be configured together")

    if latitude is not None and not -90 <= latitude <= 90:
        raise ConfigError("Weather latitude must be between -90 and 90")

    if longitude is not None and not -180 <= longitude <= 180:
        raise ConfigError("Weather longitude must be between -180 and 180")

    return WeatherSettings(
        latitude=latitude,
        longitude=longitude,
    )


def _parse_temperature_unit(value: str | None) -> TemperatureUnit:
    if value is None:
        return TemperatureUnit.CELSIUS

    normalized_value = value.strip().upper()

    aliases = {
        "C": TemperatureUnit.CELSIUS,
        "CELSIUS": TemperatureUnit.CELSIUS,
        "F": TemperatureUnit.FAHRENHEIT,
        "FAHRENHEIT": TemperatureUnit.FAHRENHEIT,
    }

    try:
        return aliases[normalized_value]
    except KeyError as error:
        raise ConfigError(
            f"Unsupported temperature unit: {value}. Supported values: C, F"
        ) from error


def _parse_optional_float(
    values: Mapping[str, str | None],
    name: str,
) -> float | None:
    value = _read_optional_value(values, name)

    if value is None:
        return None

    try:
        return float(value)
    except ValueError as error:
        raise ConfigError(f"Invalid numeric value for {name}: {value}") from error


def _read_optional_value(
    values: Mapping[str, str | None],
    name: str,
) -> str | None:
    value = values.get(name)

    if value is None:
        return None

    normalized_value = value.strip()

    if not normalized_value:
        return None

    return normalized_value
