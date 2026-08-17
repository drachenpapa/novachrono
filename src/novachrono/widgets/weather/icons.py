from collections.abc import Callable
from dataclasses import replace

from PIL import Image, ImageDraw

from novachrono.config import ConfigError, load_config
from novachrono.design import (
    FRAME_BRIGHT_COLOR,
    PANEL_COLOR,
    WEATHER_CLOUD_COLOR,
    WEATHER_CLOUD_SHADOW_COLOR,
    WEATHER_SUN_COLOR,
    WEATHER_SUN_RAY_COLOR,
)
from novachrono.outputs.times_gate import (
    TimesGateClient,
    TimesGateConfig,
    TimesGateError,
)
from novachrono.units import TemperatureUnit
from novachrono.weather import CurrentWeather, WeatherCondition
from novachrono.widgets.weather import (
    render_weather_animation,
    render_weather_panel,
)

WEATHER_ICON_ORIGIN = (16, 34)
WEATHER_ICON_SIZE = 32

THUNDERSTORM_FRAME_DURATION_MS = 250
RAIN_FRAME_DURATION_MS = 350
FOG_FRAME_DURATION_MS = 500

THUNDERSTORM_FRAME_COUNT = 12

ThunderstormDrawer = Callable[
    [ImageDraw.ImageDraw, tuple[int, int], int, int],
    None,
]


