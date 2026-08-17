from enum import StrEnum


class TemperatureUnit(StrEnum):
    """Temperature units supported by Novachrono."""

    CELSIUS = "C"
    FAHRENHEIT = "F"


def convert_temperature(
    temperature_celsius: int,
    unit: TemperatureUnit,
) -> int:
    """Convert a Celsius temperature to the requested unit."""

    if unit is TemperatureUnit.CELSIUS:
        return temperature_celsius

    return round(temperature_celsius * 9 / 5 + 32)
