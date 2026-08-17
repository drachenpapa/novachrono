from typing import Final

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import BaseImageFont

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_DIM_COLOR,
    PANEL_SIZE,
    TEXT_COLOR,
    WEATHER_RAIN_COLOR,
    create_panel,
    draw_widget_header,
)
from novachrono.i18n import DEFAULT_LOCALE, translate
from novachrono.units import TemperatureUnit, convert_temperature
from novachrono.weather import CurrentWeather, WeatherCondition
from novachrono.widgets.weather.icons import (
    draw_raindrop,
    draw_weather_icon,
    draw_weather_icon_frame,
)

WEATHER_ICON_ORIGIN: Final = (16, 34)
WEATHER_ICON_SIZE: Final = 32

RAIN_ANIMATION_FRAMES: Final = (
    0,
    1,
    2,
)

FOG_ANIMATION_FRAMES: Final = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
)


def render_weather_panel(
    weather: CurrentWeather,
    *,
    locale: str = DEFAULT_LOCALE,
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
) -> Image.Image:
    """Render today's weather conditions."""

    return _render_weather_panel(
        weather,
        locale=locale,
        temperature_unit=temperature_unit,
        icon_frame_index=None,
    )


def render_weather_animation(
    weather: CurrentWeather,
    *,
    locale: str = DEFAULT_LOCALE,
    temperature_unit: TemperatureUnit = TemperatureUnit.CELSIUS,
) -> tuple[Image.Image, ...]:
    """Render native animation frames for the current weather."""

    icon_frames = _animation_icon_frames(weather.condition)

    if len(icon_frames) == 1:
        return (
            render_weather_panel(
                weather,
                locale=locale,
                temperature_unit=temperature_unit,
            ),
        )

    return tuple(
        _render_weather_panel(
            weather,
            locale=locale,
            temperature_unit=temperature_unit,
            icon_frame_index=icon_frame_index,
        )
        for icon_frame_index in icon_frames
    )


def _render_weather_panel(
    weather: CurrentWeather,
    *,
    locale: str,
    temperature_unit: TemperatureUnit,
    icon_frame_index: int | None,
) -> Image.Image:
    image = create_panel()
    draw = ImageDraw.Draw(image)

    draw_widget_header(
        draw,
        title=translate(
            "weather.title",
            locale=locale,
        ),
        font_size=10,
    )

    _draw_current_weather(
        draw,
        weather,
        temperature_unit=temperature_unit,
        icon_frame_index=icon_frame_index,
    )

    _draw_detail_separator(draw)

    _draw_detail_row(
        draw,
        weather,
        temperature_unit=temperature_unit,
    )

    _draw_bottom_accent(draw)

    return image


def _draw_current_weather(
    draw: ImageDraw.ImageDraw,
    weather: CurrentWeather,
    *,
    temperature_unit: TemperatureUnit,
    icon_frame_index: int | None,
) -> None:
    """Draw the main icon and current temperature."""

    if icon_frame_index is None:
        draw_weather_icon(
            draw,
            condition=weather.condition,
            is_day=weather.is_day,
            origin=WEATHER_ICON_ORIGIN,
            size=WEATHER_ICON_SIZE,
        )
    else:
        draw_weather_icon_frame(
            draw,
            condition=weather.condition,
            is_day=weather.is_day,
            origin=WEATHER_ICON_ORIGIN,
            size=WEATHER_ICON_SIZE,
            frame_index=icon_frame_index,
        )

    temperature = convert_temperature(
        weather.temperature,
        temperature_unit,
    )
    temperature_text = f"{temperature}°{temperature_unit.value}"

    temperature_font = _find_font_that_fits(
        draw,
        text=temperature_text,
        maximum_width=58,
        font_sizes=(
            31,
            29,
            27,
            25,
            23,
            21,
            19,
        ),
    )

    _draw_centered_in_region(
        draw,
        left=55,
        right=113,
        y=36,
        text=temperature_text,
        font=temperature_font,
        fill=TEXT_COLOR,
    )