def main() -> None:
    try:
        app_config = load_config()
    except ConfigError as error:
        raise SystemExit(f"Configuration error: {error}") from error

    host = app_config.times_gate.host
    local_token = app_config.times_gate.local_token

    if host is None:
        raise SystemExit("Missing NOVACHRONO_TIMES_GATE_HOST.")

    if local_token is None:
        raise SystemExit("Missing NOVACHRONO_TIMES_GATE_TOKEN.")

    try:
        client = TimesGateClient(
            TimesGateConfig(
                host=host,
                local_token=local_token,
            )
        )
    except ValueError as error:
        raise SystemExit(f"Invalid Times Gate configuration: {error}") from error

    thunderstorm = _create_weather(WeatherCondition.THUNDERSTORM)
    rain = _create_weather(WeatherCondition.RAIN)
    fog = _create_weather(WeatherCondition.FOG)

    pulse_frames = _render_thunderstorm_animation(
        thunderstorm,
        drawer=_draw_pulsing_bolt,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    cloud_flash_frames = _render_thunderstorm_animation(
        thunderstorm,
        drawer=_draw_cloud_flash,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    static_panel = _render_static_cloud_and_bolt(
        thunderstorm,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    rain_frames = render_weather_animation(
        rain,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    fog_frames = render_weather_animation(
        fog,
        locale=app_config.locale,
        temperature_unit=app_config.temperature_unit,
    )

    try:
        client.send_animation(
            panel_index=0,
            images=pulse_frames,
            frame_duration_ms=THUNDERSTORM_FRAME_DURATION_MS,
        )

        client.send_animation(
            panel_index=1,
            images=cloud_flash_frames,
            frame_duration_ms=THUNDERSTORM_FRAME_DURATION_MS,
        )

        client.send_image(
            panel_index=2,
            image=static_panel,
        )

        client.send_animation(
            panel_index=3,
            images=rain_frames,
            frame_duration_ms=RAIN_FRAME_DURATION_MS,
        )

        client.send_animation(
            panel_index=4,
            images=fog_frames,
            frame_duration_ms=FOG_FRAME_DURATION_MS,
        )
    except TimesGateError as error:
        raise SystemExit(f"Times Gate error: {error}") from error

    print()
    print("Thunderstorm experiment sent.")
    print()
    print("Display 1: CLOUD + PULSING BOLT")
    print("Display 2: CLOUD FLASH + BOLT")
    print("Display 3: STATIC CLOUD + BOLT")
    print("Display 4: RAIN - frozen reference")
    print("Display 5: FOG - frozen rolling reference")
    print()
    print("Run 'uv run novachrono send-dashboard' to restore the normal dashboard.")


def _render_thunderstorm_animation(
    weather: CurrentWeather,
    *,
    drawer: ThunderstormDrawer,
    locale: str,
    temperature_unit: TemperatureUnit,
) -> tuple[Image.Image, ...]:
    base_panel = render_weather_panel(
        weather,
        locale=locale,
        temperature_unit=temperature_unit,
    )

    return tuple(
        _render_thunderstorm_frame(
            base_panel,
            drawer=drawer,
            frame_index=frame_index,
        )
        for frame_index in range(THUNDERSTORM_FRAME_COUNT)
    )


def _render_thunderstorm_frame(
    base_panel: Image.Image,
    *,
    drawer: ThunderstormDrawer,
    frame_index: int,
) -> Image.Image:
    image = base_panel.copy()
    draw = ImageDraw.Draw(image)

    _clear_weather_icon(draw)

    drawer(
        draw,
        WEATHER_ICON_ORIGIN,
        WEATHER_ICON_SIZE,
        frame_index,
    )

    return image


def _render_static_cloud_and_bolt(
    weather: CurrentWeather,
    *,
    locale: str,
    temperature_unit: TemperatureUnit,
) -> Image.Image:
    panel = render_weather_panel(
        weather,
        locale=locale,
        temperature_unit=temperature_unit,
    )

    draw = ImageDraw.Draw(panel)

    _clear_weather_icon(draw)

    _draw_cloud(
        draw,
        origin=WEATHER_ICON_ORIGIN,
        size=WEATHER_ICON_SIZE,
        bright=True,
    )

    _draw_bolt(
        draw,
        origin=WEATHER_ICON_ORIGIN,
        size=WEATHER_ICON_SIZE,
        fill=WEATHER_SUN_COLOR,
        outline=WEATHER_SUN_RAY_COLOR,
        highlight=True,
    )

    return panel


def _draw_pulsing_bolt(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    _draw_cloud(
        draw,
        origin=origin,
        size=size,
        bright=True,
    )

    if frame_index in (8, 11):
        _draw_bolt(
            draw,
            origin=origin,
            size=size,
            fill=WEATHER_SUN_COLOR,
            outline=WEATHER_SUN_RAY_COLOR,
        )
        return

    if frame_index in (9, 10):
        _draw_bolt(
            draw,
            origin=origin,
            size=size,
            fill=WEATHER_SUN_COLOR,
            outline=FRAME_BRIGHT_COLOR,
            highlight=True,
        )
        return

    _draw_bolt(
        draw,
        origin=origin,
        size=size,
        fill=None,
        outline=WEATHER_SUN_RAY_COLOR,
    )


def _draw_cloud_flash(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    size: int,
    frame_index: int,
) -> None:
    strike = frame_index in (8, 9, 10)

    _draw_cloud(
        draw,
        origin=origin,
        size=size,
        bright=strike,
    )

    if frame_index == 9:
        _draw_bolt(
            draw,
            origin=origin,
            size=size,
            fill=WEATHER_SUN_COLOR,
            outline=FRAME_BRIGHT_COLOR,
            highlight=True,
        )
        return

    if strike:
        _draw_bolt(
            draw,
            origin=origin,
            size=size,
            fill=WEATHER_SUN_COLOR,
            outline=WEATHER_SUN_RAY_COLOR,
        )
        return

    _draw_bolt(
        draw,
        origin=origin,
        size=size,
        fill=None,
        outline=WEATHER_SUN_RAY_COLOR,
    )


def _draw_cloud(
    draw: ImageDraw.ImageDraw,
    *,
    origin: tuple[int, int],
    size: int,
    bright: bool,
) -> None:
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

    draw.polygon(
        shadow_points,
        fill=shadow_color,
    )

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

    draw.polygon(
        cloud_points,
        fill=cloud_color,
    )

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
        draw.polygon(
            points,
            fill=fill,
        )

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


def _clear_weather_icon(
    draw: ImageDraw.ImageDraw,
) -> None:
    left, top = WEATHER_ICON_ORIGIN

    draw.rectangle(
        (
            left,
            top,
            left + WEATHER_ICON_SIZE - 1,
            top + WEATHER_ICON_SIZE - 1,
        ),
        fill=PANEL_COLOR,
    )


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


def _create_weather(
    condition: WeatherCondition,
) -> CurrentWeather:
    base_weather = CurrentWeather(
        condition=WeatherCondition.CLEAR,
        temperature=19,
        high_temperature=24,
        low_temperature=8,
        precipitation_probability=35,
        is_day=True,
    )

    return replace(
        base_weather,
        condition=condition,
    )


if __name__ == "__main__":
    main()
