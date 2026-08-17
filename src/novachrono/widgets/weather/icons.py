import math
from typing import Final

from PIL import ImageDraw

from novachrono.design import (
    FRAME_BRIGHT_COLOR,
    PANEL_COLOR,
    WEATHER_CLOUD_COLOR,
    WEATHER_CLOUD_SHADOW_COLOR,
    WEATHER_RAIN_COLOR,
    WEATHER_SUN_COLOR,
    WEATHER_SUN_RAY_COLOR,
)
from novachrono.weather import WeatherCondition

_MOON_COLOR: Final = "#C8E6F0"
_FOG_COLOR: Final = WEATHER_CLOUD_SHADOW_COLOR


def draw_weather_icon(
    draw: ImageDraw.ImageDraw,
    *,
    condition: WeatherCondition,
    is_day: bool,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw a static weather icon for the given condition."""
    _draw_icon(
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
    """Draw one animation frame of a weather icon."""
    _draw_icon(
        draw,
        condition=condition,
        is_day=is_day,
        origin=origin,
        size=size,
        frame_index=frame_index,
    )


def draw_raindrop(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw a small teardrop-shaped raindrop."""
    x, y = origin
    half = max(1, size // 2)

    # Pointed top triangle
    draw.polygon(
        (
            (x + half, y),
            (x, y + half),
            (x + size, y + half),
        ),
        fill=WEATHER_RAIN_COLOR,
    )

    # Round bottom ellipse
    draw.ellipse(
        (x, y + half - 1, x + size, y + size),
        fill=WEATHER_RAIN_COLOR,
    )


def _draw_icon(
    draw: ImageDraw.ImageDraw,
    *,
    condition: WeatherCondition,
    is_day: bool,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    match condition:
        case WeatherCondition.CLEAR:
            if is_day:
                _draw_sun(draw, origin=origin, size=size)
            else:
                _draw_moon(draw, origin=origin, size=size)

        case WeatherCondition.PARTLY_CLOUDY:
            if is_day:
                _draw_small_sun(draw, origin=origin, size=size)
            else:
                _draw_small_moon(draw, origin=origin, size=size)
            _draw_cloud(draw, origin=origin, size=size, bright=True)

        case WeatherCondition.CLOUDY:
            _draw_cloud(draw, origin=origin, size=size, bright=True)

        case WeatherCondition.RAIN:
            _draw_cloud(draw, origin=origin, size=size, bright=False)
            _draw_rain(draw, origin=origin, size=size, frame_index=frame_index)

        case WeatherCondition.FOG:
            _draw_fog(draw, origin=origin, size=size, frame_index=frame_index)

        case WeatherCondition.SNOW:
            _draw_cloud(draw, origin=origin, size=size, bright=False)
            _draw_snow(draw, origin=origin, size=size)

        case WeatherCondition.THUNDERSTORM:
            _draw_cloud(draw, origin=origin, size=size, bright=True)
            _draw_bolt(
                draw,
                origin=origin,
                size=size,
                fill=WEATHER_SUN_COLOR,
                outline=WEATHER_SUN_RAY_COLOR,
            )


def _draw_sun(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    cx = origin[0] + size // 2
    cy = origin[1] + size // 2
    radius = _scale(size, 6)
    ray_inner = _scale(size, 9)
    ray_outer = _scale(size, 13)
    ray_width = max(1, _scale(size, 2))

    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=WEATHER_SUN_COLOR,
    )

    for i in range(8):
        angle = i * math.pi / 4
        x1 = cx + round(ray_inner * math.cos(angle))
        y1 = cy + round(ray_inner * math.sin(angle))
        x2 = cx + round(ray_outer * math.cos(angle))
        y2 = cy + round(ray_outer * math.sin(angle))
        draw.line((x1, y1, x2, y2), fill=WEATHER_SUN_RAY_COLOR, width=ray_width)


def _draw_moon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw a crescent moon using two overlapping circles."""
    cx = origin[0] + size // 2
    cy = origin[1] + size // 2
    radius = _scale(size, 8)
    offset = _scale(size, 4)

    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=_MOON_COLOR,
    )

    # Overlay to cut the crescent shape
    draw.ellipse(
        (
            cx - radius + offset,
            cy - radius - offset,
            cx + radius + offset,
            cy + radius - offset,
        ),
        fill=PANEL_COLOR,
    )


def _draw_small_sun(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw a small sun peeking above the cloud for partly-cloudy day."""
    cx = origin[0] + _scale(size, 24)
    cy = origin[1] + _scale(size, 6)
    radius = _scale(size, 5)
    ray_inner = _scale(size, 7)
    ray_outer = _scale(size, 10)

    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=WEATHER_SUN_COLOR,
    )

    for i in range(8):
        angle = i * math.pi / 4
        x1 = cx + round(ray_inner * math.cos(angle))
        y1 = cy + round(ray_inner * math.sin(angle))
        x2 = cx + round(ray_outer * math.cos(angle))
        y2 = cy + round(ray_outer * math.sin(angle))
        draw.line((x1, y1, x2, y2), fill=WEATHER_SUN_RAY_COLOR, width=1)


def _draw_small_moon(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw a small crescent moon peeking above the cloud for partly-cloudy night."""
    cx = origin[0] + _scale(size, 23)
    cy = origin[1] + _scale(size, 6)
    radius = _scale(size, 4)
    offset = _scale(size, 3)

    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=_MOON_COLOR,
    )

    draw.ellipse(
        (
            cx - radius + offset,
            cy - radius - offset,
            cx + radius + offset,
            cy + radius - offset,
        ),
        fill=PANEL_COLOR,
    )


def _draw_cloud(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    bright: bool,
) -> None:
    """Draw a pixel-art cloud in the upper portion of the icon."""
    shadow_color = WEATHER_CLOUD_SHADOW_COLOR if bright else PANEL_COLOR
    cloud_color = WEATHER_CLOUD_COLOR if bright else WEATHER_CLOUD_SHADOW_COLOR
    highlight_color = FRAME_BRIGHT_COLOR if bright else WEATHER_CLOUD_COLOR

    shadow_points = (
        _point(origin, size, 3, 12),
        _point(origin, size, 6, 12),
        _point(origin, size, 6, 9),
        _point(origin, size, 10, 9),
        _point(origin, size, 10, 6),
        _point(origin, size, 15, 6),
        _point(origin, size, 15, 4),
        _point(origin, size, 20, 4),
        _point(origin, size, 20, 6),
        _point(origin, size, 24, 6),
        _point(origin, size, 24, 9),
        _point(origin, size, 28, 9),
        _point(origin, size, 28, 12),
        _point(origin, size, 30, 12),
        _point(origin, size, 30, 18),
        _point(origin, size, 3, 18),
    )

    draw.polygon(shadow_points, fill=shadow_color)

    cloud_points = (
        _point(origin, size, 2, 11),
        _point(origin, size, 5, 11),
        _point(origin, size, 5, 8),
        _point(origin, size, 9, 8),
        _point(origin, size, 9, 5),
        _point(origin, size, 14, 5),
        _point(origin, size, 14, 3),
        _point(origin, size, 19, 3),
        _point(origin, size, 19, 5),
        _point(origin, size, 23, 5),
        _point(origin, size, 23, 8),
        _point(origin, size, 27, 8),
        _point(origin, size, 27, 11),
        _point(origin, size, 29, 11),
        _point(origin, size, 29, 16),
        _point(origin, size, 2, 16),
    )

    draw.polygon(cloud_points, fill=cloud_color)

    draw.line(
        (
            *_point(origin, size, 14, 4),
            *_point(origin, size, 19, 4),
        ),
        fill=highlight_color,
        width=1,
    )


def _draw_bolt(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    fill: str | None,
    outline: str,
    highlight: bool = False,
) -> None:
    """Draw a lightning bolt in the lower portion of the icon."""
    points = (
        _point(origin, size, 18, 13),
        _point(origin, size, 11, 22),
        _point(origin, size, 16, 22),
        _point(origin, size, 13, 31),
        _point(origin, size, 25, 19),
        _point(origin, size, 19, 19),
        _point(origin, size, 23, 13),
    )

    if fill is not None:
        draw.polygon(points, fill=fill)

    draw.line(
        (*points, points[0]),
        fill=outline,
        width=max(1, _scale(size, 2)),
    )

    if highlight:
        draw.line(
            (
                *_point(origin, size, 18, 16),
                *_point(origin, size, 14, 21),
            ),
            fill=FRAME_BRIGHT_COLOR,
            width=1,
        )


def _draw_rain(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    """Draw animated raindrops in the lower portion of the icon."""
    drop_size = max(2, _scale(size, 3))
    animation_top = origin[1] + _scale(size, 18)
    animation_height = size - _scale(size, 18)
    slot_height = max(1, animation_height // 3)

    columns = (
        origin[0] + _scale(size, 5),
        origin[0] + _scale(size, 13),
        origin[0] + _scale(size, 21),
    )

    # Each column shows one drop that cycles through 3 positions.
    # Columns are staggered by one slot to look like falling rain.
    for col_offset, col_x in enumerate(columns):
        phase = (frame_index + col_offset) % 3
        y = animation_top + phase * slot_height
        draw_raindrop(draw, origin=(col_x, y), size=drop_size)


def _draw_fog(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    """Draw animated fog lines spanning the icon."""
    line_width = max(1, _scale(size, 2))
    fog_ys = (
        origin[1] + _scale(size, 8),
        origin[1] + _scale(size, 16),
        origin[1] + _scale(size, 24),
    )
    scroll = _scale(size, frame_index)

    for i, line_y in enumerate(fog_ys):
        offset = scroll if i % 2 == 0 else -scroll
        x1 = max(origin[0], origin[0] + _scale(size, 4) + offset)
        x2 = min(origin[0] + size, origin[0] + _scale(size, 28) + offset)

        if x1 < x2:
            draw.line((x1, line_y, x2, line_y), fill=_FOG_COLOR, width=line_width)


def _draw_snow(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
) -> None:
    """Draw snowflake dots in the lower portion of the icon."""
    dot_size = max(1, _scale(size, 2))

    positions = (
        (6, 20),
        (14, 23),
        (22, 20),
        (10, 28),
        (20, 27),
    )

    for px, py in positions:
        x = origin[0] + _scale(size, px)
        y = origin[1] + _scale(size, py)
        draw.ellipse((x, y, x + dot_size, y + dot_size), fill=WEATHER_CLOUD_COLOR)


def _point(
    origin: tuple[int, int],
    size: int,
    x: int,
    y: int,
) -> tuple[int, int]:
    return (
        origin[0] + _scale(size, x),
        origin[1] + _scale(size, y),
    )


def _scale(
    size: int,
    value: int,
) -> int:
    return round(size * value / 32)
