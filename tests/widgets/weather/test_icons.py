import pytest
from PIL import Image, ImageDraw

from novachrono.design import PANEL_COLOR
from novachrono.weather import WeatherCondition
from novachrono.widgets.weather.icons import (
    draw_raindrop,
    draw_weather_icon,
)

ICON_SIZE = 32


@pytest.mark.parametrize(
    "condition",
    list(WeatherCondition),
)
@pytest.mark.parametrize(
    "is_day",
    [True, False],
)
def test_draw_weather_icon_renders_each_condition(
    condition: WeatherCondition,
    is_day: bool,
) -> None:
    image = _create_image()
    draw = ImageDraw.Draw(image)

    before = image.tobytes()

    draw_weather_icon(
        draw,
        condition=condition,
        is_day=is_day,
        origin=(0, 0),
        size=ICON_SIZE,
    )

    assert image.tobytes() != before


def test_clear_day_and_night_icons_differ() -> None:
    day_image = _create_image()
    night_image = _create_image()

    draw_weather_icon(
        ImageDraw.Draw(day_image),
        condition=WeatherCondition.CLEAR,
        is_day=True,
        origin=(0, 0),
        size=ICON_SIZE,
    )

    draw_weather_icon(
        ImageDraw.Draw(night_image),
        condition=WeatherCondition.CLEAR,
        is_day=False,
        origin=(0, 0),
        size=ICON_SIZE,
    )

    assert day_image.tobytes() != night_image.tobytes()


def test_partly_cloudy_day_and_night_icons_differ() -> None:
    day_image = _create_image()
    night_image = _create_image()

    draw_weather_icon(
        ImageDraw.Draw(day_image),
        condition=WeatherCondition.PARTLY_CLOUDY,
        is_day=True,
        origin=(0, 0),
        size=ICON_SIZE,
    )

    draw_weather_icon(
        ImageDraw.Draw(night_image),
        condition=WeatherCondition.PARTLY_CLOUDY,
        is_day=False,
        origin=(0, 0),
        size=ICON_SIZE,
    )

    assert day_image.tobytes() != night_image.tobytes()


def test_draw_raindrop_changes_image() -> None:
    image = _create_image()
    draw = ImageDraw.Draw(image)

    before = image.tobytes()

    draw_raindrop(
        draw,
        origin=(4, 4),
        size=7,
    )

    assert image.tobytes() != before


def _create_image() -> Image.Image:
    return Image.new(
        mode="RGB",
        size=(ICON_SIZE, ICON_SIZE),
        color=PANEL_COLOR,
    )
