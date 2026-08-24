from typing import Final

from PIL import ImageDraw

from novachrono.design import (
    FRAME_ACCENT_COLOR,
    FRAME_BRIGHT_COLOR,
    FRAME_DIM_COLOR,
    WEATHER_CLOUD_COLOR,
    WEATHER_CLOUD_SHADOW_COLOR,
    WEATHER_RAIN_COLOR,
    WEATHER_SUN_COLOR,
    WEATHER_SUN_RAY_COLOR,
)
from novachrono.weather import WeatherCondition

FOG_FRAME_OFFSETS: Final = (
    (-4, 0, 4),
    (-3, 1, 3),
    (-2, 2, 2),
    (-1, 3, 1),
    (0, 4, 0),
    (1, 3, -1),
    (2, 2, -2),
    (3, 1, -3),
    (4, 0, -4),
    (2, -1, -3),
)

RAIN_FRAME_Y_OFFSETS: Final = (
    (0, 2, 4),
    (2, 4, 0),
    (4, 0, 2),
)


def draw_weather_icon(
    draw: ImageDraw.ImageDraw,
    *,
    condition: WeatherCondition,
    is_day: bool,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw the static weather icon."""

    draw_weather_icon_frame(
        draw,
        condition=condition,
        is_day=is_day,
        origin=origin,
        size=size,
        frame_index=0,
    )


def draw_weather_icon_frame(
    draw: ImageDraw.ImageDraw,
    *,
    condition: WeatherCondition,
    is_day: bool,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    """Draw one weather-icon animation frame."""

    match condition:
        case WeatherCondition.CLEAR:
            _draw_clear_icon(
                draw,
                is_day=is_day,
                origin=origin,
                size=size,
            )

        case WeatherCondition.PARTLY_CLOUDY:
            _draw_partly_cloudy_icon(
                draw,
                is_day=is_day,
                origin=origin,
                size=size,
            )

        case WeatherCondition.CLOUDY:
            _draw_cloud_icon(
                draw,
                origin=origin,
                size=size,
            )

        case WeatherCondition.FOG:
            _draw_fog_icon(
                draw,
                origin=origin,
                size=size,
                frame_index=frame_index,
            )

        case WeatherCondition.RAIN:
            _draw_rain_icon(
                draw,
                origin=origin,
                size=size,
                frame_index=frame_index,
            )

        case WeatherCondition.SNOW:
            _draw_snow_icon(
                draw,
                origin=origin,
                size=size,
            )

        case WeatherCondition.THUNDERSTORM:
            _draw_thunderstorm_icon(
                draw,
                origin=origin,
                size=size,
            )


def draw_raindrop(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw a compact precipitation drop with a bright highlight."""

    left, top = origin
    center_x = left + size // 2
    bottom = top + size

    draw.polygon(
        (
            (center_x, top),
            (left + size - 2, top + 4),
            (left + 1, top + 4),
        ),
        fill=WEATHER_RAIN_COLOR,
    )

    draw.ellipse(
        (
            left + 1,
            top + 3,
            left + size - 1,
            bottom,
        ),
        fill=WEATHER_RAIN_COLOR,
    )

    if size >= 6:
        draw.point(
            (left + size // 2 - 1, top + size // 2),
            fill=FRAME_BRIGHT_COLOR,
        )


def _draw_clear_icon(
    draw: ImageDraw.ImageDraw,
    *,
    is_day: bool,
    origin: tuple[int, int],
    size: int,
) -> None:
    if is_day:
        _draw_sun(
            draw,
            origin=origin,
            size=size,
        )
        return

    _draw_moon(
        draw,
        origin=origin,
        size=size,
    )


def _draw_partly_cloudy_icon(
    draw: ImageDraw.ImageDraw,
    *,
    is_day: bool,
    origin: tuple[int, int],
    size: int,
) -> None:
    if is_day:
        _draw_sun(
            draw,
            origin=(origin[0] - 1, origin[1] - 1),
            size=size - 4,
        )
    else:
        _draw_moon(
            draw,
            origin=(origin[0] - 1, origin[1] - 1),
            size=size - 4,
        )

    _draw_cloud(
        draw,
        origin=(origin[0] + 5, origin[1] + 10),
        size=size - 6,
    )


def _draw_cloud_icon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    _draw_cloud(
        draw,
        origin=(origin[0] + 2, origin[1] + 7),
        size=size - 4,
    )


def _draw_rain_icon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    _draw_cloud(
        draw,
        origin=(origin[0] + 2, origin[1] + 6),
        size=size - 4,
    )

    drop_offsets = RAIN_FRAME_Y_OFFSETS[frame_index % len(RAIN_FRAME_Y_OFFSETS)]

    base_positions = (
        (origin[0] + 8, origin[1] + 23),
        (origin[0] + 14, origin[1] + 25),
        (origin[0] + 20, origin[1] + 23),
    )

    for (drop_x, drop_y), y_offset in zip(
        base_positions,
        drop_offsets,
        strict=True,
    ):
        draw_raindrop(
            draw,
            origin=(drop_x, drop_y + y_offset),
            size=4,
        )


def _draw_snow_icon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    center_x = origin[0] + size // 2
    center_y = origin[1] + size // 2 + 1
    radius = 9

    draw.line(
        (
            center_x,
            center_y - radius,
            center_x,
            center_y + radius,
        ),
        fill=WEATHER_CLOUD_COLOR,
        width=1,
    )

    draw.line(
        (
            center_x - radius,
            center_y,
            center_x + radius,
            center_y,
        ),
        fill=WEATHER_CLOUD_COLOR,
        width=1,
    )

    draw.line(
        (
            center_x - 7,
            center_y - 7,
            center_x + 7,
            center_y + 7,
        ),
        fill=WEATHER_CLOUD_COLOR,
        width=1,
    )

    draw.line(
        (
            center_x - 7,
            center_y + 7,
            center_x + 7,
            center_y - 7,
        ),
        fill=WEATHER_CLOUD_COLOR,
        width=1,
    )

    _draw_snowflake_tips(
        draw,
        center_x=center_x,
        center_y=center_y,
    )


def _draw_thunderstorm_icon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    _draw_cloud(
        draw,
        origin=(origin[0] + 2, origin[1] + 6),
        size=size - 4,
    )

    bolt_points = (
        (origin[0] + 15, origin[1] + 18),
        (origin[0] + 11, origin[1] + 26),
        (origin[0] + 15, origin[1] + 26),
        (origin[0] + 13, origin[1] + 31),
        (origin[0] + 21, origin[1] + 22),
        (origin[0] + 17, origin[1] + 22),
    )

    draw.polygon(
        bolt_points,
        fill=WEATHER_SUN_COLOR,
    )

    draw.line(
        (
            origin[0] + 15,
            origin[1] + 18,
            origin[0] + 11,
            origin[1] + 26,
            origin[0] + 15,
            origin[1] + 26,
            origin[0] + 13,
            origin[1] + 31,
            origin[0] + 21,
            origin[1] + 22,
            origin[0] + 17,
            origin[1] + 22,
            origin[0] + 15,
            origin[1] + 18,
        ),
        fill=FRAME_ACCENT_COLOR,
        width=1,
    )


def _draw_fog_icon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    offsets = FOG_FRAME_OFFSETS[frame_index % len(FOG_FRAME_OFFSETS)]

    _draw_fog_band(
        draw,
        left=origin[0] + 3 + offsets[0],
        y=origin[1] + 11,
        width=20,
    )

    _draw_fog_band(
        draw,
        left=origin[0] + 8 + offsets[1],
        y=origin[1] + 17,
        width=16,
    )

    _draw_fog_band(
        draw,
        left=origin[0] + 5 + offsets[2],
        y=origin[1] + 23,
        width=18,
    )


def _draw_sun(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    center_x = origin[0] + size // 2 - 1
    center_y = origin[1] + size // 2 - 1
    radius = 7

    draw.ellipse(
        (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ),
        fill=WEATHER_SUN_COLOR,
    )

    for ray in (
        (center_x, center_y - 12, center_x, center_y - 9),
        (center_x, center_y + 9, center_x, center_y + 12),
        (center_x - 12, center_y, center_x - 9, center_y),
        (center_x + 9, center_y, center_x + 12, center_y),
        (center_x - 9, center_y - 9, center_x - 7, center_y - 7),
        (center_x + 7, center_y - 7, center_x + 9, center_y - 9),
        (center_x - 9, center_y + 9, center_x - 7, center_y + 7),
        (center_x + 7, center_y + 7, center_x + 9, center_y + 9),
    ):
        draw.line(
            ray,
            fill=WEATHER_SUN_RAY_COLOR,
            width=1,
        )


def _draw_moon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    center_x = origin[0] + size // 2 - 2
    center_y = origin[1] + size // 2 - 1
    radius = 9

    draw.ellipse(
        (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ),
        fill=FRAME_BRIGHT_COLOR,
    )

    draw.ellipse(
        (
            center_x - 2,
            center_y - radius,
            center_x + radius + 5,
            center_y + radius,
        ),
        fill="#020B14",
    )

    draw.point(
        (center_x + 8, center_y - 7),
        fill=FRAME_BRIGHT_COLOR,
    )
    draw.point(
        (center_x + 11, center_y - 4),
        fill=FRAME_BRIGHT_COLOR,
    )


def _draw_cloud(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    left = origin[0]
    top = origin[1]

    shadow_offset = 1

    draw.ellipse(
        (
            left + 3 + shadow_offset,
            top + 7 + shadow_offset,
            left + 13 + shadow_offset,
            top + 17 + shadow_offset,
        ),
        fill=WEATHER_CLOUD_SHADOW_COLOR,
    )
    draw.ellipse(
        (
            left + 10 + shadow_offset,
            top + 3 + shadow_offset,
            left + 21 + shadow_offset,
            top + 15 + shadow_offset,
        ),
        fill=WEATHER_CLOUD_SHADOW_COLOR,
    )
    draw.ellipse(
        (
            left + 18 + shadow_offset,
            top + 7 + shadow_offset,
            left + 27 + shadow_offset,
            top + 16 + shadow_offset,
        ),
        fill=WEATHER_CLOUD_SHADOW_COLOR,
    )
    draw.rectangle(
        (
            left + 4 + shadow_offset,
            top + 11 + shadow_offset,
            left + 25 + shadow_offset,
            top + 17 + shadow_offset,
        ),
        fill=WEATHER_CLOUD_SHADOW_COLOR,
    )

    draw.ellipse(
        (
            left + 3,
            top + 6,
            left + 13,
            top + 16,
        ),
        fill=WEATHER_CLOUD_COLOR,
    )
    draw.ellipse(
        (
            left + 10,
            top + 2,
            left + 21,
            top + 14,
        ),
        fill=WEATHER_CLOUD_COLOR,
    )
    draw.ellipse(
        (
            left + 18,
            top + 6,
            left + 27,
            top + 15,
        ),
        fill=WEATHER_CLOUD_COLOR,
    )
    draw.rectangle(
        (
            left + 4,
            top + 10,
            left + 25,
            top + 16,
        ),
        fill=WEATHER_CLOUD_COLOR,
    )


def _draw_fog_band(
    draw: ImageDraw.ImageDraw,
    *,
    left: int,
    y: int,
    width: int,
) -> None:
    right = left + width

    draw.line(
        (
            left,
            y,
            right,
            y,
        ),
        fill=WEATHER_CLOUD_COLOR,
        width=2,
    )

    draw.line(
        (
            left + 2,
            y + 2,
            right - 2,
            y + 2,
        ),
        fill=FRAME_DIM_COLOR,
        width=1,
    )


def _draw_snowflake_tips(
    draw: ImageDraw.ImageDraw,
    *,
    center_x: int,
    center_y: int,
) -> None:
    for x_offset, y_offset in (
        (0, -9),
        (0, 9),
        (-9, 0),
        (9, 0),
        (-7, -7),
        (7, 7),
        (-7, 7),
        (7, -7),
    ):
        draw.point(
            (center_x + x_offset, center_y + y_offset),
            fill=FRAME_BRIGHT_COLOR,
        )
