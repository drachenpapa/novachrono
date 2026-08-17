import pytest

from novachrono.units import TemperatureUnit, convert_temperature


@pytest.mark.parametrize("temperature", [-40, -20, 0, 23, 40])
def test_celsius_conversion_keeps_original_temperature(
    temperature: int,
) -> None:
    assert (
        convert_temperature(
            temperature,
            TemperatureUnit.CELSIUS,
        )
        == temperature
    )


@pytest.mark.parametrize(
    ("temperature_celsius", "expected_fahrenheit"),
    [
        (-40, -40),
        (-20, -4),
        (0, 32),
        (23, 73),
        (40, 104),
    ],
)
def test_fahrenheit_conversion(
    temperature_celsius: int,
    expected_fahrenheit: int,
) -> None:
    assert (
        convert_temperature(
            temperature_celsius,
            TemperatureUnit.FAHRENHEIT,
        )
        == expected_fahrenheit
    )
