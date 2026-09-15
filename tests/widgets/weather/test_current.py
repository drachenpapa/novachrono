from dataclasses import replace

import pytest
from PIL import Image

from novachrono.design import PANEL_SIZE
from novachrono.units import TemperatureUnit
from novachrono.weather import (
    CurrentWeather,
    WeatherCondition,
)
from novachrono.widgets.weather import (
    render_weather_animation,
    render_weather_panel,
)


def test_render_weather_panel_has_expected_size_and_mode(
    weather: CurrentWeather,
) -> None:
    panel = render_weather_panel(weather)

    assert isinstance(
        panel,
        Image.Image,
    )

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )

    assert panel.mode == "RGB"


def test_render_weather_panel_is_deterministic(
    weather: CurrentWeather,
) -> None:
    first_panel = render_weather_panel(weather)

    second_panel = render_weather_panel(weather)

    assert first_panel.tobytes() == second_panel.tobytes()


def test_render_weather_panel_changes_with_temperature(
    weather: CurrentWeather,
) -> None:
    warmer_weather = replace(
        weather,
        temperature=30,
        high_temperature=32,
        low_temperature=20,
    )

    original_panel = render_weather_panel(weather)

    warmer_panel = render_weather_panel(warmer_weather)

    assert original_panel.tobytes() != warmer_panel.tobytes()


@pytest.mark.parametrize(
    "condition",
    list(WeatherCondition),
)
def test_render_weather_panel_supports_each_condition(
    weather: CurrentWeather,
    condition: WeatherCondition,
) -> None:
    panel = render_weather_panel(
        replace(
            weather,
            condition=condition,
        )
    )

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )


@pytest.mark.parametrize(
    "condition",
    [
        WeatherCondition.CLEAR,
        WeatherCondition.PARTLY_CLOUDY,
    ],
)
def test_day_and_night_render_differently(
    weather: CurrentWeather,
    condition: WeatherCondition,
) -> None:
    day_weather = replace(
        weather,
        condition=condition,
        is_day=True,
    )

    night_weather = replace(
        day_weather,
        is_day=False,
    )

    day_panel = render_weather_panel(day_weather)

    night_panel = render_weather_panel(night_weather)

    assert day_panel.tobytes() != night_panel.tobytes()


def test_celsius_and_fahrenheit_render_differently(
    weather: CurrentWeather,
) -> None:
    celsius_panel = render_weather_panel(
        weather,
        temperature_unit=TemperatureUnit.CELSIUS,
    )

    fahrenheit_panel = render_weather_panel(
        weather,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )

    assert celsius_panel.tobytes() != fahrenheit_panel.tobytes()


@pytest.mark.parametrize(
    (
        "temperature",
        "high_temperature",
        "low_temperature",
        "temperature_unit",
    ),
    [
        (
            -20,
            -15,
            -25,
            TemperatureUnit.CELSIUS,
        ),
        (
            40,
            45,
            35,
            TemperatureUnit.FAHRENHEIT,
        ),
    ],
)
def test_render_weather_panel_supports_extreme_temperature_layouts(
    weather: CurrentWeather,
    temperature: int,
    high_temperature: int,
    low_temperature: int,
    temperature_unit: TemperatureUnit,
) -> None:
    extreme_weather = replace(
        weather,
        temperature=temperature,
        high_temperature=high_temperature,
        low_temperature=low_temperature,
    )

    panel = render_weather_panel(
        extreme_weather,
        temperature_unit=temperature_unit,
    )

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )


def test_render_weather_panel_supports_100_percent_precipitation(
    weather: CurrentWeather,
) -> None:
    rainy_weather = replace(
        weather,
        precipitation_probability=100,
    )

    panel = render_weather_panel(rainy_weather)

    assert panel.size == (
        PANEL_SIZE,
        PANEL_SIZE,
    )


def test_locale_changes_weather_panel(
    weather: CurrentWeather,
) -> None:
    german_panel = render_weather_panel(
        weather,
        locale="de_DE",
    )

    english_panel = render_weather_panel(
        weather,
        locale="en_US",
    )

    assert german_panel.tobytes() != english_panel.tobytes()


@pytest.mark.parametrize(
    (
        "condition",
        "expected_frame_count",
    ),
    [
        (
            WeatherCondition.CLEAR,
            1,
        ),
        (
            WeatherCondition.PARTLY_CLOUDY,
            1,
        ),
        (
            WeatherCondition.CLOUDY,
            1,
        ),
        (
            WeatherCondition.RAIN,
            3,
        ),
        (
            WeatherCondition.FOG,
            10,
        ),
        (
            WeatherCondition.SNOW,
            1,
        ),
        (
            WeatherCondition.THUNDERSTORM,
            1,
        ),
    ],
)
def test_render_weather_animation_uses_expected_frame_count(
    weather: CurrentWeather,
    condition: WeatherCondition,
    expected_frame_count: int,
) -> None:
    frames = render_weather_animation(
        replace(
            weather,
            condition=condition,
        )
    )

    assert len(frames) == expected_frame_count


@pytest.mark.parametrize(
    "condition",
    list(WeatherCondition),
)
def test_weather_panel_matches_first_animation_frame(
    weather: CurrentWeather,
    condition: WeatherCondition,
) -> None:
    selected_weather = replace(
        weather,
        condition=condition,
    )

    panel = render_weather_panel(selected_weather)

    frames = render_weather_animation(selected_weather)

    assert frames[0].tobytes() == panel.tobytes()


@pytest.mark.parametrize(
    "condition",
    [
        WeatherCondition.RAIN,
        WeatherCondition.FOG,
    ],
)
def test_render_weather_animation_frames_have_expected_size_and_mode(
    weather: CurrentWeather,
    condition: WeatherCondition,
) -> None:
    frames = render_weather_animation(
        replace(
            weather,
            condition=condition,
        )
    )

    for frame in frames:
        assert frame.size == (
            PANEL_SIZE,
            PANEL_SIZE,
        )
        assert frame.mode == "RGB"


def test_rain_animation_contains_three_different_frames(
    weather: CurrentWeather,
) -> None:
    frames = render_weather_animation(
        replace(
            weather,
            condition=WeatherCondition.RAIN,
        )
    )

    rendered_frames = {frame.tobytes() for frame in frames}

    assert len(rendered_frames) == 3


def test_fog_animation_contains_multiple_rolling_states(
    weather: CurrentWeather,
) -> None:
    frames = render_weather_animation(
        replace(
            weather,
            condition=WeatherCondition.FOG,
        )
    )

    rendered_frames = {frame.tobytes() for frame in frames}

    assert len(frames) == 10
    assert len(rendered_frames) >= 6