def _draw_detail_separator(
    draw: ImageDraw.ImageDraw,
) -> None:
    """Draw the separator between current weather and details."""

    separator_y = 74

    draw.line(
        (
            17,
            separator_y,
            PANEL_SIZE - 17,
            separator_y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (
            46,
            separator_y,
            82,
            separator_y,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )


def _draw_detail_row(
    draw: ImageDraw.ImageDraw,
    weather: CurrentWeather,
    *,
    temperature_unit: TemperatureUnit,
) -> None:
    """Draw high/low temperatures and precipitation probability."""

    high_temperature = convert_temperature(
        weather.high_temperature,
        temperature_unit,
    )
    low_temperature = convert_temperature(
        weather.low_temperature,
        temperature_unit,
    )

    temperature_text, temperature_font = _temperature_range_layout(
        draw,
        high_temperature=high_temperature,
        low_temperature=low_temperature,
        temperature_unit=temperature_unit,
        maximum_width=57,
    )

    _draw_centered_in_region(
        draw,
        left=17,
        right=76,
        y=84,
        text=temperature_text,
        font=temperature_font,
        fill=TEXT_COLOR,
    )

    divider_x = 78

    draw.line(
        (
            divider_x,
            81,
            divider_x,
            99,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    _draw_precipitation_group(
        draw,
        left=81,
        right=112,
        y=84,
        probability=weather.precipitation_probability,
    )


def _temperature_range_layout(
    draw: ImageDraw.ImageDraw,
    *,
    high_temperature: int,
    low_temperature: int,
    temperature_unit: TemperatureUnit,
    maximum_width: int,
) -> tuple[str, BaseImageFont]:
    """Choose the largest readable high/low temperature layout."""

    spacious_text = f"{high_temperature} / {low_temperature} °{temperature_unit.value}"
    compact_text = f"{high_temperature}/{low_temperature}°{temperature_unit.value}"

    layouts = (
        spacious_text,
        compact_text,
    )
    font_sizes = (
        12,
        11,
        10,
        9,
        8,
        7,
    )

    for font_size in font_sizes:
        font = ImageFont.load_default(size=font_size)

        for text in layouts:
            if (
                _text_width(
                    draw,
                    text=text,
                    font=font,
                )
                <= maximum_width
            ):
                return text, font

    return (
        compact_text,
        ImageFont.load_default(size=font_sizes[-1]),
    )


def _draw_precipitation_group(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    right: int,
    y: int,
    probability: int,
) -> None:
    """Draw a centered raindrop and precipitation percentage."""

    text = f"{probability}%"
    droplet_size = 7
    gap = 2
    region_width = right - left

    font = _find_font_that_fits(
        draw,
        text=text,
        maximum_width=region_width - droplet_size - gap,
        font_sizes=(
            13,
            12,
            11,
            10,
            9,
        ),
    )

    text_width = _text_width(
        draw,
        text=text,
        font=font,
    )

    total_width = droplet_size + gap + text_width
    start_x = left + (region_width - total_width) // 2

    draw_raindrop(
        draw,
        origin=(
            start_x,
            y + 3,
        ),
        size=droplet_size,
    )

    draw.text(
        (
            start_x + droplet_size + gap,
            y,
        ),
        text,
        font=font,
        fill=WEATHER_RAIN_COLOR,
    )


def _draw_bottom_accent(
    draw: ImageDraw.ImageDraw,
) -> None:
    """Draw a subtle finishing line below the weather details."""

    y = 104

    draw.line(
        (
            24,
            y,
            104,
            y,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )

    draw.line(
        (
            54,
            y,
            74,
            y,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )


def _animation_icon_frames(
    condition: WeatherCondition,
) -> tuple[int, ...]:
    match condition:
        case WeatherCondition.RAIN:
            return RAIN_ANIMATION_FRAMES

        case WeatherCondition.FOG:
            return FOG_ANIMATION_FRAMES

        case _:
            return (0,)


def _find_font_that_fits(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    maximum_width: int,
    font_sizes: tuple[int, ...],
) -> BaseImageFont:
    """Return the largest font that fits the available width."""

    for font_size in font_sizes:
        font = ImageFont.load_default(size=font_size)

        if (
            _text_width(
                draw,
                text=text,
                font=font,
            )
            <= maximum_width
        ):
            return font

    return ImageFont.load_default(size=font_sizes[-1])


def _text_width(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    font: BaseImageFont,
) -> int:
    """Measure rendered text width."""

    bounding_box = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    return bounding_box[2] - bounding_box[0]


def _draw_centered_in_region(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    right: int,
    y: int,
    text: str,
    font: BaseImageFont,
    fill: str,
) -> None:
    """Draw text horizontally centered inside a region."""

    bounding_box = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    text_width = bounding_box[2] - bounding_box[0]
    region_width = right - left
    x = left + (region_width - text_width) // 2 - bounding_box[0]

    draw.text(
        (
            x,
            y,
        ),
        text,
        font=font,
        fill=fill,
    )
