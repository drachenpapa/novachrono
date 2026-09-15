import pytest
from PIL import Image, ImageDraw

from novachrono.design import PANEL_COLOR
from novachrono.weather import WeatherCondition
from novachrono.widgets.weather.icons import (
    draw_raindrop,
    draw_weather_icon_frame,
)

ICON_SIZE = 32


@pytest.mark.parametrize(
    "condition",
    list(WeatherCondition),
)
@pytest.mark.parametrize(
    "is_day",
    [
        True,
        False,
    ],
)
def test_draw_weather_icon_frame_renders_each_condition(
    condition: WeatherCondition,
    is_day: bool,
) -> None:
    image = _create_image()
    draw = ImageDraw.Draw(image)

    before = image.tobytes()

    draw_weather_icon_frame(
        draw,
        condition=condition,
        is_day=is_day,
        origin=(0, 0),
        size=ICON_SIZE,
        frame_index=0,
    )

    assert image.tobytes() != before


@pytest.mark.parametrize(
    "condition",
    [
        WeatherCondition.CLEAR,
        WeatherCondition.PARTLY_CLOUDY,
    ],
)
def test_day_and_night_icons_differ(
    condition: WeatherCondition,
) -> None:
    day_image = _create_image()
    night_image = _create_image()

    draw_weather_icon_frame(
        ImageDraw.Draw(day_image),
        condition=condition,
        is_day=True,
        origin=(0, 0),
        size=ICON_SIZE,
        frame_index=0,
    )

    draw_weather_icon_frame(
        ImageDraw.Draw(night_image),
        condition=condition,
        is_day=False,
        origin=(0, 0),
        size=ICON_SIZE,
        frame_index=0,
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
        size=(
            ICON_SIZE,
            ICON_SIZE,
        ),
        color=PANEL_COLOR,
    )
